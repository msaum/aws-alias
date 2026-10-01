"""Credential-free behavior tests for the distributed aliases and companion."""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import aws_alias_manager as m

FIXTURES = json.loads((ROOT / "test/fixtures/responses.json").read_text())
REAL_AWS = shutil.which("aws")


def step(service, operation, response=None, **extra):
    result = {"prefix": [service, operation], "json": response if response is not None else {}}
    result.update(extra)
    return result


class IsolatedCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aws-alias-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.config = self.root / "config"
        self.config.write_text("[profile fixture]\nregion = us-east-1\noutput = table\n[profile other]\nregion = us-west-2\n")
        self.credentials = self.root / "credentials"
        self.credentials.write_text("")
        self.log = self.root / "calls.jsonl"
        self.script = self.root / "commands.json"
        self.env = {
            "HOME": str(self.home), "PATH": str(self.bin) + os.pathsep + str(Path(sys.executable).parent) + ":/usr/bin:/bin",
            "AWS_CONFIG_FILE": str(self.config), "AWS_SHARED_CREDENTIALS_FILE": str(self.credentials),
            "AWS_EC2_METADATA_DISABLED": "true", "AWS_PROFILE": "fixture", "AWS_DEFAULT_REGION": "us-east-1",
            "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off", "PYTHONDONTWRITEBYTECODE": "1",
            "COMMAND_SCRIPT": str(self.script), "COMMAND_LOG": str(self.log), "LC_ALL": "C",
        }
        for name in ("aws", "docker", "brew", "sudo"):
            self.make_stub(self.bin / name, name)
        self.script.write_text('{"steps":[]}')

    def make_stub(self, path, name):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexec " + shlex.join([sys.executable, str(ROOT / "test/helpers/command_stub.py"), name]) + ' "$@"\n')
        path.chmod(0o700)

    def program(self, steps, *, stdin=None):
        self.log.write_text("")
        self.script.write_text(json.dumps({"steps": steps, "read_stdin_program": stdin}))

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def run_manager(self, *args, env=None):
        return subprocess.run([sys.executable, str(ROOT / "aws_alias_manager.py"), *args],
                              cwd=self.root, env=env or self.env, text=True, capture_output=True, timeout=30)

    @contextlib.contextmanager
    def environment(self):
        with mock.patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr:
            yield stdout, stderr

    def bundle_files(self, comment=""):
        files = {name: (ROOT / name).read_bytes() for name in m.BUNDLE_FILES}
        files["alias"] += comment.encode()
        manifest = {"format": 1, "minimum_cli": "2.37.7", "minimum_python": "3.11",
                    "sha256": {name: m.digest(data) for name, data in files.items()}}
        files["bundle.json"] = json.dumps(manifest).encode()
        return files

    def managed_install(self, ref="a" * 40):
        with self.environment():
            with m.update_lock():
                m.publish_bundle(ref, self.bundle_files())
            link = self.home / ".aws/cli/alias"
            link.symlink_to("aws-alias/current/alias")
        return link


