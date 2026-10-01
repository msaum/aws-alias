#!/usr/bin/env python3
"""AWS alias workflows and recoverable bundle updates (Python 3.11+)."""

from __future__ import annotations

import argparse
import ast
import configparser
import contextlib
import csv
import difflib
import fcntl
import hashlib
import io
import http.client
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

FORMAT = 1
MIN_CLI = (2, 37, 7)
BUNDLE_FILES = ("alias", "aws_alias_manager.py")
REPOSITORY = "msaum/aws-alias"
MAX_DOWNLOAD = 5 * 1024 * 1024
NATIVE_TARGETS = {
    "apigateway": set(), "autoscaling": set(), "cloudformation": set(), "codepipeline": set(),
    "dynamodb": set(), "elasticbeanstalk": set(), "elasticache": set(), "servicecatalog": set(),
    "securityhub": set(), "configure": {"list-profiles", "mfa-login"}, "sts": {"get-caller-identity"},
    "iam": {"list-users"}, "logs": {"describe-log-groups"}, "ecr": {"describe-repositories"},
    "ec2": {"describe-instances", "describe-volumes", "describe-security-groups", "describe-regions",
            "describe-availability-zones", "describe-vpc-peering-connections", "describe-internet-gateways",
            "describe-nat-gateways", "describe-vpn-gateways", "describe-vpn-connections",
            "describe-instance-status", "describe-vpcs", "describe-subnets", "describe-route-tables"},
}
RETIRED = {
    "sg": "Use aws ec2 with an explicit operation.",
    "install": "Run python3 aws_alias_manager.py install from a clean checkout.",
    "rotate-iam-keys": "Use your separately reviewed IAM key-rotation procedure.",
    "iam-keys-days-remaining": "Use an explicit per-key age and rotation-policy report.",
    "create-assume-role": "Define the role and trust policy in reviewed infrastructure code.",
    "delete-virtual-mfa": "Use an administrator MFA deactivation/deletion procedure.",
    "authorize-my-ip-by-name": "Use allow-my-ip with an explicit group ID, protocol and port.",
    "allow-my-ip-all": "Use allow-my-ip with an explicit group ID, protocol and port.",
    "revoke-my-ip-all": "Use revoke-my-ip with an explicit group ID, protocol and port.",
    "assume": "Configure a role profile and select it with --profile.",
    "generate-sts-token": "Use supported AWS profile providers or configure mfa-login.",
    "region": "Use configure get region or configure set region with an explicit profile.",
    "delete-ami": "Use ami-snapshots <ami-id> to list the associated snapshots.",
}


class Error(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


class CommandError(Error):
    pass


def execute(argv, *, input_text=None, timeout=180):
    """Capture commands so failures cannot become successful transformations."""
    try:
        result = subprocess.run(
            [str(x) for x in argv], input=input_text, capture_output=True,
            text=True, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CommandError(f"Unable to run {argv[0]}: {exc}") from exc
    if result.returncode:
        raise CommandError(result.stderr.strip() or f"{argv[0]} failed", max(1, result.returncode))
    return result.stdout


def required_tool(name):
    path = shutil.which(name)
    if not path:
        raise Error(f"Required command '{name}' is missing. Install it before retrying.")
    return Path(path)


def cli_version(binary):
    value = execute([binary, "--version"])
    match = re.search(r"aws-cli/(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise Error("Unable to determine the AWS CLI version.")
    return tuple(map(int, match.groups()))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Error(f"Unable to read JSON at {path}: {exc}") from exc


def parse_aliases(data):
    parser = configparser.RawConfigParser(strict=True)
    try:
        parser.read_string(data.decode("utf-8"))
    except (ValueError, UnicodeError, configparser.Error) as exc:
        raise Error(f"Invalid alias file: {exc}") from exc
    if parser.sections() != ["toplevel"] or not parser["toplevel"]:
        raise Error("The distributed alias file must have a nonempty [toplevel] section.")
    aliases = dict(parser["toplevel"])
    for name, value in aliases.items():
        value = value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name) or not value:
            raise Error(f"Invalid alias definition: {name}")
        if value.startswith("!"):
            try:
                execute(["/bin/sh", "-n"], input_text=value[1:])
            except CommandError as exc:
                raise Error(f"Invalid shell syntax in {name}: {exc}") from exc
        else:
            try:
                args = [a.strip("\n") for a in shlex.split(value)]
            except ValueError as exc:
                raise Error(f"Invalid native alias {name}: {exc}") from exc
            # Native entries may refer to aliases; validate the graph below.
            if not args or not args[0]:
                raise Error(f"Empty native alias: {name}")
    for name in aliases:
        visited = set()
        target = name
        while target in aliases and not aliases[target].strip().startswith("!"):
            if target in visited:
                raise Error(f"Alias cycle involving {name}")
            visited.add(target)
            target = shlex.split(aliases[target].strip())[0]
    return aliases


def validate_bundle(files):
    if set(files) != {*BUNDLE_FILES, "bundle.json"}:
        raise Error("Bundle has unexpected or missing files.")
    try:
        manifest = json.loads(files["bundle.json"])
        if manifest["format"] != FORMAT or manifest["minimum_cli"] != "2.37.7":
            raise Error("Unsupported bundle format or minimum CLI.")
        if manifest["minimum_python"] != "3.11" or set(manifest["sha256"]) != set(BUNDLE_FILES):
            raise Error("Unsupported bundle dependencies or file list.")
        for name in BUNDLE_FILES:
            if digest(files[name]) != manifest["sha256"][name]:
                raise Error(f"Checksum mismatch for {name}.")
        aliases = parse_aliases(files["alias"])
        tree = ast.parse(files["aws_alias_manager.py"].decode("utf-8"))
        declarations = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                        if isinstance(node, ast.Assign) and len(node.targets) == 1
                        and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"WORKFLOWS", "RETIRED", "NATIVE_TARGETS"}}
        helpers = set(declarations["WORKFLOWS"]) | set(declarations["RETIRED"])
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        if not {"main", "run_workflow", "install", "upgrade", "update_aliases"}.issubset(functions):
            raise Error("Companion is missing required entry points.")
        for name, value in aliases.items():
            target = name
            while target in aliases and not aliases[target].strip().startswith("!"):
                command = shlex.split(aliases[target])
                target = command[0]
                if target not in aliases:
                    operations = declarations["NATIVE_TARGETS"].get(target)
                    if operations is None or (len(command) > 1 and command[1] not in operations):
                        raise Error(f"Unknown native target referenced by {name}.")
            if " run " in value and value.split(" run ", 1)[1].split()[0] not in helpers:
                raise Error(f"Unknown helper referenced by {name}.")
    except (KeyError, TypeError, ValueError, UnicodeError, SyntaxError) as exc:
        raise Error(f"Invalid bundle: {exc}") from exc
    if not {"upgrade", "update-aliases", "whoami"}.issubset(aliases):
        raise Error("Bundle is missing required entry points.")
    return manifest


class GitHubRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlparse(newurl)
        if url.scheme != "https" or url.hostname not in {"api.github.com", "raw.githubusercontent.com"}:
            raise Error("Repository download redirected outside the allowed HTTPS hosts.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "aws-alias-manager/1", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.build_opener(GitHubRedirects()).open(request, timeout=20) as response:
            data = response.read(MAX_DOWNLOAD + 1)
            declared = response.headers.get("Content-Length")
            if len(data) > MAX_DOWNLOAD or not data:
                raise Error("Repository response is empty or exceeds the size limit.")
            if declared and int(declared) != len(data):
                raise Error("Repository download was incomplete.")
            return data
    except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as exc:
        raise Error(f"Repository download failed: {exc}") from exc


def fetch_bundle(ref=None):
    if ref is not None and not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise Error("--ref must be a full lowercase 40-character commit SHA.", 2)
    try:
        if ref is None:
            repo = json.loads(download(f"https://api.github.com/repos/{REPOSITORY}"))
            branch = urllib.parse.quote(repo["default_branch"], safe="")
            ref = json.loads(download(f"https://api.github.com/repos/{REPOSITORY}/commits/{branch}"))["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise Error("GitHub returned an invalid commit SHA.")
    except (KeyError, ValueError, TypeError) as exc:
        raise Error(f"Invalid GitHub metadata: {exc}") from exc
    files = {name: download(f"https://raw.githubusercontent.com/{REPOSITORY}/{ref}/{name}")
             for name in (*BUNDLE_FILES, "bundle.json")}
    validate_bundle(files)
    return ref, files


def store_path():
    return Path.home() / ".aws" / "cli" / "aws-alias"


def ensure_store():
    store = store_path()
    if store.is_symlink():
        raise Error("The bundle store must be a directory owned by the invoking user.")
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not store.is_dir() or store.stat().st_uid != os.getuid():
        raise Error("The bundle store is owned by another user.")
    for child in (store / "bundles", store / "backups"):
        if child.is_symlink() or (child.exists() and (not child.is_dir() or child.stat().st_uid != os.getuid())):
            raise Error("The bundle and backup directories must be owned directories.")
    return store


@contextlib.contextmanager
def update_lock():
    store = ensure_store()
    path = store / "update.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Error("Another CLI or alias update is running.", 4) from exc
        yield store
    finally:
        os.close(fd)


def current_bundle():
    store = ensure_store()
    pointer = store / "current"
    if not pointer.is_symlink():
        raise Error("No managed bundle is installed. Bootstrap from a clean repository checkout.")
    target = os.readlink(pointer)
    if not re.fullmatch(r"bundles/[0-9a-f]{40}-[0-9a-f]{12}", target):
        raise Error("The current bundle pointer has an unexpected target.")
    directory = store / target
    if directory.is_symlink() or not directory.is_dir():
        raise Error("The current bundle directory is unavailable.")
    for name in (*BUNDLE_FILES, "bundle.json", "installed.json"):
        if (directory / name).is_symlink() or not (directory / name).is_file():
            raise Error(f"Unexpected bundle file: {name}")
    record = read_json(directory / "installed.json")
    if (not isinstance(record, dict) or record.get("format") != FORMAT
            or record.get("commit") != directory.name[:40]
            or not isinstance(record.get("sha256"), dict)
            or set(record["sha256"]) != {*BUNDLE_FILES, "bundle.json"}
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in record["sha256"].values())):
        raise Error("Invalid installed bundle metadata.")
    return directory, record


def local_hashes(directory):
    return {name: digest((directory / name).read_bytes()) for name in (*BUNDLE_FILES, "bundle.json")}


def managed_alias():
    path = Path.home() / ".aws" / "cli" / "alias"
    return path.is_symlink() and os.readlink(path) == "aws-alias/current/alias"


def differences(directory, files):
    for name in BUNDLE_FILES:
        before = (directory / name).read_text(encoding="utf-8", errors="replace") if (directory / name).exists() else ""
        after = files[name].decode("utf-8")
        if before != after:
            print("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                              fromfile=f"installed/{name}", tofile=f"candidate/{name}")), end="")


def backup(directory=None, alias_file=None):
    target = ensure_store() / "backups" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12])
    target.mkdir(parents=True, mode=0o700)
    if directory:
        for name in (*BUNDLE_FILES, "bundle.json", "installed.json"):
            shutil.copyfile(directory / name, target / name)
            (target / name).chmod(0o600)
    if alias_file is not None:
        shutil.copyfile(alias_file, target / "personal-alias")
        (target / "personal-alias").chmod(0o600)
    print(f"Backup: {target}", file=sys.stderr)
    return target


