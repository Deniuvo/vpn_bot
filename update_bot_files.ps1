# PowerShell скрипт для обновления bot.py и yoomoney_api.py на сервере
# Использование: .\update_bot_files.ps1 root@90.156.169.27

param(
    [Parameter(Mandatory=$false)]
    [string]$Server = "root@90.156.169.27"
)

Write-Host "📦 Обновление файлов бота на сервере $Server..." -ForegroundColor Cyan
Write-Host ""

# Проверка файлов
$files = @("bot.py", "yoomoney_api.py")
$missing = @()

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    Write-Host "❌ Файлы не найдены:" -ForegroundColor Red
    foreach ($file in $missing) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Убедитесь, что вы находитесь в папке проекта (C:\Users\1\Desktop\vpn_bot)" -ForegroundColor Yellow
    exit 1
}

# Копирование файлов
foreach ($file in $files) {
    Write-Host "📤 Копирование $file..." -ForegroundColor Yellow
    scp $file "${Server}:/root/vpn_bot/"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $file скопирован" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Ошибка копирования $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Все файлы успешно обновлены на сервере!" -ForegroundColor Green
Write-Host ""
Write-Host "🔄 Перезапустите бота на сервере:" -ForegroundColor Yellow
Write-Host "   ssh $Server" -ForegroundColor Gray
Write-Host "   cd /root/vpn_bot" -ForegroundColor Gray
Write-Host "   pkill -f 'python3 main.py'" -ForegroundColor Gray
Write-Host "   bash start_bot.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "Или выполните одну команду:" -ForegroundColor Yellow
Write-Host "   ssh $Server `"cd /root/vpn_bot && pkill -f 'python3 main.py' && bash start_bot.sh`"" -ForegroundColor Cyan