class WorkflowTests(IsolatedCase):
    def cases(self):
        f = FIXTURES
        instance = step("ec2", "describe-instances", f["instances"])
        groups = step("ec2", "describe-security-groups", f["groups"])
        users = step("iam", "list-users", {"Users": [{"UserName": "hardware-user"}, {"UserName": "never-used"}]})
        keys = step("iam", "list-access-keys", {"AccessKeyMetadata": [{"AccessKeyId": "A" * 20}]})
        return {
            "list-user-keys": (["hardware-user"], [keys]),
            "list-virtual-mfa": (["hardware-user"], [step("iam", "list-mfa-devices", f["mfa"])]),
            "find-access-key": (["A" * 20], [users, keys, step("iam", "list-access-keys", {"AccessKeyMetadata": []})]),
            "find-users-without-mfa": ([], [users, step("iam", "list-mfa-devices", f["mfa"]), step("iam", "list-mfa-devices", {"MFADevices": []})]),
            "sg-rules": (["sg-0123"], [groups]),
            "get-group-id": (["test", "vpc-0123"], [groups]),
            "public-ports": ([], [groups]),
            "find-ssh-open": ([], [groups]),
            "allow-my-ip": (["sg-0123", "tcp", "22", "192.0.2.1/32", "--aws-profile", "fixture", "--aws-region", "us-east-1"],
                            [step("sts", "get-caller-identity", f["identity"]), step("ec2", "authorize-security-group-ingress", {"Return": True})]),
            "revoke-my-ip": (["sg-0123", "udp", "50-100", "2001:db8::1/128", "--aws-profile", "fixture", "--aws-region", "us-east-1"],
                             [step("sts", "get-caller-identity", f["identity"]), step("ec2", "revoke-security-group-ingress", {"Return": True})]),
            "ami-snapshots": (["ami-0123"], [step("ec2", "describe-images", {"Images": [{"BlockDeviceMappings": [{"Ebs": {"SnapshotId": "snap-0123"}}, {"VirtualName": "ephemeral0"}]}]})]),
            "list-instances": (["us-east-1", "us-west-2"], [instance, instance]),
            "search-instances": (["quoted, \"name\""], [instance]),
            "find-instances-in-sg": (["sg-0123"], [instance]),
            "get-asg-instance-ips": (["group,with'quotes"], [instance]),
            "find-host-by-instance-id": (["i-0123456789abcdef0"], [instance]),
            "get-dns-from-instance-id": (["i-0123456789abcdef0"], [instance]),
            "get-instance-id-from-dns": (["public.example"], [instance]),
            "find-instance-by-public-ip": (["203.0.113.5"], [instance]),
            "find-nat-gateway-by-public-ip": (["203.0.113.5"], [step("ec2", "describe-nat-gateways", f["nat"])]),
            "list-hosts-csv": ([], [instance]),
            "amazon-linux-amis": (["arm64"], [step("ssm", "get-parameter", {"Parameter": {"Value": "ami-0123"}})]),
            "last-log": (["/fixture/log"], [{"prefix": ["logs", "tail"], "stdout": "fixture event\n"}]),
            "docker-ecr-login": (["000000000000.dkr.ecr.us-east-1.amazonaws.com", "--aws-profile", "fixture", "--aws-region", "us-east-1"],
                                 [{"prefix": ["ecr", "get-login-password"], "stdout": "synthetic-password\n"},
                                  {"program": "docker", "prefix": ["login", "--username", "AWS", "--password-stdin"], "stdout": "Login Succeeded\n"}]),
            "ecr-scan-findings": (["repo", "--image-digest", "sha256:" + "a" * 64], [step("ecr", "describe-image-scan-findings", f["scan"])]),
            "sh-quick-report": ([], [step("securityhub", "get-findings", f["findings"])]),
            "sh-findings-csv": ([], [step("securityhub", "get-findings", f["findings"])]),
            "lambda-list-csv": ([], [step("lambda", "list-functions", f["lambda"])]),
            "events-list-csv": (["--event-bus", "custom"], [step("events", "list-rules", f["events"])]),
        }

    def test_every_aws_workflow_success_and_failure(self):
        self.assertEqual(set(self.cases()), m.WORKFLOWS - {"tostring", "my-ip"})
        for name, (args, steps) in self.cases().items():
            with self.subTest(name=name, mode="success"):
                self.program(steps, stdin="docker")
                result = self.run_manager("run", name, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(self.calls()), len(steps))
                for call in self.calls():
                    if call["program"] == "aws":
                        self.assertIn("--profile", call["argv"])
                        if name != "last-log":
                            self.assertEqual(call["argv"][call["argv"].index("--output") + 1], "text" if name == "docker-ecr-login" else "json")
            with self.subTest(name=name, mode="upstream-failure"):
                failed = copy.deepcopy(steps[0])
                failed.update(code=42, stderr="fixture AccessDenied")
                self.program([failed])
                result = self.run_manager("run", name, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fixture AccessDenied", result.stderr)
                self.assertEqual(len(self.calls()), 2 if name == "list-instances" else 1)

    def test_inherited_credentials_and_original_home_are_isolated(self):
        original_home = self.root / "original home"
        sentinels = original_home / ".aws/cli"
        sentinels.mkdir(parents=True)
        alias = sentinels / "alias"
        alias.write_bytes(b"personal alias sentinel")
        credentials = original_home / ".aws/credentials"
        credentials.write_bytes(b"credential sentinel")
        self.program([step("ec2", "describe-instances", FIXTURES["instances"])])
        inherited = {"HOME": str(original_home), "AWS_ACCESS_KEY_ID": "INHERITEDTESTKEY",
                     "AWS_SECRET_ACCESS_KEY": "inherited-test-secret", "AWS_PROFILE": "wrong"}
        with mock.patch.dict(os.environ, inherited):
            result = self.run_manager("run", "get-asg-instance-ips", "group")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(alias.read_bytes(), b"personal alias sentinel")
        self.assertEqual(credentials.read_bytes(), b"credential sentinel")
        call = self.calls()[0]
        self.assertEqual(call["argv"][call["argv"].index("--profile") + 1], "fixture")
        self.assertNotIn("inherited-test-secret", result.stdout + result.stderr)

    def test_tostring_valid_missing_and_invalid_files(self):
        result = self.run_manager("run", "tostring", str(ROOT / "test/tostring.json"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '"{\\"StreamNames\\":[]}"')
        bad = self.root / "bad.json"
        bad.write_text("not json")
        for path in (bad, self.root / "absent"):
            result = self.run_manager("run", "tostring", str(path))
            self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_ip_lookup_valid_invalid_and_transfer_failure(self):
        for response, expected in ((b"192.0.2.1\n", 0), (b"not-an-ip", 1), (b"2001:db8::1", 1)):
            with self.subTest(response=response), self.environment() as (out, err):
                with mock.patch.object(m.urllib.request, "urlopen") as opener:
                    opener.return_value.__enter__.return_value.read.return_value = response
                    self.assertEqual(m.main(["run", "my-ip"]), expected)
        with self.environment(), mock.patch.object(m.urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertEqual(m.main(["run", "my-ip"]), 1)

    def test_retired_entries_do_not_invoke_aws(self):
        for name in m.RETIRED:
            with self.subTest(name=name):
                result = self.run_manager("run", name)
                self.assertEqual(result.returncode, 2)
                self.assertIn("retired", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_profiles_regions_and_endpoints_are_forwarded(self):
        self.program([step("ec2", "describe-instances", FIXTURES["instances"], options={"--profile": "other", "--region": "eu-west-1", "--endpoint-url": "http://127.0.0.1:9999"})])
        result = self.run_manager("run", "get-asg-instance-ips", "group", "--profile", "other", "--region", "eu-west-1", "--endpoint-url", "http://127.0.0.1:9999")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_ambient_output_does_not_change_json_transforms(self):
        for output in ("json", "yaml", "text", "table"):
            with self.subTest(output=output):
                self.config.write_text(f"[profile fixture]\nregion = us-east-1\noutput = {output}\n")
                self.program([step("ec2", "describe-instances", FIXTURES["instances"])])
                result = self.run_manager("run", "get-asg-instance-ips", "group")
                self.assertEqual(json.loads(result.stdout), ["10.0.0.1", "10.0.0.2"])

    def test_missing_profile_stops_before_aws(self):
        env = {k: v for k, v in self.env.items() if k not in {"AWS_PROFILE", "AWS_DEFAULT_PROFILE"}}
        explicit = {"allow-my-ip", "revoke-my-ip", "docker-ecr-login"}
        for name, (args, _steps) in self.cases().items():
            with self.subTest(name=name):
                # Remove the explicitly scoped fixture arguments as a caller
                # using consumed outer globals would appear to the helper.
                args = list(args)
                for flag in ("--aws-profile", "--aws-region"):
                    if flag in args:
                        index = args.index(flag)
                        del args[index:index + 2]
                self.program([])
                result = self.run_manager("run", name, *args, env=env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(f"aws {name}", result.stderr)
                self.assertIn("--aws-profile PROFILE", result.stderr)
                self.assertIn("-- --profile PROFILE", result.stderr)
                self.assertIn("AWS CLI consumes ordinary --profile", result.stderr)
                if name in explicit:
                    self.assertIn("--aws-region REGION", result.stderr)
                    self.assertIn("--region REGION", result.stderr)
                if name == "ecr-scan-findings":
                    self.assertIn("--image-tag <image-tag>", result.stderr)
                self.assertEqual(self.calls(), [])

    def test_partial_explicit_context_shows_both_forms_before_aws(self):
        for name in ("allow-my-ip", "revoke-my-ip", "docker-ecr-login"):
            args = (["000000000000.dkr.ecr.us-east-1.amazonaws.com"] if name == "docker-ecr-login"
                    else ["sg-0123", "tcp", "22"])
            for flags in (["--aws-profile", "fixture"], ["--aws-region", "us-east-1"]):
                with self.subTest(name=name, flags=flags):
                    self.program([])
                    result = self.run_manager("run", name, *args, *flags)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("--aws-profile PROFILE --aws-region REGION", result.stderr)
                    self.assertIn("-- --profile PROFILE --region REGION", result.stderr)
                    self.assertEqual(self.calls(), [])

    def test_no_mutation_with_invalid_security_group_arguments(self):
        invalid = [[], ["sg-0123"], ["sg-0123", "tcp", "70000"], ["sg-0123", "tcp", "22", "0.0.0.0/0"],
                   ["sg-0123", "tcp", "22", "not-a-cidr"], ["group-name", "tcp", "22", "192.0.2.1/32"]]
        for name in ("allow-my-ip", "revoke-my-ip"):
            for args in invalid:
                with self.subTest(name=name, args=args):
                    result = self.run_manager("run", name, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.calls(), [])

    def test_sg_missing_explicit_context_and_ip_failure_stop_mutation(self):
        with self.environment(), mock.patch.object(m, "current_ip", side_effect=m.Error("lookup failed")):
            self.assertEqual(m.main(["run", "allow-my-ip", "sg-0123", "tcp", "22", "--aws-profile", "fixture", "--aws-region", "us-east-1"]), 1)
        result = self.run_manager("run", "allow-my-ip", "sg-0123", "tcp", "22", "192.0.2.1/32")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_permission_idempotence_and_denied_mutation(self):
        for name, operation, code in (("allow-my-ip", "authorize-security-group-ingress", "InvalidPermission.Duplicate"),
                                      ("revoke-my-ip", "revoke-security-group-ingress", "InvalidPermission.NotFound")):
            self.program([step("sts", "get-caller-identity", FIXTURES["identity"]), step("ec2", operation, code=254, stderr=f"An error occurred ({code})")])
            result = self.run_manager("run", name, "sg-0123", "tcp", "22", "192.0.2.1/32", "--aws-profile", "fixture", "--aws-region", "us-east-1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)["Changed"])

    def test_group_lookup_requires_exactly_one_match(self):
        for groups in ([], [FIXTURES["groups"]["SecurityGroups"][0]] * 2):
            self.program([step("ec2", "describe-security-groups", {"SecurityGroups": groups})])
            result = self.run_manager("run", "get-group-id", "a,name'", "vpc-0123")
            self.assertEqual(result.returncode, 1)
            call = self.calls()[0]["argv"]
            self.assertEqual(json.loads(call[call.index("--filters") + 1])[0]["Values"], ["a,name'"])

    def test_public_and_ssh_rule_scope(self):
        for name in ("public-ports", "find-ssh-open"):
            self.program([step("ec2", "describe-security-groups", FIXTURES["groups"])])
            result = self.run_manager("run", name)
            rows = json.loads(result.stdout)
            self.assertTrue(any(row["PeerType"] == "ipv6" for row in rows))
            self.assertTrue(any(row["Protocol"] == "-1" for row in rows))
            self.assertTrue(any(row["FromPort"] == 0 and row["ToPort"] == 100 for row in rows))
            self.assertTrue(all(row["Direction"] == "ingress" for row in rows))
            if name == "find-ssh-open":
                self.assertTrue(all(row["Protocol"] != "udp" for row in rows))

    def test_csv_round_trips_and_fields(self):
        cases = {
            "list-hosts-csv": ("ec2", "describe-instances", "instances", 5),
            "sh-findings-csv": ("securityhub", "get-findings", "findings", 14),
            "lambda-list-csv": ("lambda", "list-functions", "lambda", 12),
            "events-list-csv": ("events", "list-rules", "events", 6),
        }
        for name, (service, operation, fixture, columns) in cases.items():
            with self.subTest(name=name):
                self.program([step(service, operation, FIXTURES[fixture])])
                result = self.run_manager("run", name)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = list(csv.reader(io.StringIO(result.stdout)))
                self.assertTrue(all(len(row) == columns for row in rows))
                if name == "list-hosts-csv":
                    self.assertEqual(rows[1][0], "i-0123456789abcdef0")
                    self.assertEqual(rows[1][-1], 'quoted, "name"\nsecond line')
                    self.assertEqual(rows[2][-1], "")
                if name == "sh-findings-csv":
                    self.assertEqual(len(rows), 4)
                    self.assertEqual(rows[1][-2], "Fix, then verify")
                if name == "lambda-list-csv":
                    self.assertEqual(rows[1][3], "")
                    self.assertEqual(rows[1][10:], ["Active", "Image"])
                if name == "events-list-csv":
                    self.assertEqual(rows[1][1], "default")

    def test_securityhub_counts_ignore_metadata(self):
        self.program([step("securityhub", "get-findings", FIXTURES["findings"])])
        result = self.run_manager("run", "sh-quick-report")
        rows = json.loads(result.stdout)
        self.assertEqual(sum(row["Count"] for row in rows), 2)
        self.assertEqual(rows[-1]["Severity"], "INFORMATIONAL")
        self.assertEqual(rows[-1]["Count"], 1)
        self.assertEqual(len(self.calls()), 1)

    def test_empty_responses_and_missing_tags(self):
        for name, (args, steps) in self.cases().items():
            if name in {"allow-my-ip", "revoke-my-ip", "docker-ecr-login", "amazon-linux-amis", "last-log"}:
                continue
            empty = {key: [] for key in steps[0].get("json", {})}
            if name == "ecr-scan-findings":
                empty = {"imageScanStatus": {"status": "COMPLETE"}, "imageScanFindings": {"findings": []}}
            if name == "list-instances":
                empty = {"Reservations": []}
            empty_steps = [dict(s, json=empty) for s in steps] if name == "list-instances" else [dict(steps[0], json=empty)]
            self.program(empty_steps)
            result = self.run_manager("run", name, *args)
            self.assertEqual(result.returncode, 1 if name == "get-group-id" else 0, f"{name}: {result.stderr}")

    def test_partial_region_failure_is_visible(self):
        self.program([step("ec2", "describe-instances", FIXTURES["instances"], options={"--region": "us-east-1"}),
                      step("ec2", "describe-instances", code=42, stderr="region denied", options={"--region": "us-west-2"})])
        result = self.run_manager("run", "list-instances", "us-east-1", "us-west-2")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(json.loads(result.stdout)), 2)
        self.assertIn("us-west-2", result.stderr)

    def test_ecr_password_only_on_stdin_and_region_validation(self):
        args, steps = self.cases()["docker-ecr-login"]
        self.program(steps, stdin="docker")
        result = self.run_manager("run", "docker-ecr-login", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        docker = self.calls()[-1]
        self.assertEqual(docker["stdin"], "synthetic-password\n")
        self.assertNotIn("synthetic-password", " ".join(docker["argv"]) + result.stdout + result.stderr)
        self.program([])
        result = self.run_manager("run", "docker-ecr-login", "000000000000.dkr.ecr.us-west-2.amazonaws.com", "--aws-profile", "fixture", "--aws-region", "us-east-1")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_scan_status_and_basic_enhanced_findings(self):
        for status, expected in (("COMPLETE", 0), ("ACTIVE", 0), ("IN_PROGRESS", 1), ("FAILED", 1)):
            response = {"imageScanStatus": {"status": status}, "imageScanFindings": {"findings": [{"severity": "LOW", "name": "basic"}], "enhancedFindings": [{"severity": "HIGH", "name": "enhanced"}]}}
            self.program([step("ecr", "describe-image-scan-findings", response)])
            result = self.run_manager("run", "ecr-scan-findings", "repo", "--image-tag", "stable")
            self.assertEqual(result.returncode, expected)
            self.assertEqual(len(json.loads(result.stdout)["findings"]), 2)


class BundleTests(IsolatedCase):
    def args(self, **kwargs):
        return argparse.Namespace(check=False, rollback=False, replace_local=False, ref=None, **kwargs)

    def test_manifest_rejects_invalid_inputs_before_publication(self):
        valid = self.bundle_files()
        m.validate_bundle(valid)
        for name, contents in (("alias", b"PARTIAL DOWNLOAD"), ("aws_alias_manager.py", b"broken python !")):
            files = dict(valid, **{name: contents})
            with self.assertRaises(m.Error):
                m.validate_bundle(files)
        for source in (b"[toplevel]\nx = sts\nx = ec2\n", b"[toplevel]\nx = !f() {\n", b"[toplevel]\na = b\nb = a\n"):
            with self.assertRaises(m.Error):
                m.parse_aliases(source)

    def test_rehashed_invalid_targets_and_companion_are_rejected(self):
        candidates = [
            ("alias", (ROOT / "alias").read_bytes().replace(b"whoami = sts get-caller-identity", b"whoami = invalid-service invented")),
            ("alias", (ROOT / "alias").read_bytes().replace(b"run tostring", b"run nonexistent-helper")),
            ("aws_alias_manager.py", b"WORKFLOWS=set()\nRETIRED={}\nNATIVE_TARGETS={}\n"),
        ]
        for name, contents in candidates:
            with self.subTest(file=name):
                files = self.bundle_files()
                files[name] = contents
                manifest = json.loads(files["bundle.json"])
                manifest["sha256"][name] = m.digest(contents)
                files["bundle.json"] = json.dumps(manifest).encode()
                with self.assertRaises(m.Error):
                    m.validate_bundle(files)

    def test_clean_checkout_requires_committed_bundle(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        env = dict(self.env, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
        subprocess.run(["git", "init", "-q", str(checkout)], check=True, env=env)
        for name, data in self.bundle_files().items():
            (checkout / name).write_bytes(data)
        with self.environment(), self.assertRaises(m.Error):
            m.clean_checkout(checkout)
        subprocess.run(["git", "-C", str(checkout), "add", "."], check=True, env=env)
        subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True, env=env)
        with self.environment():
            self.assertEqual(len(m.clean_checkout(checkout)), 40)
            (checkout / "alias").write_text("personal edit")
            with self.assertRaises(m.Error):
                m.clean_checkout(checkout)

    def test_updates_check_rollback_and_noop(self):
        link = self.managed_install()
        candidate = self.bundle_files("\n# candidate revision\n")
        with self.environment():
            before, _ = m.current_bundle()
            with mock.patch.object(m, "fetch_bundle", return_value=("b" * 40, candidate)):
                args = self.args(); args.check = True
                m.update_aliases(args)
                self.assertEqual(m.current_bundle()[0], before)
                m.update_aliases(self.args())
                current, metadata = m.current_bundle()
                self.assertEqual(metadata["commit"], "b" * 40)
                self.assertEqual(link.read_bytes(), candidate["alias"])
                m.update_aliases(self.args())
                self.assertEqual(m.current_bundle()[0], current)
            args = self.args(); args.rollback = True
            m.update_aliases(args)
            self.assertEqual(m.current_bundle()[0], before)

    def test_local_edits_preserved_until_pinned_replacement(self):
        link = self.managed_install()
        link.write_bytes(link.read_bytes() + b"\n# personal alias\n")
        personal = link.read_bytes()
        candidate = self.bundle_files("\n# upstream\n")
        with self.environment(), mock.patch.object(m, "fetch_bundle", return_value=("b" * 40, candidate)):
            with self.assertRaises(m.Error) as error:
                m.update_aliases(self.args())
            self.assertEqual(error.exception.code, 3)
            self.assertEqual(link.read_bytes(), personal)
            args = self.args(); args.replace_local = True
            with self.assertRaises(m.Error):
                m.update_aliases(args)
            args.ref = "b" * 40
            m.update_aliases(args)
            backups = list((m.store_path() / "backups").glob("*/alias"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), personal)

    def test_helper_edits_are_protected(self):
        self.managed_install()
        with self.environment():
            current, _ = m.current_bundle()
            helper = current / "aws_alias_manager.py"
            helper.write_bytes(helper.read_bytes() + b"\n# local edit\n")
            with mock.patch.object(m, "fetch_bundle", return_value=("b" * 40, self.bundle_files())), self.assertRaises(m.Error) as error:
                m.update_aliases(self.args())
            self.assertEqual(error.exception.code, 3)

    def test_transfer_validation_backup_and_activation_failures_preserve_current(self):
        link = self.managed_install()
        original = link.read_bytes()
        with self.environment():
            current, _ = m.current_bundle()
            for failure in (m.Error("partial transfer"), m.Error("HTTP 404"), m.Error("invalid INI")):
                with mock.patch.object(m, "fetch_bundle", side_effect=failure), self.assertRaises(m.Error):
                    m.update_aliases(self.args())
                self.assertEqual(link.read_bytes(), original)
                self.assertEqual(m.current_bundle()[0], current)
            with mock.patch.object(m, "fetch_bundle", return_value=("b" * 40, self.bundle_files("\n# new\n"))):
                with mock.patch.object(m, "backup", side_effect=OSError("backup failed")), self.assertRaises(OSError):
                    m.update_aliases(self.args())
                with mock.patch.object(m, "switch_bundle", side_effect=OSError("activation failed")), self.assertRaises(OSError):
                    m.update_aliases(self.args())
            self.assertEqual(link.read_bytes(), original)
            self.assertEqual(m.current_bundle()[0], current)

    def test_change_between_check_and_activation_is_detected(self):
        link = self.managed_install()
        with self.environment():
            old, _ = m.current_bundle()
            observed = m.local_hashes(old)
            link.write_bytes(link.read_bytes() + b"\n# raced edit\n")
            with self.assertRaises(m.Error) as error:
                m.publish_bundle("b" * 40, self.bundle_files(), previous=old.name, expected=observed)
            self.assertEqual(error.exception.code, 3)
            self.assertEqual(m.current_bundle()[0], old)

    def test_lock_contention_and_unexpected_symlinks(self):
        self.managed_install()
        with self.environment():
            with m.update_lock(), self.assertRaises(m.Error) as error:
                with m.update_lock():
                    pass
            self.assertEqual(error.exception.code, 4)
            pointer = m.store_path() / "current"
            pointer.unlink()
            pointer.symlink_to(self.root)
            with self.assertRaises(m.Error):
                m.current_bundle()

    def test_bootstrap_preserves_personal_file_and_supports_recovery(self):
        alias = self.home / ".aws/cli/alias"
        alias.parent.mkdir(parents=True)
        alias.write_text("[toplevel]\npersonal = sts get-caller-identity\n")
        original = alias.read_bytes()
        self.program([{"prefix": ["--version"], "stdout": "aws-cli/2.37.7 fixture\n"}] * 2)
        with self.environment(), mock.patch.object(m, "clean_checkout", return_value="a" * 40):
            with self.assertRaises(m.Error) as error:
                m.install(argparse.Namespace(replace_local=False))
            self.assertEqual(error.exception.code, 3)
            self.assertEqual(alias.read_bytes(), original)
            m.install(argparse.Namespace(replace_local=True))
            self.assertTrue(alias.is_symlink())
            backups = list((m.store_path() / "backups").glob("*/personal-alias"))
            self.assertEqual(backups[0].read_bytes(), original)

    def test_downloads_pin_default_branch_and_validate_content(self):
        files = self.bundle_files()
        urls = []
        def fetch(url):
            urls.append(url)
            if url.endswith("/repos/msaum/aws-alias"):
                return b'{"default_branch":"main"}'
            if "/commits/" in url:
                return json.dumps({"sha": "b" * 40}).encode()
            return files[url.rsplit("/", 1)[-1]]
        with mock.patch.object(m, "download", side_effect=fetch):
            sha, result = m.fetch_bundle()
        self.assertEqual(sha, "b" * 40)
        self.assertIn("/commits/main", urls[1])
        self.assertTrue(all("/" + sha + "/" in url for url in urls[2:]))
        with mock.patch.object(m, "download", side_effect=AssertionError("network must not run")), self.assertRaises(m.Error):
            m.fetch_bundle("master")

    def test_download_rejects_partial_empty_and_off_host_redirect(self):
        response = mock.MagicMock()
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        response.headers = {"Content-Length": "100"}
        response.read.return_value = b"partial"
        with mock.patch.object(m.urllib.request, "build_opener", return_value=opener), self.assertRaises(m.Error):
            m.download("https://raw.githubusercontent.com/fixture")
        response.headers = {}; response.read.return_value = b""
        with mock.patch.object(m.urllib.request, "build_opener", return_value=opener), self.assertRaises(m.Error):
            m.download("https://raw.githubusercontent.com/fixture")
        with self.assertRaises(m.Error):
            m.GitHubRedirects().redirect_request(None, None, 302, "redirect", {}, "http://outside.invalid/path")


class UpgradeTests(IsolatedCase):
    def official_binary(self):
        binary = self.root / "official/v2/2.37.7/dist/aws"
        self.make_stub(binary, "aws")
        (self.bin / "aws").unlink()
        (self.bin / "aws").symlink_to(binary)
        return self.bin / "aws"

    def version_step(self, version="2.37.7"):
        return {"prefix": ["--version"], "stdout": f"aws-cli/{version} fixture\n"}

    def test_official_native_update_and_already_current(self):
        self.official_binary()
        self.program([self.version_step(), {"program": "brew", "prefix": ["--prefix", "awscli"], "code": 1},
                      {"prefix": ["update", "help"], "stdout": "update help"}, {"prefix": ["update"]}, self.version_step()]
                     if m.platform.system() == "Darwin" else [self.version_step(), {"prefix": ["update", "help"]}, {"prefix": ["update"]}, self.version_step()])
        result = self.run_manager("upgrade")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified CLI", result.stdout)

    def test_current_official_layout_uses_install_metadata(self):
        binary = self.root / "official-current/aws"
        self.make_stub(binary, "aws")
        (self.bin / "aws").unlink()
        (self.bin / "aws").symlink_to(binary)
        data = binary.parent / "awscli/data"
        data.mkdir(parents=True)
        (data / "metadata.json").write_text('{"distribution_source":"exe"}')
        (data / "install.json").write_text(json.dumps({"install_dir": str(binary.parent), "bin_dir": str(self.bin)}))
        with self.environment(), mock.patch.object(m.platform, "system", return_value="Linux"):
            info = m.detect_installation(self.bin / "aws")
            self.assertEqual(info["method"], "official")
            self.program([self.version_step(), {"prefix": ["update", "help"]}, {"prefix": ["update"]}, self.version_step("2.37.8")])
            m.upgrade(argparse.Namespace(all=False, dry_run=False))
            (data / "metadata.json").write_text('{"distribution_source":"container"}')
            with self.assertRaises(m.Error):
                m.detect_installation(self.bin / "aws")
            (data / "metadata.json").write_text('{"distribution_source":"exe"}')
            (data / "install.json").write_text(json.dumps({"install_dir": str(self.root), "bin_dir": str(self.bin)}))
            with self.assertRaises(m.Error):
                m.detect_installation(self.bin / "aws")

    def test_homebrew_detection_update_and_pin(self):
        binary = self.root / "Cellar/awscli/2.37.7/bin/aws"
        self.make_stub(binary, "aws")
        (self.bin / "aws").unlink(); (self.bin / "aws").symlink_to(binary)
        initial = [self.version_step(), {"program": "brew", "prefix": ["--prefix", "awscli"], "stdout": str(binary.parent.parent) + "\n"},
                   {"program": "brew", "prefix": ["list", "--pinned"]}]
        with self.environment(), mock.patch.object(m.platform, "system", return_value="Darwin"):
            self.program(initial + [{"program": "brew", "prefix": ["update"]}, {"program": "brew", "prefix": ["upgrade", "awscli"]}, self.version_step("2.37.8")])
            m.upgrade(argparse.Namespace(all=False, dry_run=False))
            self.assertTrue(any(call["argv"] == ["upgrade", "awscli"] for call in self.calls()))
            self.program([initial[1], dict(initial[2], stdout="awscli\n")])
            with self.assertRaises(m.Error):
                m.detect_installation(self.bin / "aws")

    def test_dry_run_old_cli_failed_upgrade_and_partial_all(self):
        self.official_binary()
        info = {"method": "official", "binary": str(self.bin / "aws"), "privileged": False, "command": [str(self.bin / "aws"), "update"]}
        with self.environment(), mock.patch.object(m, "detect_installation", return_value=info):
            self.program([self.version_step(), {"prefix": ["update", "help"]}])
            m.upgrade(argparse.Namespace(all=True, dry_run=True))
            self.assertFalse(any(call["argv"] == ["update"] for call in self.calls()))
            self.program([self.version_step("2.0.0")])
            with self.assertRaises(m.Error):
                m.upgrade(argparse.Namespace(all=False, dry_run=False))
            self.program([self.version_step(), {"prefix": ["update", "help"]}, {"prefix": ["update"], "code": 42}])
            with mock.patch.object(m, "update_aliases") as aliases, self.assertRaises(m.Error):
                m.upgrade(argparse.Namespace(all=True, dry_run=False))
            aliases.assert_not_called()
            self.program([self.version_step(), {"prefix": ["update", "help"]}, {"prefix": ["update"]}, self.version_step("2.37.8")])
            with mock.patch.object(m, "update_aliases", side_effect=m.Error("local conflict", 3)), self.assertRaises(m.Error) as error:
                m.upgrade(argparse.Namespace(all=True, dry_run=False))
            self.assertIn("CLI update succeeded", str(error.exception))
            self.assertEqual(error.exception.code, 3)

    def test_unsupported_installation_platform_and_missing_tool(self):
        with self.environment(), mock.patch.object(m.platform, "system", return_value="Windows"), self.assertRaises(m.Error):
            m.detect_installation(self.bin / "aws")
        with self.environment(), mock.patch.object(m.platform, "system", return_value="Linux"), self.assertRaises(m.Error):
            m.detect_installation(self.bin / "aws")
        with mock.patch.object(m.shutil, "which", return_value=None), self.assertRaises(m.Error):
            m.required_tool("aws")


@unittest.skipUnless(REAL_AWS, "A real AWS CLI is required for alias-parser checks.")
class ActualAliasTests(IsolatedCase):
    def setUp(self):
        super().setUp()
        self.managed_install()

    def test_helper_flags_separator_spaces_and_native_global_consumption(self):
        self.program([step("ec2", "describe-instances", FIXTURES["instances"], options={"--profile": "other", "--region": "eu-west-1"})])
        result = subprocess.run([REAL_AWS, "get-asg-instance-ips", "group with spaces", "--", "--profile", "other", "--region", "eu-west-1"], env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["10.0.0.1", "10.0.0.2"])
        self.program([step("ec2", "describe-instances", FIXTURES["instances"], options={"--profile": "other", "--region": "eu-west-1"})])
        result = subprocess.run([REAL_AWS, "get-asg-instance-ips", "group", "--aws-profile", "other", "--aws-region", "eu-west-1"], env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.program([])
        env = {k: v for k, v in self.env.items() if k != "AWS_PROFILE"}
        for flags in (["--profile", "other", "get-asg-instance-ips", "group"], ["get-asg-instance-ips", "group", "--profile", "other"]):
            result = subprocess.run([REAL_AWS, *flags], env=env, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("aws get-asg-instance-ips <asg-name> --aws-profile PROFILE", result.stderr)
            self.assertIn("aws get-asg-instance-ips <asg-name> -- --profile PROFILE", result.stderr)
            self.assertEqual(self.calls(), [])

    def test_all_migration_aliases_and_tostring_through_real_cli(self):
        for name in m.RETIRED:
            result = subprocess.run([REAL_AWS, name], env=self.env, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("retired", result.stderr)
        result = subprocess.run([REAL_AWS, "tostring", str(ROOT / "test/tostring.json")], env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [])



@unittest.skipUnless(REAL_AWS, "A real AWS CLI is required for native model checks.")
class NativeModelTests(IsolatedCase):
    def test_every_native_operation_and_service_shortcut(self):
        self.managed_install()
        aliases = m.parse_aliases((ROOT / "alias").read_bytes())
        for name, value in aliases.items():
            if value.startswith("!") or name in {"profiles", "mfa"}:
                continue
            with self.subTest(alias=name):
                command = shlex.split(value)
                options = ["help"] if len(command) == 1 else ["--generate-cli-skeleton", "input"]
                env = dict(self.env, AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing")
                result = subprocess.run([REAL_AWS, name, *options], env=env, text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([REAL_AWS, "profiles"], env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), {"fixture", "other"})
        result = subprocess.run([REAL_AWS, "mfa", "help"], env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(REAL_AWS, "A real AWS CLI is required for loopback pagination checks.")
class LocalEndpointTests(IsolatedCase):
    @contextlib.contextmanager
    def endpoint(self, pages):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                try:
                    request_body = json.loads(body)
                except ValueError:
                    import urllib.parse
                    request_body = urllib.parse.parse_qs(body.decode())
                calls.append({"body": request_body, "authorization": self.headers.get("Authorization", "")})
                status, payload = pages[min(len(calls) - 1, len(pages) - 1)]
                data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/xml" if isinstance(payload, str) else "application/x-amz-json-1.1")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *_args):
                pass
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        except PermissionError as exc:
            self.skipTest(f"Loopback binding is unavailable: {exc}")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", calls
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def invoke(self, *args):
        self.credentials.write_text("[fixture]\naws_access_key_id = testing\naws_secret_access_key = testing\n[other]\naws_access_key_id = testing\naws_secret_access_key = testing\n")
        env = dict(self.env, AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing", AWS_MAX_ATTEMPTS="1")
        return subprocess.run([REAL_AWS, *args], env=env, text=True, capture_output=True, timeout=30)

    def test_native_alias_paginates_empty_and_later_page_failure(self):
        self.managed_install()
        pages = [(200, {"repositories": [{"repositoryArn": "arn:one"}], "nextToken": "second"}),
                 (200, {"repositories": [{"repositoryArn": "arn:two"}]})]
        with self.endpoint(pages) as (url, calls):
            result = self.invoke("--profile", "other", "ecr-list-repositories", "--region", "eu-west-1", "--endpoint-url", url, "--output", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), ["arn:one", "arn:two"])
            self.assertEqual(calls[1]["body"]["nextToken"], "second")
            self.assertIn("eu-west-1/ecr", calls[0]["authorization"])
        with self.endpoint([(200, {"repositories": []})]) as (url, calls):
            result = self.invoke("ecr-list-repositories", "--endpoint-url", url, "--output", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
        with self.endpoint([pages[0], (400, {"__type": "AccessDeniedException", "message": "fixture denied page two"})]) as (url, calls):
            result = self.invoke("ecr-list-repositories", "--endpoint-url", url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fixture denied page two", result.stderr)
            self.assertEqual(len(calls), 2)

    def test_every_native_query_response_empty_and_failure(self):
        self.managed_install()
        fixtures = json.loads((ROOT / "test/fixtures/native-responses.json").read_text())
        native_operations = {name for name, value in m.parse_aliases((ROOT / "alias").read_bytes()).items()
                             if not value.startswith("!") and len(shlex.split(value)) > 1 and name not in {"mfa", "profiles"}}
        self.assertEqual(set(fixtures), native_operations)
        for name, fixture in fixtures.items():
            for mode in ("success", "empty", "failure"):
                with self.subTest(alias=name, mode=mode):
                    payload = fixture["response" if mode == "success" else "empty"]
                    if mode == "failure":
                        payload = ("<Response><Errors><Error><Code>AccessDenied</Code><Message>fixture denied</Message></Error></Errors><RequestID>fixture</RequestID></Response>"
                                   if fixture["protocol"] in {"ec2", "query"} else {"__type": "AccessDeniedException", "message": "fixture denied"})
                    with self.endpoint([(400 if mode == "failure" else 200, payload)]) as (url, calls):
                        result = self.invoke(name, "--endpoint-url", url)
                        if mode == "failure":
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn("fixture denied", result.stderr)
                        else:
                            self.assertEqual(result.returncode, 0, result.stderr)
                            if mode == "success":
                                self.assertIn(fixture["expected"], result.stdout)
                        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
