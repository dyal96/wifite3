#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# wifite3 / wifit3 — Automated Termux Bootstrap & Launcher for Android OTG
# Repository: https://github.com/dyal96/wifite3
# Upstream:   https://github.com/derv82/wifit3
# ==============================================================================

set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}"
echo "  __      __.__ _____.__  __     ________  "
echo " /  \    /  \__|/ ____\__|/  |_  \_____  \ "
echo " \   \/\/   /  \   __\|  \   __\   _(__  < "
echo "  \        /|  ||  |  |  ||  |    /       \\"
echo "   \__/\  / |__||__|  |__||__|   /______  /"
echo "        \/                              \/ "
echo "  Android Termux OTG Wireless Auditor by dyal96"
echo -e "${COLOR_RESET}"

# Verify running inside Termux
if [ -z "$PREFIX" ] || [ ! -d "/data/data/com.termux" ]; then
    echo -e "${COLOR_RED}[!] Error: This script must be executed inside Termux on Android.${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_GREEN}[+] Updating Termux package repositories...${COLOR_RESET}"
pkg update -y

echo -e "${COLOR_GREEN}[+] Installing required system dependencies (python, libusb, git, clang, uv)...${COLOR_RESET}"
pkg install -y python libusb git clang libffi

# Install uv for deterministic environment and fast virtual environments
if ! command -v uv &> /dev/null; then
    echo -e "${COLOR_GREEN}[+] Installing uv via pip...${COLOR_RESET}"
    pip install --upgrade pip
    pip install uv
fi

# Clone or update wifite3 repository
INSTALL_DIR="$HOME/wifite3"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "${COLOR_GREEN}[+] Updating existing wifite3 installation at $INSTALL_DIR...${COLOR_RESET}"
    cd "$INSTALL_DIR"
    git pull --rebase || true
else
    echo -e "${COLOR_GREEN}[+] Cloning wifite3 into $INSTALL_DIR...${COLOR_RESET}"
    git clone https://github.com/dyal96/wifite3.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${COLOR_GREEN}[+] Synchronizing project dependencies via uv...${COLOR_RESET}"
uv sync

# Create a convenient global shortcut command 'wifit3'
BIN_PATH="$PREFIX/bin/wifit3"
cat << 'EOF' > "$BIN_PATH"
#!/data/data/com.termux/files/usr/bin/bash
DIR="$HOME/wifite3"
if [ ! -d "$DIR" ]; then
    echo "[!] wifite3 directory not found at $DIR"
    exit 1
fi
cd "$DIR"

# Check USB device permissions if rooted
if command -v su &> /dev/null && [ -d "/dev/bus/usb" ]; then
    su -c "chmod -R 666 /dev/bus/usb/" 2>/dev/null || true
fi

exec uv run wifit3 "$@"
EOF
chmod +x "$BIN_PATH"

echo -e "${COLOR_CYAN}==============================================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}[✓] Installation Complete!${COLOR_RESET}"
echo -e "${COLOR_CYAN}==============================================================================${COLOR_RESET}"
echo -e "You can now plug in your USB Wi-Fi adapter via OTG cable."
echo ""
echo -e "${COLOR_YELLOW}USB Permissions Checklist:${COLOR_RESET}"
echo -e "  1. ${COLOR_GREEN}Rooted Devices:${COLOR_RESET} Permissions are handled automatically via 'su'."
echo -e "  2. ${COLOR_GREEN}Non-Rooted Devices:${COLOR_RESET} Install ${COLOR_CYAN}Termux:API${COLOR_RESET} and ${COLOR_CYAN}Termux:USB${COLOR_RESET} from F-Droid,"
echo -e "     then grant permission using: ${COLOR_CYAN}termux-usb -r /dev/bus/usb/XXX/YYY${COLOR_RESET}"
echo ""
echo -e "${COLOR_YELLOW}How to Run:${COLOR_RESET}"
echo -e "  - Full Automated Field Audit: ${COLOR_CYAN}wifit3 --auto${COLOR_RESET}"
echo -e "  - Interactive TUI:            ${COLOR_CYAN}wifit3${COLOR_RESET}"
echo -e "${COLOR_CYAN}==============================================================================${COLOR_RESET}"
