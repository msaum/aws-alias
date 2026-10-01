#!/usr/bin/env python3
"""Check the source bundle; --write-manifest refreshes its checked-in hashes."""
import argparse
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import aws_alias_manager as manager


def model_check(command):
    with tempfile.TemporaryDirectory(prefix="aws-alias-models-") as directory:
        root = Path(directory)
        (root / "config").write_text("")
        (root / "credentials").write_text("")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": directory,
               "AWS_CONFIG_FILE": str(root / "config"), "AWS_SHARED_CREDENTIALS_FILE": str(root / "credentials"),
               "AWS_EC2_METADATA_DISABLED": "true", "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off"}
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise manager.Error(result.stderr.strip() or "AWS model check failed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--aws-models", action="store_true", help="Check native aliases using offline AWS input skeletons.")
    parser.add_argument("--shellcheck", action="store_true", help="Lint extracted shell bodies with ShellCheck.")
    args = parser.parse_args()
    files = {name: (ROOT / name).read_bytes() for name in manager.BUNDLE_FILES}
    manifest = {"format": manager.FORMAT, "minimum_cli": "2.37.7", "minimum_python": "3.11",
                "sha256": {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}}
    if args.write_manifest:
        (ROOT / "bundle.json").write_text(json.dumps(manifest, indent=2) + "\n")
    files["bundle.json"] = (ROOT / "bundle.json").read_bytes()
    manager.validate_bundle(files)
    aliases = manager.parse_aliases(files["alias"])
    dispositions = json.loads((ROOT / "docs/alias-dispositions.json").read_text())
    names = [row["name"] for row in dispositions]
    if len(names) != 74 or len(set(names)) != 74 or set(names) != set(aliases) - {"ami-snapshots"}:
        raise manager.Error("Every original alias must have exactly one migration disposition.")
    if {row["name"] for row in dispositions if row["action"] not in {"Keep", "Simplify", "Fix", "Replace", "Retire"}}:
        raise manager.Error("Invalid migration disposition.")
    sso_contracts = json.loads((ROOT / "docs/profile-sso-contracts.json").read_text())
    sso_names = [row["alias"] for row in sso_contracts]
    if len(sso_names) != len(aliases) or set(sso_names) != set(aliases):
        raise manager.Error("Every current alias must have exactly one profile/SSO contract.")
    for name, value in aliases.items():
        value = value.strip()
        if value.startswith("!"):
            if " run " in value:
                target = value.split(" run ", 1)[1].split()[0]
                if target not in manager.WORKFLOWS | manager.RETIRED.keys():
                    raise manager.Error(f"Alias {name} references unknown helper {target}.")
            if args.shellcheck:
                # AWS adds the positional arguments when invoking this function.
                result = subprocess.run(["shellcheck", "--shell=sh", "-"], input=value[1:] + ' "$@"',
                                        capture_output=True, text=True, timeout=30)
                if result.returncode:
                    raise manager.Error(f"ShellCheck {name}:\n{result.stdout}{result.stderr}")
        elif args.aws_models:
            command = shlex.split(value)
            service = command[0]
            if service in {"configure", "sts"} and name in {"profiles", "mfa"}:
                continue  # Configuration commands do not implement input skeletons.
            if len(command) == 1:
                model_check(["aws", service, "help"])
            else:
                model_check(["aws", *command, "--generate-cli-skeleton", "input", "--no-sign-request", "--region", "us-east-1"])
    print(f"Validated {len(aliases)} aliases and bundle checksums.")


if __name__ == "__main__":
    try:
        main()
    except manager.Error as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(error.code)
