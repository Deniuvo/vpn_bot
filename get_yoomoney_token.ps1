# Сойка VPN — обмен OAuth-кода ЮMoney на access token
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Сойка VPN — получение токена ЮMoney" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "vpn_env\Scripts\python.exe") {
    $python = "vpn_env\Scripts\python.exe"
} else {
    $python = "python"
}

$codeFile = Join-Path $PSScriptRoot "yoomoney_code.txt"
$argsList = @()

if ($args.Count -gt 0) {
    $argsList = @($args[0])
} elseif (Test-Path $codeFile) {
    $argsList = @("--file", $codeFile)
} else {
    Write-Host "Создайте файл yoomoney_code.txt и вставьте код одной строкой." -ForegroundColor Yellow
    Write-Host "Или: .\get_yoomoney_token.ps1 ВАШ_КОД" -ForegroundColor Yellow
    "" | Out-File -FilePath $codeFile -Encoding utf8
    notepad $codeFile
    Read-Host "После сохранения кода нажмите Enter"
    if (Test-Path $codeFile) {
        $argsList = @("--file", $codeFile)
    }
}

if ($argsList.Count -gt 0) {
    & $python yoomoney_oauth.py @argsList
}

Read-Host "Нажмите Enter для выхода"
