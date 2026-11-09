"""Tests for auto-appending cracked passwords to wordlists/cracked_wordlists.txt."""
from pathlib import Path
from unittest.mock import patch

from wifit3.crack.passwords import cracked_wordlist_path
from wifit3.models import AccessPoint
from wifit3.persist.config import Config
from wifit3.persist.save import append_cracked_wordlist, save_wpa_psk, save_wps_pin


def test_append_cracked_wordlist(tmp_path: Path):
    target_file = tmp_path / "cracked_wordlists.txt"
    with patch("wifit3.crack.passwords.cracked_wordlist_path", return_value=target_file):
        append_cracked_wordlist("SecretPass123")
        assert target_file.read_text(encoding="utf-8").strip() == "SecretPass123"

        # Duplicate append does not duplicate the line
        append_cracked_wordlist("SecretPass123")
        lines = [line.strip() for line in target_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines == ["SecretPass123"]

        # New distinct password appends cleanly
        append_cracked_wordlist("AnotherPass456")
        lines = [line.strip() for line in target_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines == ["SecretPass123", "AnotherPass456"]


def test_save_wpa_psk_triggers_append(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(Config, "captures_dir", str(tmp_path / "captures"))
    target_file = tmp_path / "cracked_wordlists.txt"
    with patch("wifit3.crack.passwords.cracked_wordlist_path", return_value=target_file):
        save_wpa_psk("TestSSID", "00:11:22:33:44:55", "PasswordWPA2")
        assert target_file.exists()
        assert "PasswordWPA2" in target_file.read_text(encoding="utf-8")


def test_save_wps_pin_triggers_append(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(Config, "captures_dir", str(tmp_path / "captures"))
    target_file = tmp_path / "cracked_wordlists.txt"
    ap = AccessPoint(bssid="00:11:22:33:44:55", ssid="TestWPS", channel=6)
    with patch("wifit3.crack.passwords.cracked_wordlist_path", return_value=target_file):
        save_wps_pin(ap, "12345670", "PasswordFromWPS")
        assert target_file.exists()
        assert "PasswordFromWPS" in target_file.read_text(encoding="utf-8")
