@echo off
setlocal enabledelayedexpansion

:: Keep window open if launched by double-clicking in Explorer
set "INTERACTIVE_MODE=0"
echo %cmdcmdline% | find /i "%~0" >nul
if not errorlevel 1 set "INTERACTIVE_MODE=1"

:: Set directory
cd /d "%~dp0"

:: Determine repository root directory
set "PROJECT_DIR=%~dp0"
if exist "%~dp0wifit3-master\pyproject.toml" (
    set "PROJECT_DIR=%~dp0wifit3-master"
)

:: Ensure user local bin is in PATH (where uv is installed)
if exist "%USERPROFILE%\.local\bin" (
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

cd /d "%PROJECT_DIR%"

:: 1. Launch via established virtual environment if available
if exist "%PROJECT_DIR%\.venv\Scripts\wifit3.exe" (
    "%PROJECT_DIR%\.venv\Scripts\wifit3.exe" %*
    goto :handle_exit
)

:: 2. Check if uv is installed, or try to install it
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [wifit3] uv package manager not found. Installing uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
    if exist "%USERPROFILE%\.local\bin" (
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    )
)

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [wifit3] Setting up environment with Python 3.11...
    uv sync --no-dev --python 3.11
    if %ERRORLEVEL% equ 0 (
        uv run --no-dev wifit3 %*
        goto :handle_exit
    )
)

:: 3. Check for standalone prebuilt executable
for %%F in (
    "%PROJECT_DIR%\wifit3.exe"
    "%PROJECT_DIR%\dist\wifit3.exe"
    "%PROJECT_DIR%\wifit3-windows-*.exe"
    "%PROJECT_DIR%\..\wifit3-windows-*.exe"
    "%PROJECT_DIR%\..\..\wifit3-windows-*.exe"
) do (
    if exist "%%~fF" (
        echo [wifit3] Launching prebuilt binary: %%~nxF
        "%%~fF" %*
        goto :handle_exit
    )
)

:: 4. Fallback to system Python if available
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHONPATH=%PROJECT_DIR%\src;%PYTHONPATH%"
    python -m wifit3 %*
    goto :handle_exit
)

echo.
echo [ERROR] Could not start wifit3.
echo Please ensure uv (https://astral.sh/uv) or Python 3.11+ is installed.
echo.
if "!INTERACTIVE_MODE!"=="1" pause
exit /b 1

:handle_exit
set "EXIT_CODE=%ERRORLEVEL%"
if "!EXIT_CODE!" neq "0" (
    echo.
    echo [wifit3 exited with code !EXIT_CODE!]
    if "!INTERACTIVE_MODE!"=="1" pause
)
exit /b !EXIT_CODE!
