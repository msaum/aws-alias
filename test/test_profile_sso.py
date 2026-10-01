"""Profile and SSO compatibility through the real CLI, with local providers only."""
import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import subprocess
import threading
import unittest
import urllib.parse

import test_contracts as contracts


@unittest.skipUnless(contracts.REAL_AWS, "Requires the real AWS CLI.")
class ProfileSSOTests(contracts.IsolatedCase):
    def setUp(self):
        super().setUp()
        self.managed_install()
        self.native = json.loads((contracts.ROOT / "test/fixtures/native-responses.json").read_text())
        self.requests = []
        self.sso_failure = False
        self.config.write_text("""[profile modern]
sso_session = fixture-session
sso_account_id = 111111111111
sso_role_name = ReadOnly
region = eu-west-1
[sso-session fixture-session]
sso_start_url = https://fixture.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
[profile legacy]
sso_start_url = https://legacy-fixture.awsapps.com/start
sso_region = us-east-1
sso_account_id = 222222222222
sso_role_name = ReadOnly
region = us-west-2
[profile invalid]
region = us-east-1
""")
        cache = self.home / ".aws/sso/cache"
        cache.mkdir(parents=True)
        for key in ("fixture-session", "https://legacy-fixture.awsapps.com/start"):
            (cache / (hashlib.sha1(key.encode()).hexdigest() + ".json")).write_text(json.dumps({
                "accessToken": "fixture-sso-token", "expiresAt": "2050-01-01T00:00:00Z",
                "region": "us-east-1", "startUrl": key if key.startswith("https:") else "https://fixture.awsapps.com/start"}))
        self.env.pop("AWS_PROFILE", None)
        self.env.pop("AWS_DEFAULT_REGION", None)
        # Nested workflow calls must use the real CLI to exercise its SSO provider.
        (self.bin / "aws").unlink()
        (self.bin / "aws").symlink_to(contracts.REAL_AWS)

    @contextlib.contextmanager
    def endpoint(self):
        case = self
        class Handler(BaseHTTPRequestHandler):
            def respond(self, status, payload):
                encoded = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/xml" if isinstance(payload, str) else "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            def do_GET(self):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if self.path.startswith("/federation/credentials"):
                    case.requests.append({"service": "sso", "account": query.get("account_id", [None])[0], "role": query.get("role_name", [None])[0]})
                    if case.sso_failure:
                        self.respond(401, {"message": "fixture SSO session expired", "__type": "UnauthorizedException"})
                    else:
                        account = query["account_id"][0]
                        self.respond(200, {"roleCredentials": {"accessKeyId": "ASIA" + account + "TEST", "secretAccessKey": "fixture-secret", "sessionToken": "fixture-session-token", "expiration": 2524608000000}})
                elif self.path.startswith("/restapis"):
                    signing = re.search(r"Credential=([^/]+)/\d+/([^/]+)/([^/]+)/", self.headers.get("Authorization", ""))
                    key, region, service = signing.groups()
                    case.requests.append({"service": service, "operation": "GetRestApis", "key": key, "region": region})
                    self.respond(200, {"items": []})
                else:
                    self.respond(400, {"message": "unexpected fixture request"})
            def do_POST(self):
                payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                try:
                    body = json.loads(payload)
                except ValueError:
                    body = urllib.parse.parse_qs(payload.decode())
                authorization = self.headers.get("Authorization", "")
                signing = re.search(r"Credential=([^/]+)/\d+/([^/]+)/([^/]+)/", authorization)
                if not signing:
                    self.respond(400, {"message": "missing fixture signing scope"})
                    return
                key, region, service = signing.groups()
                operation = body.get("Action", [None])[0] if isinstance(body.get("Action"), list) else self.headers.get("X-Amz-Target", "").split(".")[-1]
                case.requests.append({"service": service, "operation": operation, "key": key, "region": region, "body": body})
                if service == "sts" and operation == "AssumeRole":
                    self.respond(200, "<AssumeRoleResponse><AssumeRoleResult><Credentials><AccessKeyId>ASIA333333333333TEST</AccessKeyId><SecretAccessKey>fixture-chain-secret</SecretAccessKey><SessionToken>fixture-chain-token</SessionToken><Expiration>2050-01-01T00:00:00Z</Expiration></Credentials><AssumedRoleUser><AssumedRoleId>fixture:session</AssumedRoleId><Arn>arn:aws:sts::333333333333:assumed-role/FixtureReadOnly/session</Arn></AssumedRoleUser></AssumeRoleResult></AssumeRoleResponse>")
                    return
                if service == "iam" and operation == "ListMFADevices":
                    self.respond(200, "<ListMFADevicesResponse><ListMFADevicesResult><MFADevices><member><UserName>hardware-user</UserName><SerialNumber>fixture-hardware-serial</SerialNumber><EnableDate>2026-01-01T00:00:00Z</EnableDate></member></MFADevices><IsTruncated>false</IsTruncated></ListMFADevicesResult></ListMFADevicesResponse>")
                    return
                if service == "sts" and operation == "GetCallerIdentity":
                    account = key[4:16]
                    self.respond(200, f"<GetCallerIdentityResponse><GetCallerIdentityResult><UserId>fixture-role:session</UserId><Account>{account}</Account><Arn>arn:aws:sts::{account}:assumed-role/SSOReadOnly/session</Arn></GetCallerIdentityResult></GetCallerIdentityResponse>")
                    return
                match = next((f for f in case.native.values() if f["service"] == service and f["operation"].replace("-", "").lower() == (operation or "").lower()), None)
                if match:
                    self.respond(200, match["response"])
                elif service in {"autoscaling", "cloudformation", "elasticbeanstalk", "elasticache"}:
                    self.respond(200, f"<{operation}Response><{operation}Result/></{operation}Response>")
                elif service in {"codepipeline", "dynamodb", "servicecatalog", "securityhub"}:
                    self.respond(200, {})
                else:
                    self.respond(400, {"message": "unexpected fixture operation"})
            def log_message(self, *_args):
                pass
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        except PermissionError as exc:
            self.skipTest(f"Loopback unavailable: {exc}")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            yield url
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def invoke(self, url, *args, extra_env=None):
        env = dict(self.env, AWS_ENDPOINT_URL_SSO=url, AWS_ENDPOINT_URL_SSO_OIDC=url, AWS_ENDPOINT_URL_STS=url, AWS_MAX_ATTEMPTS="1")
        env.update(extra_env or {})
        return subprocess.run([contracts.REAL_AWS, *args], env=env, text=True, capture_output=True, timeout=30)

    def test_whoami_preserves_sso_profile_before_after_and_environment(self):
        with self.endpoint() as url:
            for profile, account, region in (("modern", "111111111111", "eu-west-1"), ("legacy", "222222222222", "us-west-2")):
                for args, env in ((["--profile", profile, "whoami"], {}), (["whoami", "--profile", profile], {}), (["whoami"], {"AWS_PROFILE": profile})):
                    with self.subTest(profile=profile, args=args):
                        result = self.invoke(url, *args, "--endpoint-url", url, extra_env=env)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(json.loads(result.stdout)["Account"], account)
                        request = self.requests[-1]
                        self.assertEqual(request["key"], "ASIA" + account + "TEST")
                        self.assertEqual(request["region"], region)
            self.assertEqual({r["account"] for r in self.requests if r["service"] == "sso"}, {"111111111111", "222222222222"})

    def test_all_native_query_aliases_with_sso_profiles(self):
        with self.endpoint() as url:
            for name in self.native:
                for profile, account in (("modern", "111111111111"), ("legacy", "222222222222")):
                    with self.subTest(alias=name, profile=profile):
                        result = self.invoke(url, "--profile", profile, name, "--endpoint-url", url)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(self.requests[-1]["key"], "ASIA" + account + "TEST")

    def test_all_native_service_shortcuts_use_the_sso_provider(self):
        commands = {"ag": "get-rest-apis", "as": "describe-auto-scaling-groups", "cfn": "describe-stacks",
                    "cp": "list-pipelines", "ddb": "list-tables", "eb": "describe-applications",
                    "ec": "describe-cache-clusters", "sc": "list-portfolios", "sh": "get-findings"}
        aliases = contracts.m.parse_aliases((contracts.ROOT / "alias").read_bytes())
        self.assertEqual(set(commands), {name for name, value in aliases.items() if len(value.split()) == 1 and not value.startswith("!")})
        with self.endpoint() as url:
            for name, operation in commands.items():
                for profile, account in (("modern", "111111111111"), ("legacy", "222222222222")):
                    with self.subTest(alias=name, profile=profile):
                        result = self.invoke(url, "--profile", profile, name, operation, "--endpoint-url", url)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(self.requests[-1]["key"], "ASIA" + account + "TEST")

    def test_helper_uses_sso_provider_with_prefixed_separator_and_environment_profile(self):
        with self.endpoint() as url:
            for flags, env, account in ((["--aws-profile", "modern", "--aws-endpoint-url", url], {}, "111111111111"),
                                        (["--", "--profile", "legacy", "--endpoint-url", url], {}, "222222222222"),
                                        (["--aws-endpoint-url", url], {"AWS_PROFILE": "modern"}, "111111111111")):
                with self.subTest(flags=flags):
                    result = self.invoke(url, "get-asg-instance-ips", "fixture group", *flags, extra_env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout), ["10.0.0.1", "10.0.0.2"])
                    self.assertEqual(self.requests[-1]["key"], "ASIA" + account + "TEST")

    def test_invalid_profile_and_failed_sso_session_preserve_errors(self):
        self.sso_failure = True
        with self.endpoint() as url:
            for profile, expected in (("missing-profile", "could not be found"), ("modern", "SSO session associated with this profile")):
                for args in (["whoami", "--profile", profile, "--endpoint-url", url],
                             ["get-asg-instance-ips", "group", "--aws-profile", profile, "--aws-endpoint-url", url]):
                    with self.subTest(args=args):
                        result = self.invoke(url, *args)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(expected, result.stderr)
            self.assertTrue(self.requests)
            self.assertTrue(all(request["service"] == "sso" for request in self.requests))

    def test_ambient_profile_precedence_matches_real_cli(self):
        with self.endpoint() as url:
            env = {"AWS_PROFILE": "modern", "AWS_DEFAULT_PROFILE": "legacy"}
            native = self.invoke(url, "whoami", "--endpoint-url", url, extra_env=env)
            self.assertEqual(native.returncode, 0, native.stderr)
            native_key = self.requests[-1]["key"]
            helper = self.invoke(url, "get-asg-instance-ips", "group", "--aws-endpoint-url", url, extra_env=env)
            self.assertEqual(helper.returncode, 0, helper.stderr)
            self.assertEqual(self.requests[-1]["key"], native_key)

    def test_role_profile_can_use_sso_as_its_source(self):
        with self.config.open("a") as config:
            config.write("\n[profile chained]\nrole_arn = arn:aws:iam::333333333333:role/FixtureReadOnly\nsource_profile = modern\nrole_session_name = fixture-chain\nregion = eu-west-1\n")
        with self.endpoint() as url:
            result = self.invoke(url, "whoami", "--profile", "chained", "--endpoint-url", url)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["Account"], "333333333333")
            assume = next(request for request in self.requests if request.get("operation") == "AssumeRole")
            self.assertEqual(assume["key"], "ASIA111111111111TEST")
            self.assertEqual(self.requests[-1]["key"], "ASIA333333333333TEST")

    def test_missing_or_expired_sso_token_stops_before_service_calls(self):
        token = self.home / ".aws/sso/cache" / (hashlib.sha1(b"fixture-session").hexdigest() + ".json")
        original = json.loads(token.read_text())
        with self.endpoint() as url:
            for mode in ("missing", "expired"):
                if mode == "missing":
                    token.rename(token.with_suffix(".saved"))
                else:
                    token.write_text(json.dumps(dict(original, expiresAt="2000-01-01T00:00:00Z")))
                for args in (["whoami", "--profile", "modern", "--endpoint-url", url],
                             ["get-asg-instance-ips", "group", "--aws-profile", "modern", "--aws-endpoint-url", url]):
                    with self.subTest(mode=mode, args=args):
                        result = self.invoke(url, *args)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertRegex(result.stderr, "(?i)(sso|token)")
                self.assertEqual(self.requests, [])

    def test_iam_device_lookup_requires_an_explicit_username_under_sso(self):
        with self.endpoint() as url:
            result = self.invoke(url, "list-virtual-mfa", "--aws-profile", "modern", "--aws-endpoint-url", url)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("username", result.stderr)
            self.assertEqual(self.requests, [])
            result = self.invoke(url, "list-virtual-mfa", "hardware-user", "--aws-profile", "modern", "--aws-endpoint-url", url)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)[0]["UserName"], "hardware-user")
            self.assertEqual(self.requests[-1]["key"], "ASIA111111111111TEST")
            self.assertEqual(self.requests[-1]["body"]["UserName"], ["hardware-user"])


