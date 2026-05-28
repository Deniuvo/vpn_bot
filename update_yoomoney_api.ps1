# PowerShell скрипт для обновления yoomoney_api.py на сервере
# Использование: .\update_yoomoney_api.ps1 root@90.156.169.27

param(
    [Parameter(Mandatory=$true)]
    [string]$Server
)

Write-Host "📦 Копирование yoomoney_api.py на сервер $Server..." -ForegroundColor Cyan

if (-not (Test-Path "yoomoney_api.py")) {
    Write-Host "❌ Файл yoomoney_api.py не найден в текущей директории!" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Копирование файла..." -ForegroundColor Yellow
scp yoomoney_api.py "${Server}:/root/vpn_bot/"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ yoomoney_api.py успешно обновлен на сервере!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔄 Перезапустите бота на сервере:" -ForegroundColor Yellow
    Write-Host "   ssh $Server" -ForegroundColor Gray
    Write-Host "   cd /root/vpn_bot" -ForegroundColor Gray
    Write-Host "   pkill -f 'python3 main.py'" -ForegroundColor Gray
    Write-Host "   bash start_bot.sh" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Ошибка копирования файла!" -ForegroundColor Red
    Write-Host "Проверьте подключение к серверу" -ForegroundColor Yellow
}