def switch_bundle(bundle_id):
    store = ensure_store()
    temp = store / (".current-" + uuid.uuid4().hex)
    try:
        temp.symlink_to("bundles/" + bundle_id)
        os.replace(temp, store / "current")
    finally:
        if temp.is_symlink():
            temp.unlink()


def publish_bundle(ref, files, *, previous=None, expected=None, existing_alias=None):
    validate_bundle(files)
    store = ensure_store()
    bundles = store / "bundles"
    bundles.mkdir(exist_ok=True, mode=0o700)
    bundle_id = ref + "-" + uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=".staging-", dir=bundles) as staging:
        stage = Path(staging)
        for name, contents in files.items():
            (stage / name).write_bytes(contents)
            (stage / name).chmod(0o600)
        metadata = {"format": FORMAT, "commit": ref, "previous": previous,
                    "installed_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": {name: digest(data) for name, data in files.items()}}
        (stage / "installed.json").write_text(encode(metadata) + "\n", encoding="utf-8")
        if expected:
            old, record = current_bundle()
            if old.name != previous or local_hashes(old) != expected or not managed_alias():
                raise Error("Installed files changed during the update. Review the new diff.", 3)
        if existing_alias is not None:
            alias_file, expected_bytes = existing_alias
            if alias_file.is_symlink() or (alias_file.read_bytes() if alias_file.exists() else None) != expected_bytes:
                raise Error("The alias file changed during installation.", 3)
        # Keep publication on the same filesystem as the pointer replacement.
        destination = bundles / bundle_id
        stage.rename(destination)
        # TemporaryDirectory sees a missing staging directory after rename.
    switch_bundle(bundle_id)
    print(f"Installed {REPOSITORY}@{ref}")


