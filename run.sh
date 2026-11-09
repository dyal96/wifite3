#!/usr/bin/env bash
# ==============================================================================
# wifite3 / wifit3 - Linux Quick Launcher & Environment Bootstrapper
# Repository: https://github.com/dyal96/wifite3
# Upstream:   https://github.com/dyal96/wifite3
# ==============================================================================

set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${COLOR_CYAN}"
echo "       .__  _____.__  __        ________"
echo "__  _  _|__|/ ____\__|/  |_  ____ \_____  \\"
echo "\ \/ \/ /  \   __\|  \   __\/ __ \  _(__  <"
echo " \     /|  ||  |  |  ||  | \  ___/ /       \\"
echo "  \/\_/ |__||__|  |__||__|  \___  >______  /"
echo "                                \/       \/ "
echo "Linux Standalone USB Wireless Auditor by Dyal96"
echo -e "${COLOR_RESET}"

# Function to check if a command exists
has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check for Python 3.11+
check_python() {
    if has_cmd python3; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
            return 0
        fi
    fi
    return 1
}

# 2. Package manager installation helper for system deps
install_system_deps() {
    echo -e "${COLOR_YELLOW}[!] Missing dependencies detected. Installing required packages...${COLOR_RESET}"
    if has_cmd apt-get; then
        sudo apt-get update -y
        sudo apt-get install -y python3 python3-pip python3-venv libusb-1.0-0 libusb-1.0-0-dev git curl
    elif has_cmd dnf; then
        sudo dnf install -y python3 python3-pip libusb1 libusb1-devel git curl
    elif has_cmd pacman; then
        sudo pacman -Sy --noconfirm python python-pip libusb git curl
    elif has_cmd zypper; then
        sudo zypper install -y python3 python3-pip libusb-1_0-0 libusb-1_0-devel git curl
    else
        echo -e "${COLOR_RED}[!] Unable to detect package manager. Please ensure Python 3.11+ and libusb-1.0 are installed.${COLOR_RESET}"
    fi
}

if ! check_python; then
    echo -e "${COLOR_YELLOW}[!] Python 3.11 or higher is required.${COLOR_RESET}"
    install_system_deps
fi

# 3. Ensure Astral uv is available
if ! has_cmd uv; then
    if [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    elif [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

if ! has_cmd uv; then
    echo -e "${COLOR_GREEN}[+] Installing uv (fast Python package manager)...${COLOR_RESET}"
    if has_cmd curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    elif has_cmd pip3; then
        pip3 install --user uv
        export PATH="$HOME/.local/bin:$PATH"
    else
        install_system_deps
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    fi
fi

# 4. Synchronize environment
if [ ! -d ".venv" ]; then
    echo -e "${COLOR_GREEN}[+] Initializing virtual environment and syncing dependencies via uv...${COLOR_RESET}"
    uv sync --no-dev
else
    # Quick sync check
    uv sync --no-dev --quiet
fi

# 5. Launch wifite3 / wifit3
echo -e "${COLOR_GREEN}[✓] Launching wifit3...${COLOR_RESET}"
exec uv run --no-dev wifit3 "$@"
