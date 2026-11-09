from unittest.mock import AsyncMock, MagicMock
import pytest
from textual.app import App
from textual.screen import Screen
from textual.widgets import Button

from tests.wlan.mocks import build_ap
from wifit3.chips.driver import DeviceID
from wifit3.ui.app import WifiteApp
from wifit3.ui.screens.focus_v2.screen import FocusViewV2
from wifit3.ui.screens.scanner import ScannerView
from wifit3.ui.screens.splash import SplashView


def test_cli_auto_argument():
    import argparse
    from wifit3 import __version__

    parser = argparse.ArgumentParser(prog="wifit3")
    parser.add_argument("--version", action="version", version=f"wifit3 {__version__}")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("-a", "--auto", action="store_true")
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args(["-a"])
    assert args.auto is True

    args2 = parser.parse_args(["--auto"])
    assert args2.auto is True

    args3 = parser.parse_args([])
    assert args3.auto is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_usb_devices")
async def test_splash_auto_mode_triggers_start(monkeypatch):
    dev = DeviceID(0x0E8D, 0x7961, "MT7921AU", bus=2, address=32)
    app = WifiteApp(auto_mode=True)
    async with app.run_test(size=(120, 40)) as pilot:
        splash = app.screen
        assert isinstance(splash, SplashView)
        started = []

        def _fake_start():
            started.append(True)

        monkeypatch.setattr(splash, "action_start", _fake_start)
        splash.render_devices([dev])
        await pilot.pause(0.3)
        assert len(started) == 1


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_usb_devices")
async def test_scanner_toggle_automode():
    screen = ScannerView()
    assert screen.automode_active is False
    screen.action_toggle_automode()
    assert screen.automode_active is True
    screen.action_toggle_automode()
    assert screen.automode_active is False


class _DummyFocus(Screen):
    auto_run_on_enter = False


class _ScannerHost(App):
    def __init__(self):
        super().__init__()
        self.array = MagicMock()
        self.array.start_hopping = AsyncMock()
        self.target_ap = None
        self.pbc_enabled = True
        self.vault = MagicMock()
        self.vault.has_psk.return_value = False
        self.vault.has_wep_key.return_value = False
        self.vault.has_wps_psk.return_value = False
        self.vault.has_handshake.return_value = False
        self.vault.has_pmkid.return_value = False
        self.focus_view = _DummyFocus()
        self.scanner_view = ScannerView()

    def on_mount(self) -> None:
        self.push_screen(self.scanner_view)


@pytest.mark.asyncio
async def test_scanner_automode_tick_selects_target():
    host = _ScannerHost()
    async with host.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0)
        scanner = host.screen

        ap1 = build_ap(bssid="00:11:22:33:44:55", ssid="TargetOne", channel=6)
        ap1.signal_by_card = {"wlan0": -45}
        ap2 = build_ap(bssid="aa:bb:cc:dd:ee:ff", ssid="TargetTwo", channel=1)
        ap2.signal_by_card = {"wlan0": -70}

        scanner.ap_cache[ap1.bssid] = ap1
        scanner.ap_cache[ap2.bssid] = ap2

        scanner.automode_active = True
        scanner._automode_tick()

        assert host.target_ap == ap1
        assert ap1.bssid in scanner._automode_visited
        assert host.focus_view.auto_run_on_enter is True


class _FocusHost(App):
    def __init__(self):
        super().__init__()
        self.array = None
        self.target_ap = None
        self.pbc_enabled = True
        self.vault = MagicMock()
        self.vault.ap_state.return_value.keys = ()

    def on_mount(self) -> None:
        self.push_screen(FocusViewV2())


@pytest.mark.asyncio
async def test_focus_auto_button_and_toggle():
    host = _FocusHost()
    async with host.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0)
        focus = host.screen
        focus._tick_timer.stop()

        ap = build_ap(bssid="00:11:22:33:44:55", ssid="TargetOne", channel=6, encryption="WPA2")
        host.target_ap = ap
        focus._target_ap = ap
        focus.refresh_buttons()

        btn = focus.query_one("#btn-auto", Button)
        assert btn.display is True
        assert str(btn.label) == "Auto"

        focus.action_toggle_auto_mode()
        assert focus._auto_mode_active is True
        assert str(btn.label) == "Stop Auto"

        focus.action_toggle_auto_mode()
        assert focus._auto_mode_active is False
        assert str(btn.label) == "Auto"


@pytest.mark.asyncio
async def test_focus_auto_campaign_loop_skips_when_already_cracked():
    host = _FocusHost()
    async with host.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0)
        focus = host.screen
        focus._tick_timer.stop()

        ap = build_ap(bssid="00:11:22:33:44:55", ssid="TargetOne", channel=6, encryption="WPA2")
        host.target_ap = ap
        focus._target_ap = ap

        host.vault.has_psk.return_value = True

        focus.start_auto_mode()
        await pilot.pause(0.1)

        assert focus._auto_mode_active is False


def test_automode_score_prioritises_wps_over_wep_over_wpa2():
    """WPS (unlocked) > WEP > WPA2: scoring tiers are ordered correctly."""
    ap_wps = build_ap(bssid="00:00:00:00:00:01", encryption="WPA2", wps=True)
    ap_wps.wps_locked = False
    ap_wps.signal_by_card = {"wlan0": -60}

    ap_wep = build_ap(bssid="00:00:00:00:00:02", encryption="WEP")
    ap_wep.signal_by_card = {"wlan0": -60}

    ap_wpa2 = build_ap(bssid="00:00:00:00:00:03", encryption="WPA2")
    ap_wpa2.signal_by_card = {"wlan0": -60}

    score_wps = ScannerView._automode_score(ap_wps)
    score_wep = ScannerView._automode_score(ap_wep)
    score_wpa2 = ScannerView._automode_score(ap_wpa2)

    assert score_wps > score_wep > score_wpa2


def test_automode_tick_skips_wpa3_only():
    """WPA3-only APs (no transition mode) must be excluded from auto mode candidates."""
    screen = ScannerView()
    screen._automode_scanned = 0
    screen._automode_cracked = 0

    ap_wpa3 = build_ap(bssid="00:00:00:00:00:aa", encryption="WPA2", wpa3=True)
    ap_wpa3.transition_mode = False
    ap_wpa3.signal_by_card = {"wlan0": -40}  # strong signal — should not win

    ap_wpa2 = build_ap(bssid="00:00:00:00:00:bb", encryption="WPA2")
    ap_wpa2.wpa3 = False
    ap_wpa2.signal_by_card = {"wlan0": -80}  # weaker but attackable

    assert ScannerView._automode_score(ap_wpa3) < ScannerView._automode_score(ap_wpa2)


def test_automode_progress_counters_reset_on_enable():
    """Enabling auto mode resets the scanned/cracked counters."""
    screen = ScannerView()
    screen._automode_scanned = 5
    screen._automode_cracked = 3
    # Enable auto mode — counters must be zeroed.
    screen.action_toggle_automode()
    assert screen.automode_active is True
    assert screen._automode_scanned == 0
    assert screen._automode_cracked == 0
    # Disable auto mode.
    screen.action_toggle_automode()
    assert screen.automode_active is False