def clean_checkout(root):
    root = Path(root).resolve()
    top = Path(execute(["git", "-C", root, "rev-parse", "--show-toplevel"]).strip()).resolve()
    if top != root:
        raise Error("Bootstrap must run from this repository's root checkout.")
    dirty = execute(["git", "-C", root, "status", "--porcelain", "--untracked-files=all", "--", *BUNDLE_FILES, "bundle.json"])
    if dirty.strip():
        raise Error("Commit the bundle files before bootstrapping from this checkout.")
    ref = execute(["git", "-C", root, "rev-parse", "HEAD"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise Error("Unable to identify the checkout commit.")
    return ref


def install(args):
    root = Path(__file__).resolve().parent
    ref = clean_checkout(root)
    files = {name: (root / name).read_bytes() for name in (*BUNDLE_FILES, "bundle.json")}
    validate_bundle(files)
    binary = required_tool("aws")
    if cli_version(binary) < MIN_CLI:
        raise Error("AWS CLI 2.37.7+ is required. Perform the one-time official CLI upgrade first.")
    with update_lock():
        alias_file = Path.home() / ".aws" / "cli" / "alias"
        if managed_alias():
            raise Error("A managed bundle is already installed. Use update-aliases.")
        if alias_file.is_symlink() or (alias_file.exists() and not alias_file.is_file()):
            raise Error("The existing alias path has an unexpected type; preserve it and resolve it manually.")
        original = alias_file.read_bytes() if alias_file.exists() else None
        if original is not None:
            print("".join(difflib.unified_diff(original.decode("utf-8", errors="replace").splitlines(True),
                                              files["alias"].decode().splitlines(True),
                                              fromfile="personal/alias", tofile="candidate/alias")), end="")
            if not args.replace_local:
                raise Error("An alias file already exists. Review the diff and rerun install --replace-local.", 3)
            backup(alias_file=alias_file)
        publish_bundle(ref, files, existing_alias=(alias_file, original))
        temp = alias_file.parent / (".alias-" + uuid.uuid4().hex)
        try:
            temp.symlink_to("aws-alias/current/alias")
            if alias_file.is_symlink() or (alias_file.read_bytes() if alias_file.exists() else None) != original:
                raise Error("The alias file changed before link activation.", 3)
            os.replace(temp, alias_file)
        finally:
            if temp.is_symlink():
                temp.unlink()


def update_aliases(args):
    if args.replace_local and not args.ref:
        raise Error("Explicit replacement requires --replace-local --ref <full-commit-sha>.", 2)
    if args.check and (args.replace_local or args.rollback):
        raise Error("--check cannot be combined with replacement or rollback.", 2)
    lock = contextlib.nullcontext() if args.check else update_lock()
    with lock:
        old, metadata = current_bundle()
        observed = local_hashes(old)
        modified = observed != metadata["sha256"] or not managed_alias()
        if args.rollback:
            previous = metadata.get("previous")
            if not previous or not re.fullmatch(r"[0-9a-f]{40}-[0-9a-f]{12}", previous):
                raise Error("No previous bundle is available.")
            target = store_path() / "bundles" / previous
            if target.is_symlink():
                raise Error("Unexpected previous bundle directory.")
            for name in (*BUNDLE_FILES, "bundle.json", "installed.json"):
                if (target / name).is_symlink() or not (target / name).is_file():
                    raise Error("Unexpected previous bundle file.")
            record = read_json(target / "installed.json")
            files = {name: (target / name).read_bytes() for name in (*BUNDLE_FILES, "bundle.json")}
            validate_bundle(files)
            if local_hashes(target) != record["sha256"]:
                raise Error("The previous bundle has local changes and cannot be restored.", 3)
            ref = record["commit"]
            if record.get("format") != FORMAT or ref != target.name[:40]:
                raise Error("Invalid previous bundle metadata.")
            if args.ref and args.ref != ref:
                raise Error("--ref does not identify the previous bundle.", 2)
        else:
            ref, files = fetch_bundle(args.ref)
        print(f"Installed: {metadata['commit']}\nAvailable: {ref}")
        if modified or args.check:
            differences(old, files)
        if modified and not args.replace_local:
            raise Error(f"Local changes detected. Preserve them or review the diff and use --replace-local --ref {ref}.", 3)
        if not managed_alias():
            raise Error("The installed alias link was replaced. Restore or bootstrap that path explicitly.", 3)
        if args.check:
            return
        if not modified and metadata["commit"] == ref and observed == {name: digest(data) for name, data in files.items()}:
            print("The installed bundle is current.")
            return
        backup(directory=old)
        if args.rollback:
            if local_hashes(old) != observed or not managed_alias():
                raise Error("Installed files changed during rollback.", 3)
            if local_hashes(target) != record["sha256"]:
                raise Error("The previous bundle changed during rollback.", 3)
            switch_bundle(previous)
            print(f"Restored {REPOSITORY}@{ref}")
        else:
            publish_bundle(ref, files, previous=old.name, expected=observed)


def detect_installation(binary):
    system, machine = platform.system(), platform.machine().lower()
    if system not in {"Darwin", "Linux"} or machine not in {"arm64", "aarch64", "x86_64", "amd64"}:
        raise Error(f"Unsupported platform: {system}/{machine}")
    real = Path(binary).resolve()
    brew = shutil.which("brew") if system == "Darwin" else None
    if brew:
        try:
            prefix = Path(execute([brew, "--prefix", "awscli"]).strip()).resolve()
        except CommandError:
            prefix = None
        if prefix and real.is_relative_to(prefix):
            pinned = execute([brew, "list", "--pinned"]).splitlines()
            if "awscli" in pinned:
                raise Error("Homebrew awscli is pinned. Unpin it explicitly before upgrading.")
            return {"method": "homebrew", "binary": str(binary), "backend": brew,
                    "privileged": False, "command": [brew, "upgrade", "awscli"]}
    # Current official installers record their root and binary directory.
    metadata_file = real.parent / "awscli" / "data" / "metadata.json"
    install_file = real.parent / "awscli" / "data" / "install.json"
    if metadata_file.is_file() and install_file.is_file():
        metadata, installation = read_json(metadata_file), read_json(install_file)
        install_root = Path(installation.get("install_dir", "")).resolve()
        bin_root = Path(installation.get("bin_dir", "")).resolve()
        if (metadata.get("distribution_source") == "exe" and bin_root == Path(binary).parent.resolve()
                and (real.parent == install_root or real.is_relative_to(install_root / "v2"))
                and not any(part in {"Cellar", "Caskroom", "snap", ".venv", "site-packages"} for part in real.parts)):
            return {"method": "official", "binary": str(binary), "root": str(install_root),
                    "privileged": install_root.stat().st_uid == 0, "command": [str(binary), "update"]}
        raise Error("Official installer metadata does not match the active CLI path.")
    # Older official installations contain a versioned v2/<version>/dist layout.
    for parent in real.parents:
        if parent.name == "dist" and parent.parent.parent.name == "v2":
            install_root = parent.parent.parent.parent
            # Homebrew and unrecognized package owners must not fall through.
            if any(part in {"Cellar", "Caskroom", "snap", ".venv", "site-packages"} for part in real.parts):
                break
            return {"method": "official", "binary": str(binary), "root": str(install_root),
                    "privileged": install_root.stat().st_uid == 0,
                    "command": [str(binary), "update"]}
    raise Error("Unable to prove ownership of the active AWS CLI. Use its installation provider's upgrade procedure.")


def upgrade(args):
    binary = required_tool("aws")
    before = cli_version(binary)
    info = detect_installation(binary)
    if info["method"] == "official":
        if before < MIN_CLI:
            raise Error("This official CLI predates the supported updater. Upgrade once using https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        execute([binary, "update", "help"])
    print(f"Active CLI: {binary}\nVersion: {'.'.join(map(str, before))}\nMethod: {info['method']}")
    command = info["command"]
    if info["privileged"]:
        if not os.isatty(0) and not args.dry_run:
            raise Error("This system installation requires an interactive terminal for sudo.")
        command = [str(required_tool("sudo")), *command]
    print("Action: " + shlex.join(command))
    if args.dry_run:
        if args.all:
            print("Then check and update the alias bundle.")
        return
    with update_lock():
        if info["method"] == "homebrew":
            execute([info["backend"], "update"])
        # Preserve terminal interaction for the native updater and sudo.
        try:
            result = subprocess.run(command, check=False)
        except OSError as exc:
            raise Error(f"CLI update could not start: {exc}") from exc
        if result.returncode:
            raise Error("CLI update failed; alias updates were not started.", max(1, result.returncode))
        after_binary = required_tool("aws")
        after = cli_version(after_binary)
        if str(after_binary) != str(binary) or after < before or after < MIN_CLI:
            raise Error("CLI verification failed: the active path or version is unexpected.")
        print(f"Verified CLI: {after_binary} {'.'.join(map(str, after))}")
    if args.all:
        try:
            update_aliases(argparse.Namespace(check=False, replace_local=False, ref=None, rollback=False))
        except Error as exc:
            raise Error(f"CLI update succeeded; alias update failed: {exc}", exc.code) from exc


class AWS:
    def __init__(self, args):
        self.binary = required_tool("aws")
        self.profile = args.profile or os.environ.get("AWS_PROFILE") or os.environ.get("AWS_DEFAULT_PROFILE")
        self.region = args.region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        self.endpoint = args.endpoint_url
        self.ca_bundle = args.ca_bundle
        if not self.profile:
            raise Error(profile_guidance(args.workflow), 2)
        self.options = ["--profile", self.profile, "--no-cli-pager", "--no-cli-auto-prompt",
                        "--cli-connect-timeout", "15", "--cli-read-timeout", "30"]
        if self.endpoint:
            self.options += ["--endpoint-url", self.endpoint]
        if self.ca_bundle:
            self.options += ["--ca-bundle", self.ca_bundle]
        print(f"Scope: profile={self.profile}; region={self.region or 'profile configuration'}", file=sys.stderr)

    def call(self, service, operation, *params, region=None, output="json"):
        selected = region or self.region
        options = self.options + (["--region", selected] if selected else [])
        return execute([self.binary, service, operation, *params, *options, "--output", output])

    def json(self, service, operation, *params, region=None):
        raw = self.call(service, operation, *params, region=region)
        try:
            result = json.loads(raw)
        except ValueError as exc:
            raise Error(f"{service} {operation} returned invalid JSON.") from exc
        if not isinstance(result, dict):
            raise Error(f"{service} {operation} returned an unexpected response shape.")
        return result


def emit(value, output=None):
    output = output or "json"
    if output == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2))
    elif output == "text":
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            print("\t".join("" if x is None else str(x) for x in row.values()) if isinstance(row, dict) else ("" if row is None else row))
    else:
        rows = value if isinstance(value, list) else [value]
        if not rows:
            return
        if not isinstance(rows[0], dict):
            rows = [{"Value": row} for row in rows]
        columns = list(dict.fromkeys(k for row in rows for k in row))
        values = [["" if row.get(k) is None else str(row[k]) for k in columns] for row in rows]
        widths = [max(len(k), *(len(row[i]) for row in values)) for i, k in enumerate(columns)]
        print(" | ".join(k.ljust(widths[i]) for i, k in enumerate(columns)))
        for row in values:
            print(" | ".join(x.ljust(widths[i]) for i, x in enumerate(row)))


def csv_output(headers, rows):
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)


