"""The USB backend interface: one libusb context."""
import os
from types import SimpleNamespace

import pytest
import usb.core

from tests.device.fakes import FakeBackend
from wifit3.device import backend


def test_libusb_backend_enumerates(monkeypatch):
    seen = {}
    dev = object()

    def find(**kw):
        seen.update(kw)
        return [dev]

    monkeypatch.setattr(usb.core, "find", find)
    ctx = object()
    assert backend.LibusbBackend(ctx).enumerate() == [dev]
    assert seen == {"find_all": True, "backend": ctx}


def test_libusb_backend_find_targets_instance(monkeypatch):
    seen = {}
    dev = object()

    def find(**kw):
        seen.update(kw)
        return dev

    monkeypatch.setattr(usb.core, "find", find)
    ctx = object()
    assert backend.LibusbBackend(ctx).find(0x1111, 0x2222, bus=2, address=7) is dev
    assert seen == {"idVendor": 0x1111, "idProduct": 0x2222, "backend": ctx, "bus": 2, "address": 7}


def test_libusb_backend_find_without_instance(monkeypatch):
    seen = {}

    def find(**kw):
        seen.update(kw)
        return None

    monkeypatch.setattr(usb.core, "find", find)
    backend.LibusbBackend(object()).find(1, 2)
    assert "bus" not in seen and "address" not in seen


def test_libusb_backend_find_all(monkeypatch):
    devs = [object()]
    monkeypatch.setattr(usb.core, "find", lambda **kw: devs)
    assert backend.LibusbBackend(object()).find_all(1, 2) == devs


def test_libusb_backend_node_path():
    dev = type("D", (), {"bus": 2, "address": 35})()
    assert backend.LibusbBackend(None).node_path(dev) == "/dev/bus/usb/002/035"


def test_usb_backend_returns_a_libusb_backend(monkeypatch):
    low = object()
    monkeypatch.setattr(backend, "_desktop_libusb", lambda: low)
    assert isinstance(backend.usb_backend(), backend.LibusbBackend)


def test_usb_backend_missing_libusb(monkeypatch):
    monkeypatch.setattr(backend, "_desktop_libusb", lambda: None)
    with pytest.raises(usb.core.NoBackendError):
        backend.usb_backend()


@pytest.fixture(autouse=True)
def _reset_backend_factory():
    yield
    backend.set_usb_backend_factory(None)


def test_usb_backend_factory_override():
    fake = FakeBackend()
    backend.set_usb_backend_factory(lambda: fake)
    assert backend.usb_backend() is fake


def test_desktop_libusb_prefers_the_bundle(monkeypatch):
    bundled = object()
    monkeypatch.setattr(backend, "libusb_package",
                        SimpleNamespace(get_libusb1_backend=lambda: bundled))
    monkeypatch.setattr("usb.backend.libusb1.get_backend",
                        lambda: pytest.fail("system backend used"))
    assert backend._desktop_libusb() is bundled


def test_desktop_libusb_falls_back_to_system(monkeypatch):
    system = object()
    monkeypatch.setattr(backend, "libusb_package",
                        SimpleNamespace(get_libusb1_backend=lambda: None))
    monkeypatch.setattr("usb.backend.libusb1.get_backend", lambda: system)
    assert backend._desktop_libusb() is system


def test_termux_fallback_prepends_ld_library_path(monkeypatch, tmp_path):
    """When the .so exists under $PREFIX/lib and LD_LIBRARY_PATH is unset,
    the Termux fallback must inject the directory before loading."""
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "libusb-1.0.so").write_bytes(b"")   # just needs to exist

    monkeypatch.setattr(backend, "libusb_package", None)
    monkeypatch.setenv("PREFIX", str(tmp_path))
    monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)

    captured = {}
    call_count = [0]

    def fake_get_backend(find_library=None):
        call_count[0] += 1
        if find_library is not None:
            captured["find_library_result"] = find_library("usb-1.0")
            return object()  # "loaded" backend
        return None  # first call: system lookup fails

    monkeypatch.setattr("usb.backend.libusb1.get_backend", fake_get_backend)
    result = backend._desktop_libusb()

    assert result is not None
    assert captured["find_library_result"] == str(lib_dir / "libusb-1.0.so")
    assert str(lib_dir) in os.environ.get("LD_LIBRARY_PATH", "")
