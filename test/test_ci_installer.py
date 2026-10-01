"""Verify CI signer checks without downloading or installing a CLI."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("ci_installer", Path(__file__).resolve().parents[1] / "scripts/install_ci_cli.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class MacSignatureTests(unittest.TestCase):
    def test_accepts_trusted_notarized_and_older_trust_statuses(self):
        chain = "Developer ID Installer: AMZN Mobile LLC (94KV3E626L)\nApple Root CA"
        current = "Status: signed by a developer certificate issued by Apple for distribution\nNotarization: trusted by the Apple notary service\n" + chain
        self.assertTrue(installer.macos_signature_verified(current))
        self.assertTrue(installer.macos_signature_verified("Status: signed by a certificate trusted by macOS\n" + chain))
        for invalid in (current.replace("94KV3E626L", "WRONGTEAM"), current.replace("Apple Root CA", "Other Root"),
                        current.replace("Notarization: trusted by the Apple notary service", "Notarization: unavailable"),
                        current.replace("Status: signed by a developer certificate issued by Apple for distribution", "Status: untrusted")):
            with self.subTest(signature=invalid):
                self.assertFalse(installer.macos_signature_verified(invalid))