def name_tag(resource, key="Name"):
    return next((tag.get("Value") for tag in resource.get("Tags", []) or [] if tag.get("Key") == key), None)


def instances(data):
    return [item for reservation in data.get("Reservations", []) for item in reservation.get("Instances", [])]


def filters(**values):
    return encode([{"Name": key.replace("__", ":"), "Values": value if isinstance(value, list) else [value]}
                   for key, value in values.items()])


def resource_id(prefix):
    def validate(value):
        if not re.fullmatch(prefix + r"-[0-9a-f]+", value):
            raise argparse.ArgumentTypeError(f"Expected a {prefix}- resource ID.")
        return value
    return validate


def address(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected an IPv4 or IPv6 address.") from exc


def port(value):
    try:
        pieces = value.split("-")
        start = int(pieces[0])
        end = int(pieces[1]) if len(pieces) == 2 else start
        if len(pieces) > 2 or not 0 <= start <= end <= 65535:
            raise ValueError
        return start, end
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be 0–65535 or an ordered port range.") from exc


def current_ip():
    request = urllib.request.Request("https://checkip.amazonaws.com", headers={"User-Agent": "aws-alias-manager/1"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read(128).decode().strip()
        result = ipaddress.ip_address(data)
    except (OSError, ValueError, UnicodeError, http.client.HTTPException) as exc:
        raise Error(f"Public IP lookup failed: {exc}") from exc
    if result.version != 4:
        raise Error("The automatic public IP lookup must return IPv4; supply IPv6 explicitly.")
    return str(result)


def rules(groups, *, public=False, ssh=False):
    rows = []
    for group in groups:
        for direction, key in (("ingress", "IpPermissions"), ("egress", "IpPermissionsEgress")):
            if (public or ssh) and direction != "ingress":
                continue
            for rule in group.get(key, []) or []:
                protocol = str(rule.get("IpProtocol", ""))
                start, end = rule.get("FromPort"), rule.get("ToPort")
                if ssh and not (protocol == "-1" or (protocol in {"tcp", "6"} and start is not None and end is not None and start <= 22 <= end)):
                    continue
                peers = [(r.get("CidrIp"), "ipv4") for r in rule.get("IpRanges", [])]
                peers += [(r.get("CidrIpv6"), "ipv6") for r in rule.get("Ipv6Ranges", [])]
                if not public:
                    peers += [(r.get("GroupId"), "group") for r in rule.get("UserIdGroupPairs", [])]
                    peers += [(r.get("PrefixListId"), "prefix-list") for r in rule.get("PrefixListIds", [])]
                for peer, kind in peers:
                    if public and peer not in {"0.0.0.0/0", "::/0"}:
                        continue
                    rows.append({"GroupId": group.get("GroupId"), "GroupName": group.get("GroupName"),
                                 "Direction": direction, "Protocol": protocol, "FromPort": start,
                                 "ToPort": end, "PeerType": kind, "Peer": peer})
    return rows


def workflow_parser(name):
    p = argparse.ArgumentParser(prog="aws " + name, allow_abbrev=False)
    p.set_defaults(workflow=name)
    p.add_argument("--profile", "--aws-profile", dest="profile")
    p.add_argument("--region", "--aws-region", dest="region")
    p.add_argument("--endpoint-url", "--aws-endpoint-url", dest="endpoint_url")
    p.add_argument("--ca-bundle", "--aws-ca-bundle", dest="ca_bundle")
    p.add_argument("--output", "--aws-output", dest="output", choices=("json", "text", "table"))
    if name == "tostring":
        p.add_argument("file", type=Path)
    elif name in {"list-user-keys", "list-virtual-mfa"}:
        p.add_argument("username", help="Explicit IAM username; IAM device APIs do not describe SSO users.")
    elif name == "find-access-key":
        p.add_argument("key")
    elif name == "sg-rules":
        p.add_argument("group_id", type=resource_id("sg"))
    elif name == "get-group-id":
        p.add_argument("group_name")
        p.add_argument("vpc_id", type=resource_id("vpc"))
    elif name in {"allow-my-ip", "revoke-my-ip"}:
        p.add_argument("group_id", type=resource_id("sg"))
        p.add_argument("protocol", choices=("tcp", "udp"))
        p.add_argument("port", type=port)
        p.add_argument("cidr", nargs="?")
    elif name == "ami-snapshots":
        p.add_argument("ami_id", type=resource_id("ami"))
    elif name == "list-instances":
        p.add_argument("regions", nargs="+")
    elif name == "search-instances":
        p.add_argument("name")
    elif name == "find-instances-in-sg":
        p.add_argument("group_id", type=resource_id("sg"))
        p.add_argument("tag_key", nargs="?", default="Name")
    elif name == "get-asg-instance-ips":
        p.add_argument("asg_name")
    elif name in {"find-host-by-instance-id", "get-dns-from-instance-id"}:
        p.add_argument("instance_id", type=resource_id("i"))
    elif name in {"find-instance-by-public-ip", "find-nat-gateway-by-public-ip"}:
        p.add_argument("ip", type=address)
    elif name == "get-instance-id-from-dns":
        p.add_argument("dns_name")
    elif name == "amazon-linux-amis":
        p.add_argument("architecture", choices=("x86_64", "arm64"), nargs="?", default="x86_64")
    elif name == "last-log":
        p.add_argument("log_group")
        p.add_argument("--since", default="10m")
        p.add_argument("--follow", action="store_true")
    elif name == "docker-ecr-login":
        p.add_argument("registry")
    elif name == "ecr-scan-findings":
        p.add_argument("repository")
        image = p.add_mutually_exclusive_group(required=True)
        image.add_argument("--image-tag")
        image.add_argument("--image-digest")
    elif name == "events-list-csv":
        p.add_argument("--event-bus", default="default")
    return p


def profile_guidance(name, *, explicit_region=False):
    parser = workflow_parser(name)
    positional = ["<" + action.dest.replace("_", "-") + ">"
                  for action in parser._actions
                  if not action.option_strings and action.nargs != "?"]
    for group in parser._mutually_exclusive_groups:
        if group.required:
            action = group._group_actions[0]
            positional += [action.option_strings[0], "<" + action.dest.replace("_", "-") + ">"]
    command = " ".join(["aws", name, *positional])
    region = " --aws-region REGION" if explicit_region else ""
    separator_region = " --region REGION" if explicit_region else ""
    selection = "an explicit profile and region" if explicit_region else "a profile"
    message = (f"Select {selection} using either:\n"
               f"  {command} --aws-profile PROFILE{region}\n"
               f"  {command} -- --profile PROFILE{separator_region}\n"
               "AWS CLI consumes ordinary --profile flags before invoking this helper.")
    if not explicit_region:
        message += "\nYou can also set AWS_PROFILE or AWS_DEFAULT_PROFILE."
    return message


WORKFLOWS = {
    "tostring", "my-ip", "list-user-keys", "list-virtual-mfa", "find-access-key",
    "find-users-without-mfa", "sg-rules", "get-group-id", "public-ports", "find-ssh-open",
    "allow-my-ip", "revoke-my-ip", "ami-snapshots", "list-instances", "search-instances",
    "find-instances-in-sg", "get-asg-instance-ips", "find-host-by-instance-id",
    "find-instance-by-public-ip", "find-nat-gateway-by-public-ip", "list-hosts-csv",
    "get-dns-from-instance-id", "get-instance-id-from-dns", "amazon-linux-amis", "last-log",
    "docker-ecr-login", "ecr-scan-findings", "sh-quick-report", "sh-findings-csv",
    "lambda-list-csv", "events-list-csv",
}


def run_workflow(name, argv):
    if name in RETIRED:
        raise Error(f"{name} is retired. {RETIRED[name]}", 2)
    if name not in WORKFLOWS:
        raise Error(f"Unknown workflow: {name}", 2)
    args = workflow_parser(name).parse_args([arg for arg in argv if arg != "--"])
    if name == "tostring":
        print(json.dumps(encode(read_json(args.file)), ensure_ascii=False))
        return
    if name == "my-ip":
        print(current_ip())
        return
    if name.endswith("-csv") and args.output:
        raise Error("CSV commands have a fixed CSV output contract.", 2)
    if name == "find-access-key" and not re.fullmatch(r"[A-Z0-9]{20}", args.key):
        raise Error("Expected a 20-character access key ID.", 2)
    if name in {"allow-my-ip", "revoke-my-ip"}:
        if not args.profile or not args.region:
            raise Error(profile_guidance(name, explicit_region=True), 2)
        try:
            network = ipaddress.ip_network(args.cidr or (current_ip() + "/32"), strict=True)
        except ValueError as exc:
            raise Error("Expected a single-host IPv4 /32 or IPv6 /128 CIDR.", 2) from exc
        if network.prefixlen != network.max_prefixlen:
            raise Error("The my-IP helpers accept only /32 or /128 host CIDRs.", 2)
    if name == "docker-ecr-login":
        if not args.region or not args.profile:
            raise Error(profile_guidance(name, explicit_region=True), 2)
        expected = re.fullmatch(r"\d{12}\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com(?:\.cn)?", args.registry)
        if not expected or expected.group(1) != args.region:
            raise Error("Registry must be a private ECR hostname in the selected region.", 2)
    if name == "list-instances" and args.regions != ["all"]:
        if any(not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-\d+", region) for region in args.regions):
            raise Error("Supply exact region names or the single value 'all'.", 2)
    aws = AWS(args)
    data = None
    if name == "list-user-keys":
        data = aws.json("iam", "list-access-keys", "--user-name", args.username).get("AccessKeyMetadata", [])
    elif name == "list-virtual-mfa":
        data = aws.json("iam", "list-mfa-devices", "--user-name", args.username).get("MFADevices", [])
    elif name in {"find-access-key", "find-users-without-mfa"}:
        data = []
        for user in aws.json("iam", "list-users").get("Users", []):
            username = user["UserName"]
            if name == "find-access-key":
                keys = aws.json("iam", "list-access-keys", "--user-name", username).get("AccessKeyMetadata", [])
                if any(key.get("AccessKeyId") == args.key for key in keys):
                    data.append(username)
            elif not aws.json("iam", "list-mfa-devices", "--user-name", username).get("MFADevices", []):
                data.append(username)
        if name == "find-access-key" and not data:
            print("No matching IAM user owns this key in the selected account.", file=sys.stderr)
    elif name == "get-group-id":
        groups = aws.json("ec2", "describe-security-groups", "--filters",
                          filters(**{"group-name": args.group_name, "vpc-id": args.vpc_id})).get("SecurityGroups", [])
        if len(groups) != 1:
            raise Error(f"Expected exactly one group in that VPC; found {len(groups)}.")
        data = groups[0]["GroupId"]
    elif name in {"sg-rules", "public-ports", "find-ssh-open"}:
        params = ["--group-ids", args.group_id] if name == "sg-rules" else []
        groups = aws.json("ec2", "describe-security-groups", *params).get("SecurityGroups", [])
        data = rules(groups, public=name == "public-ports", ssh=name == "find-ssh-open")
    elif name in {"allow-my-ip", "revoke-my-ip"}:
        identity = aws.json("sts", "get-caller-identity")
        print(f"Account: {identity['Account']}; group={args.group_id}; region={args.region}", file=sys.stderr)
        start, end = args.port
        permission = {"IpProtocol": args.protocol, "FromPort": start, "ToPort": end,
                      "IpRanges" if network.version == 4 else "Ipv6Ranges":
                          [{"CidrIp" if network.version == 4 else "CidrIpv6": str(network)}]}
        operation = "authorize-security-group-ingress" if name == "allow-my-ip" else "revoke-security-group-ingress"
        try:
            data = aws.json("ec2", operation, "--group-id", args.group_id, "--ip-permissions", encode([permission]))
        except CommandError as exc:
            expected_code = "InvalidPermission.Duplicate" if name == "allow-my-ip" else "InvalidPermission.NotFound"
            if f"({expected_code})" not in str(exc):
                raise
            data = {"Changed": False, "Reason": expected_code}
    elif name == "ami-snapshots":
        images = aws.json("ec2", "describe-images", "--image-ids", args.ami_id).get("Images", [])
        data = sorted({mapping["Ebs"]["SnapshotId"] for image in images for mapping in image.get("BlockDeviceMappings", [])
                       if mapping.get("Ebs", {}).get("SnapshotId")})
    elif name == "list-instances":
        selected = args.regions
        if selected == ["all"]:
            selected = sorted({region["RegionName"] for region in aws.json("ec2", "describe-regions").get("Regions", [])})
        data, failures = [], []
        for region in dict.fromkeys(selected):
            try:
                rows = instances(aws.json("ec2", "describe-instances", region=region))
                data.extend({"Region": region, "InstanceId": row.get("InstanceId"), "Name": name_tag(row),
                             "InstanceType": row.get("InstanceType"), "PublicIpAddress": row.get("PublicIpAddress"),
                             "State": row.get("State", {}).get("Name")} for row in rows)
            except Error as exc:
                failures.append(f"{region}: {exc}")
        emit(data, args.output)
        if failures:
            raise Error("Some regions failed: " + "; ".join(failures))
        return
    elif name in {"search-instances", "find-instances-in-sg", "get-asg-instance-ips", "find-host-by-instance-id",
                  "find-instance-by-public-ip", "list-hosts-csv", "get-dns-from-instance-id", "get-instance-id-from-dns"}:
        params = []
        if name == "search-instances":
            params = ["--filters", filters(**{"instance-state-name": ["running", "stopped"]})]
        elif name == "find-instances-in-sg":
            params = ["--filters", filters(**{"network-interface.group-id": args.group_id})]
        elif name == "get-asg-instance-ips":
            params = ["--filters", filters(**{"tag:aws:autoscaling:groupName": args.asg_name})]
        elif name in {"find-host-by-instance-id", "get-dns-from-instance-id"}:
            params = ["--instance-ids", args.instance_id]
        elif name == "find-instance-by-public-ip":
            params = ["--filters", filters(**{"ip-address": args.ip})]
        elif name == "get-instance-id-from-dns":
            params = ["--filters", filters(**{"dns-name": args.dns_name})]
        rows = instances(aws.json("ec2", "describe-instances", *params))
        if name == "list-hosts-csv":
            csv_output(["InstanceId", "InstanceType", "PrivateIpAddress", "SubnetId", "Name"],
                       [[row.get(k) for k in ("InstanceId", "InstanceType", "PrivateIpAddress", "SubnetId")] + [name_tag(row)] for row in rows])
            return
        if name == "search-instances":
            rows = [row for row in rows if args.name in (name_tag(row) or "")]
        if name == "get-asg-instance-ips":
            data = [row["PrivateIpAddress"] for row in rows if row.get("PrivateIpAddress")]
        elif name in {"find-host-by-instance-id", "get-dns-from-instance-id", "get-instance-id-from-dns"}:
            key = {"find-host-by-instance-id": "PrivateDnsName", "get-dns-from-instance-id": "PublicDnsName", "get-instance-id-from-dns": "InstanceId"}[name]
            data = [row[key] for row in rows if row.get(key)]
        else:
            data = [{"InstanceId": row.get("InstanceId"), "Name": name_tag(row, args.tag_key if name == "find-instances-in-sg" else "Name"),
                     "PrivateIpAddress": row.get("PrivateIpAddress"), "PublicIpAddress": row.get("PublicIpAddress")} for row in rows]
    elif name == "find-nat-gateway-by-public-ip":
        gateways = aws.json("ec2", "describe-nat-gateways").get("NatGateways", [])
        data = [{"NatGatewayId": row.get("NatGatewayId"), "Name": name_tag(row)} for row in gateways
                if any(peer.get("PublicIp") == args.ip for peer in row.get("NatGatewayAddresses", []))]
    elif name == "amazon-linux-amis":
        parameter = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-" + args.architecture
        data = aws.json("ssm", "get-parameter", "--name", parameter)["Parameter"]["Value"]
    elif name == "last-log":
        params = ["logs", "tail", args.log_group, "--since", args.since, *aws.options]
        if aws.region:
            params += ["--region", aws.region]
        if args.follow:
            params.append("--follow")
        result = subprocess.run([str(aws.binary), *params], check=False)
        if result.returncode:
            raise Error("CloudWatch log tail failed.", max(1, result.returncode))
        return
    elif name == "docker-ecr-login":
        docker = required_tool("docker")
        password = aws.call("ecr", "get-login-password", output="text").strip()
        if not password:
            raise Error("ECR returned an empty password.")
        result = execute([docker, "login", "--username", "AWS", "--password-stdin", args.registry], input_text=password + "\n")
        print(result, end="")
        return
    elif name == "ecr-scan-findings":
        image = {"imageTag": args.image_tag} if args.image_tag else {"imageDigest": args.image_digest}
        response = aws.json("ecr", "describe-image-scan-findings", "--repository-name", args.repository, "--image-id", encode(image))
        status = response.get("imageScanStatus", {}).get("status", "UNKNOWN")
        scan = response.get("imageScanFindings", {})
        findings = [{"severity": row.get("severity"), "name": row.get("name"), "description": row.get("description"),
                     "findingArn": row.get("findingArn")} for row in (scan.get("findings", []) or []) + (scan.get("enhancedFindings", []) or [])]
        data = {"status": status, "imageId": image, "findings": findings}
        emit(data, args.output)
        if status not in {"COMPLETE", "ACTIVE"}:
            raise Error(f"Image scan is not complete: {status}")
        return
    elif name in {"sh-quick-report", "sh-findings-csv"}:
        selection = {"WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
                     "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]}
        rows = aws.json("securityhub", "get-findings", "--filters", encode(selection)).get("Findings", [])
        print("Security Hub scope: ACTIVE records with NEW workflow status in the selected account/region.", file=sys.stderr)
        if name == "sh-quick-report":
            data = [{"Severity": severity, "Count": sum(row.get("Severity", {}).get("Label") == severity for row in rows),
                     "Titles": sorted({row.get("Title", "") for row in rows if row.get("Severity", {}).get("Label") == severity})}
                    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL")]
        else:
            headers = ["Title", "Description", "Region", "GeneratorId", "FirstObservedAt", "LastObservedAt", "CreatedAt", "UpdatedAt",
                       "Severity.Label", "Id", "Resources.Type", "Resources.Id", "Remediation.Text", "Remediation.Url"]
            values = []
            for row in rows:
                recommendation = (row.get("Remediation") or {}).get("Recommendation") or {}
                for resource in row.get("Resources", []) or [{}]:
                    values.append([row.get(k) for k in headers[:8]] + [row.get("Severity", {}).get("Label"), row.get("Id"),
                                  resource.get("Type"), resource.get("Id"), recommendation.get("Text"), recommendation.get("Url")])
            csv_output(headers, values)
            return
    elif name == "lambda-list-csv":
        rows = aws.json("lambda", "list-functions").get("Functions", [])
        headers = ["FunctionName", "Description", "FunctionArn", "Runtime", "Role", "Handler", "CodeSize", "Timeout", "MemorySize", "LastModified", "TracingConfig.Mode", "PackageType"]
        csv_output(headers, [[row.get(k) for k in headers[:10]] + [(row.get("TracingConfig") or {}).get("Mode"), row.get("PackageType")] for row in rows])
        return
    elif name == "events-list-csv":
        rows = aws.json("events", "list-rules", "--event-bus-name", args.event_bus).get("Rules", [])
        print(f"Event bus: {args.event_bus}", file=sys.stderr)
        headers = ["Name", "EventBusName", "Description", "Arn", "State", "ScheduleExpression"]
        csv_output(headers, [[row.get("Name"), row.get("EventBusName", args.event_bus), *[row.get(k) for k in headers[2:]]] for row in rows])
        return
    emit(data, args.output)


def main(argv=None):
    if sys.version_info < (3, 11):
        print("Python 3.11+ is required.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("install", help="Bootstrap from a clean checkout.", allow_abbrev=False)
    setup.add_argument("--replace-local", action="store_true")
    cli = commands.add_parser("upgrade", help="Update the active AWS CLI.", allow_abbrev=False)
    cli.add_argument("--all", action="store_true")
    cli.add_argument("--dry-run", action="store_true")
    aliases = commands.add_parser("aliases", help="Update or restore the managed alias bundle.", allow_abbrev=False)
    modes = aliases.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--rollback", action="store_true")
    aliases.add_argument("--replace-local", action="store_true")
    aliases.add_argument("--ref")
    run = commands.add_parser("run", help="Execute an alias workflow.", allow_abbrev=False)
    run.add_argument("name")
    run.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            install(args)
        elif args.command == "upgrade":
            upgrade(args)
        elif args.command == "aliases":
            update_aliases(args)
        else:
            run_workflow(args.name, args.args)
        return 0
    except Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