@unittest.skipUnless(contracts.REAL_AWS, "Requires real AWS alias parsing.")
class EveryWorkflowProfileTests(contracts.IsolatedCase):
    def test_every_aws_workflow_forwards_an_sso_profile_in_both_supported_forms(self):
        self.managed_install()
        with self.config.open("a") as config:
            config.write("\n[profile sso-fixture]\nsso_session = fixture\nsso_account_id = 111111111111\nsso_role_name = ReadOnly\nregion = us-east-1\n[sso-session fixture]\nsso_start_url = https://fixture.awsapps.com/start\nsso_region = us-east-1\n")
        cases = contracts.WorkflowTests.cases(self)
        self.assertEqual(set(cases), contracts.m.WORKFLOWS - {"my-ip", "tostring"})
        for name, (arguments, steps) in cases.items():
            for flags in (["--aws-profile", "sso-fixture"], ["--", "--profile", "sso-fixture"]):
                with self.subTest(alias=name, flags=flags):
                    scripted = []
                    for step in steps:
                        item = dict(step)
                        if item.get("program", "aws") == "aws":
                            item["options"] = dict(item.get("options", {}), **{"--profile": "sso-fixture"})
                        scripted.append(item)
                    self.program(scripted, stdin="docker")
                    result = subprocess.run([contracts.REAL_AWS, name, *arguments, *flags], env=self.env, text=True, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    for call in self.calls():
                        if call["program"] == "aws":
                            self.assertEqual(call["argv"][call["argv"].index("--profile") + 1], "sso-fixture")
