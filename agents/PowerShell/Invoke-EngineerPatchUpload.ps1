param(
    [Parameter(Mandatory=\True)]
    [string] \,
    [Parameter(Mandatory=\True)]
    [string] \,
    [string] \ = 'E1-PATCH-MANUAL',
    [string] \ = 'http://localhost:8000/api/patches'
)

if (-not (Test-Path \)) {
    Write-Error "Файл \ не найден."
    exit 1
}

# пока API может быть не готов — фиксируем факт попытки
Write-Host "➡ Отправка патча \ от \ в задачу \ через \" -ForegroundColor Cyan

try {
    # если API уже реализован — этот блок начнет работать сразу
    \ = Invoke-RestMethod -Uri \ -Method Post -Form @{
        file   = Get-Item \
        author = \
        task_id = \
    } -ContentType "multipart/form-data"

    Write-Host "✅ Патч загружен. ID: " -ForegroundColor Green
}
catch {
    Write-Warning "API пока не отвечает или не реализован. Скрипт создан и может быть вызван агентом позже."
}
