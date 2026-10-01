#!/usr/bin/env python3
"""Install an official AWS CLI in an ephemeral CI runner, verifying its signer.

Trust source: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
"""
import html
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def download(url, target):
    with urllib.request.urlopen(url, timeout=120) as response:
        target.write_bytes(response.read())


def macos_signature_verified(signature):
    status = next((line.split("Status:", 1)[1].strip().lower()
                   for line in signature.splitlines() if "Status:" in line), "")
    trusted = status.startswith("signed by a certificate trusted") or (
        status == "signed by a developer certificate issued by apple for distribution"
        and "Notarization: trusted by the Apple notary service" in signature)
    return (trusted and "Developer ID Installer: AMZN Mobile LLC (94KV3E626L)" in signature
            and "Apple Root CA" in signature)


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This installer is restricted to ephemeral GitHub Actions runners.")
    version = sys.argv[1]
    if version != "current" and not re.fullmatch(r"2\.\d+\.\d+", version):
        raise SystemExit("Expected current or an exact v2 version.")
    suffix = "" if version == "current" else "-" + version
    with tempfile.TemporaryDirectory(prefix="aws-alias-ci-cli-") as directory:
        root = Path(directory)
        if platform.system() == "Darwin":
            package = root / "AWSCLIV2.pkg"
            download(f"https://awscli.amazonaws.com/AWSCLIV2{suffix}.pkg", package)
            signature = run("pkgutil", "--check-signature", str(package))
            print(signature)
            if not macos_signature_verified(signature):
                raise SystemExit("AWS macOS installer signature verification failed.")
            print(run("sudo", "installer", "-pkg", str(package), "-target", "/"))
            binary = Path("/usr/local/bin/aws")
        else:
            architecture = "aarch64" if platform.machine() in {"arm64", "aarch64"} else "x86_64"
            url = f"https://awscli.amazonaws.com/awscli-exe-linux-{architecture}{suffix}.zip"
            package, signature, key = root / "cli.zip", root / "cli.sig", root / "key.asc"
            download(url, package)
            download(url + ".sig", signature)
            documentation = root / "installation.html"
            download("https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html", documentation)
            source = html.unescape(re.sub(r"<[^>]+>", "", documentation.read_text()))
            block = re.search(r"-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----", source, re.S)
            if not block:
                raise SystemExit("AWS signing key was absent from the official documentation.")
            key.write_text(block.group())
            gnupg = root / "gnupg"
            gnupg.mkdir(mode=0o700)
            fingerprint = "FB5DB77FD5C118B80511ADA8A6310ACC4672475C"
            metadata = run("gpg", "--homedir", str(gnupg), "--show-keys", "--with-colons", str(key))
            if not any(line.startswith("fpr:") and line.split(":")[9] == fingerprint for line in metadata.splitlines()):
                raise SystemExit("AWS signing key fingerprint changed; review the installer trust source.")
            run("gpg", "--homedir", str(gnupg), "--import", str(key))
            print(run("gpg", "--homedir", str(gnupg), "--verify", str(signature), str(package)))
            with zipfile.ZipFile(package) as archive:
                archive.extractall(root)
            for executable in (root / "aws/install", root / "aws/dist/aws", root / "aws/dist/aws_completer"):
                executable.chmod(0o755)
            install = Path(os.environ["RUNNER_TEMP"]) / ("aws-cli-" + version)
            binaries = Path(os.environ["RUNNER_TEMP"]) / ("aws-bin-" + version)
            print(run(str(root / "aws/install"), "--install-dir", str(install), "--bin-dir", str(binaries)))
            binary = binaries / "aws"
        result = run(str(binary), "--version")
        if version != "current" and f"aws-cli/{version} " not in result:
            raise SystemExit("Installed version differs from the requested baseline.")
        print(result)
        with open(os.environ["GITHUB_PATH"], "a") as path:
            path.write(str(binary.parent) + "\n")


if __name__ == "__main__":
    main()
