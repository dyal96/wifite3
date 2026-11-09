# wifite3 on Android (Termux OTG Guide)

> A practical guide to running `wifite3` on Android devices via USB OTG using Termux.  
> Turn your Android phone into a pocket wireless auditing station without needing a laptop.

---

## ⚡ Quick Start (One-Line Setup)

Open **Termux** on your Android device and paste:

```bash
pkg update -y && pkg install -y curl && curl -sSL https://raw.githubusercontent.com/dyal96/wifite3/master/termux-setup.sh | bash
```

Once installed, simply run:
```bash
wifit3 --auto
```

---

## 📱 Why This Works

Unlike traditional wireless tools (`aircrack-ng`, `wifite2`, `kismet`, `bettercap`) which require:
- A custom Android kernel with monitor-mode patches (`bcmon`, `nethunter` kernels)
- Root access to modify system network interfaces (`wlan0`)
- Operating system driver bindings

**`wifite3` works completely differently:**
1. **Userland Drivers:** It contains pure-Python reimplementations of Linux Wi-Fi drivers (`src/wifit3/chips/`).
2. **Direct USB Access:** It speaks raw 802.11 Control and Bulk USB transfers directly to the adapter via **PyUSB** and **libusb**.
3. **No Kernel Drivers Needed:** Android's native Wi-Fi stack is completely bypassed. Your phone's internal Wi-Fi is untouched.

---

## 🛠️ Prerequisites

### 1. Install Termux from F-Droid
> [!WARNING]
> **Do NOT install Termux from the Google Play Store** (that version is deprecated and unmaintained).

