# СКРИПТ ПЕРЕНОСА BOT V2
# Автоматический перенос модуля в целевую структуру

Write-Host "=== ПЕРЕНОС BOT V2 ===" -ForegroundColor Green

# Параметры
$SourcePath = "C:\Users\Artur\EngineersIT.Bot"
$TargetPath = "CRD12\agents\EngineersIT.Bot"

# Проверка существования целевого пути
if (Test-Path $TargetPath) {
    Write-Host "⚠️  Целевой путь уже существует: $TargetPath" -ForegroundColor Yellow
    $backupPath = "$TargetPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "Создание бэкапа: $backupPath" -ForegroundColor Gray
    Move-Item $TargetPath $backupPath -Force
}

# Создание целевой директории
Write-Host "Создание целевой директории..." -ForegroundColor Gray
$null = New-Item -ItemType Directory -Path $TargetPath -Force

# Копирование файлов
Write-Host "Копирование файлов модуля..." -ForegroundColor Gray
Copy-Item "$SourcePath\*" $TargetPath -Recurse -Force

# Проверка копирования
$sourceFiles = Get-ChildItem $SourcePath -Recurse -File
$targetFiles = Get-ChildItem $TargetPath -Recurse -File

if ($sourceFiles.Count -eq $targetFiles.Count) {
    Write-Host "✅ Все $($sourceFiles.Count) файлов скопированы успешно" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка копирования: $($sourceFiles.Count) -> $($targetFiles.Count)" -ForegroundColor Red
    exit 1
}

# Обновление путей в .psm1 файле (если необходимо)
Write-Host "Обновление путей в модуле..." -ForegroundColor Gray
$psm1Path = "$TargetPath\EngineersIT.Bot.psm1"
if (Test-Path $psm1Path) {
    $content = Get-Content $psm1Path -Raw
    # Заменяем абсолютные пути на относительные
    $newContent = $content -replace "C:\\\\Users\\\\Artur\\\\EngineersIT\\.Bot", "."
    if ($content -ne $newContent) {
        $newContent | Out-File $psm1Path -Encoding UTF8
        Write-Host "✅ Пути в .psm1 обновлены" -ForegroundColor Green
    }
}

# Тестирование модуля в новом расположении
Write-Host "
Тестирование модуля в новом расположении..." -ForegroundColor Cyan
try {
    Import-Module $TargetPath -Force -ErrorAction Stop
    $functions = Get-Command -Module EngineersIT.Bot
    Write-Host "✅ Модуль загружен успешно: $($functions.Count) функций" -ForegroundColor Green
    
    # Базовый тест
    $testResult = Get-BotModuleInfo
    Write-Host "✅ Базовый тест пройден: $($testResult.ModuleName)" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Ошибка загрузки модуля: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "
🎉 ПЕРЕНОС УСПЕШНО ЗАВЕРШЕН! 🎉" -ForegroundColor Green -BackgroundColor DarkBlue
Write-Host "Модуль Bot v2 перемещен в: $TargetPath" -ForegroundColor White
Write-Host " "

Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Обновить PSModulePath если необходимо" -ForegroundColor White
Write-Host "2. Настроить интеграцию с job_queue/events" -ForegroundColor White
Write-Host "3. Заменить REST заглушки на реальные вызовы" -ForegroundColor White
Write-Host "4. Провести полное e2e тестирование" -ForegroundColor White
