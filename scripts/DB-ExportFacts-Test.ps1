param(
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    [string]$TableName = "core.events"
)

Write-Host "=== ТЕСТОВЫЙ ЭКСПОРТ ===" -ForegroundColor Cyan
Write-Host "Таблица: $TableName"
Write-Host "Выходной файл: $OutputPath"

# Создаем тестовые данные
$testData = @"
event_id,event_type,created_at,description
1,user_login,2024-01-01 10:00:00,User logged in
2,data_export,2024-01-01 11:00:00,Data exported to CSV
3,system_check,2024-01-01 12:00:00,System health check completed
4,backup_start,2024-01-01 13:00:00,Database backup started
5,backup_end,2024-01-01 14:00:00,Database backup completed
"@

# Создаем директорию если не существует
$dir = Split-Path $OutputPath -Parent
if (!(Test-Path $dir)) { 
    New-Item -ItemType Directory -Path $dir -Force 
    Write-Host "Создана директория: $dir" -ForegroundColor Green
}

# Записываем тестовые данные
$testData | Out-File -FilePath $OutputPath -Encoding UTF8

if (Test-Path $OutputPath) {
    $size = (Get-Item $OutputPath).Length
    $lines = (Get-Content $OutputPath).Count
    Write-Host "✅ Тестовый файл создан успешно!" -ForegroundColor Green
    Write-Host "📊 Размер: $size байт" -ForegroundColor Yellow
    Write-Host "📈 Строк: $lines" -ForegroundColor Yellow
    Write-Host "📍 Путь: $OutputPath" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ Ошибка создания файла" -ForegroundColor Red
    exit 1
}