Install the latest versions from **F-Droid**:
- [**Termux on F-Droid**](https://f-droid.org/en/packages/com.termux/)
- [**Termux:API on F-Droid**](https://f-droid.org/en/packages/com.termux.api/) (Optional, recommended for non-root USB access)
- [**Termux:USB on F-Droid**](https://f-droid.org/en/packages/com.termux.usb/) (Optional, for USB Host API forwarding)

### 2. USB OTG Cable or Adapter
- USB-C to USB-A (or Micro-USB to USB-A) adapter supporting USB OTG (On-The-Go).

### 3. Supported USB Wi-Fi Dongle
Android USB OTG ports typically deliver **500mA** of power. Use compact, low-power nano adapters:

| Adapter | Chipset | Band | Current Draw | Android OTG Notes |
|---|---|---|---|---|
| **Generic Nano Dongle** | MT7601U | 2.4 GHz | ~100mA | **Recommended #1** -- lowest power draw, small form factor |
| **TP-Link TL-WN722N v2/v3** | RTL8188EUS | 2.4 GHz | ~120mA | **Recommended #2** -- reliable, compact, plug-and-play |
| **Panda PAU05** | RT5370 | 2.4 GHz | ~150mA | Excellent compatibility |
| **TP-Link TL-WN722N v1** | AR9271 | 2.4 GHz | ~250mA | Proven packet injection |
| **ALFA AWUS036ACHM** | MT7610U | 2.4 / 5 GHz | ~350mA | Dual-band capability |

> [!CAUTION]
> **Avoid high-power adapters** (like ALFA AWUS1900 or AWUS036ACH with RTL8814AU/RTL8812AU) on direct OTG. They draw 800mA+ and can cause your phone's battery protection to trip. If using high-power cards, use an externally-powered OTG hub.

---

## 🚀 Step-by-Step Manual Setup

If you prefer not using the automated script:

### Step 1: Install Termux Packages
```bash
pkg update -y
pkg install -y python libusb git clang libffi
pip install --upgrade pip
pip install uv
```

### Step 2: Clone Repository & Sync
```bash
git clone https://github.com/dyal96/wifite3.git ~/wifite3
cd ~/wifite3
uv sync
```

---

## 🔑 USB Permissions Configuration

Android's security model restricts direct access to `/dev/bus/usb/`. Depending on whether your device is rooted or non-rooted, follow the corresponding section:

### Option A: Rooted Android (Simplest & Best Experience)
If your phone is rooted (Magisk, KernelSU, or APatch):
1. Plug your USB Wi-Fi adapter into your phone via OTG.
2. In Termux, grant permissions to the USB bus:
   ```bash
   su -c "chmod -R 666 /dev/bus/usb/"
   ```
   *(Note: The `termux-setup.sh` script does this automatically if `su` is present).*
3. Run wifite3:
   ```bash
   wifit3 --auto
   ```

### Option B: Non-Rooted Android (Termux:USB)
1. Install **Termux:USB** and **Termux:API** from F-Droid.
2. Plug in your USB Wi-Fi adapter.
3. List available USB devices:
   ```bash
   termux-usb -l
   ```
   Output will show something like `["/dev/bus/usb/001/002"]`.
4. Request Android USB permission:
   ```bash
   termux-usb -r /dev/bus/usb/001/002
   ```
   A system popup will appear asking: *"Open Termux:USB to handle this device?"* Tap **Allow**.

---

## 🎯 Operating Modes on Mobile

### 1. Automated Field Auditing (`--auto` / `-a`)
Ideal for pocket operation or when using touch screens without a full keyboard:
```bash
wifit3 --auto
```
- Automatically detects the adapter and clicks `START`.
- Cycles visible APs prioritizing high-probability targets (WPS > WEP > WPA2).
- Automatically steps through attack campaigns and saves handshakes/passwords into `captures/`.
- Emits summary toasts and logs.

### 2. Interactive TUI Mode
```bash
wifit3
```
- **Terminal Sizing Tip:** For best layout, rotate your phone to **landscape** orientation, or pinch-to-zoom out in Termux to fit 100+ columns.
- **Controls:**
  - `A`: Toggle Auto Mode
  - `N`: Next target (skip current target and advance to next AP)
  - `Q`: Quit
  - `C`: Channel filter
  - `V`: Open Vault (cracked passwords and captured handshakes)
  - `ESC`: Go back from Focus view to Scanner

---

## 📝 Wordlists & Custom Wordlist Generation

- **Auto-Learned Passwords**: Any password cracked during attacks is automatically appended to `wordlists/cracked_wordlists.txt` and prioritized in future guess lists.
- **Custom Wordlists**: If you need to generate tailored wordlists based on specific keywords, names, or patterns, use [**dyal96/Custom-Wordlist-Generator**](https://github.com/dyal96/Custom-Wordlist-Generator).

---

## ⚡ Performance Optimization for ARM / Mobile

1. **PixieDust Sweeps:**
   - On desktop x86, glibc RTL819x and eCos PRNG sweeps take 10-30 seconds. On mobile ARM processors, they may take 1-2 minutes.
   - For fast scanning, stick to default mode or keep `--auto` active to transition across targets cleanly.
2. **Offline Cracking on Phone:**
   - Password dictionary attacks (WPA hashcat / CPU crack) generate heat and drain battery quickly on mobile devices.
   - Export your captured `.hc22000` and `.pcap` files from the `captures/` folder to a desktop PC or cloud GPU rig for cracking.

---

## ❓ Troubleshooting

### "No backend available" / PyUSB cannot find libusb
Run:
```bash
export LD_LIBRARY_PATH="$PREFIX/lib:$LD_LIBRARY_PATH"
```
Ensure `libusb` is installed: `pkg install -y libusb`.

### Adapter not detected on Splash screen
1. Make sure your phone has **USB OTG enabled** (some phones like OnePlus/Oppo have an "OTG Connection" switch in Android Settings that turns off automatically after 10 minutes).
2. Check if the adapter powers up (LED flashes).
3. If rooted, re-run `su -c "chmod -R 666 /dev/bus/usb/"`.

### Textual UI layout looks crushed or cut off
1. Pinch-to-zoom out in Termux to reduce font size.
2. Rotate device to landscape orientation.
3. Termux settings: Long-press anywhere on terminal screen -> More -> Change font size -> Select smaller font.
