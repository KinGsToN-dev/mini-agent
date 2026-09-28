# ============================================================
# start_tradingview.ps1
# Launch TradingView Desktop (MSIX/Store) with CDP on port 9222.
# Pure ASCII - works with PowerShell 5.1 without BOM.
# ============================================================

$ErrorActionPreference = "Stop"

# --- COM class to launch Store apps ---
if (-not ("AppActivation" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class AppActivation {
    [ComImport]
    [Guid("2E941141-7F97-4756-BA1D-9DECDE894A3D")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IApplicationActivationManager {
        int ActivateApplication(
            [MarshalAs(UnmanagedType.LPWStr)] string appUserModelId,
            [MarshalAs(UnmanagedType.LPWStr)] string arguments,
            uint options,
            out uint processId
        );
    }

    [ComImport]
    [Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")]
    class ApplicationActivationManager {}

    public static uint Launch(string aumid, string args) {
        var manager = (IApplicationActivationManager)new ApplicationActivationManager();
        uint pid;
        int hr = manager.ActivateApplication(aumid, args, 0, out pid);
        if (hr != 0)
            Marshal.ThrowExceptionForHR(hr);
        return pid;
    }
}
"@
}

$aumid = "TradingView.Desktop_n534cwy3pjxzj!TradingView.Desktop"
$args = "--remote-debugging-port=9222 --remote-allow-origins=*"

Write-Host "[..] Launching TradingView with CDP on port 9222..." -ForegroundColor Cyan

$processId = [AppActivation]::Launch($aumid, $args)
Write-Host "[OK] TradingView launched. PID: $processId" -ForegroundColor Green

# --- Wait for CDP to be ready ---
Write-Host "[..] Waiting for CDP on port 9222..." -ForegroundColor Cyan

$maxWait = 30
$waited = 0
$ready = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++

    try {
        $r = Invoke-RestMethod "http://127.0.0.1:9222/json/version" -TimeoutSec 2 -ErrorAction Stop
        $ready = $true
        Write-Host "[OK] CDP ready. Browser: $($r.Browser)" -ForegroundColor Green
        break
    } catch {
        # not ready yet
    }

    if ($waited % 5 -eq 0) {
        Write-Host "  ... $waited sec" -ForegroundColor DarkGray
    }
}

if ($ready) {
    Write-Host ""
    Write-Host "Check:" -ForegroundColor Cyan
    Write-Host "  http://127.0.0.1:9222/json/version"
    Write-Host "  http://127.0.0.1:9222/json           (list of tabs)"
    Write-Host ""
    Write-Host "Now you can run _tv_test.py or tradingview-mcp." -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] CDP not ready in $maxWait sec" -ForegroundColor Red
    Write-Host "Check TradingView window - maybe startup error." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"