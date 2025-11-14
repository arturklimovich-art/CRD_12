# CRD12 Bot Integration Layer - Database-driven communication
# Взаимодействие с crd12_bot через базу данных PostgreSQL

param(
    [string]$Command,
    [string]$TaskId,
    [string]$TaskData
)

try {
    # Подключение к БД
    $connectionString = "Host=localhost;Port=5433;Username=postgres;Password=1234;Database=crd12_pgvector"
    
    # Импортируем Npgsql если доступен
    try {
        # Пытаемся найти Npgsql.dll в текущей директории или в GAC
        $npgsqlPath = Resolve-Path "Npgsql.dll" -ErrorAction SilentlyContinue
        if ($npgsqlPath) {
            Add-Type -Path $npgsqlPath.Path
        } else {
            # Если не нашли, пробуем загрузить из GAC (для .NET Framework)
            Add-Type -AssemblyName "Npgsql, Version=4.0.0.0, Culture=neutral, PublicKeyToken=5d8b90d52f46fda7" -ErrorAction SilentlyContinue
        }
        # Проверка, загрузилась ли сборка
        [void][Npgsql.NpgsqlConnection]
    } catch {
        Write-Host "⚠️ Npgsql.dll не доступен или не удалось загрузить. SQL-команды не будут выполнены." -ForegroundColor Yellow
        # В этом случае можно было бы использовать psql.exe, но для Npgsql логика ниже
    }

    switch ($Command) {
        "get-tasks" {
            Write-Host "📋 Получение списка задач из eng_it.tasks..." -ForegroundColor Cyan
            # Здесь будет код для получения задач из БД
            break
        }
        "create-task" {
            Write-Host "➕ Создание новой задачи..." -ForegroundColor Cyan
            # Здесь будет код для создания задачи в БД
            break
        }
        "update-status" {
            # Эта логика добавлена по вашему запросу.
            # Предполагается, что этот command вызывается после 'post_deploy_validated'
            # и устанавливает статус 'DONE'.
            
            Write-Host "🔄 Обновление статуса задачи $TaskId на 'DONE'..." -ForegroundColor Cyan

            # Проверяем, что TaskId был передан
            if ([string]::IsNullOrEmpty($TaskId)) {
                Write-Host "❌ Ошибка: TaskId не был предоставлен для команды update-status." -ForegroundColor Red
                break
            }
            
            # Обновляем статус задачи в DB
            # Используем параметризованный запрос для безопасности
            $updateQuery = @"
UPDATE eng_it.tasks
SET status = 'DONE', updated_at = NOW()
WHERE id = @TaskId
"@

            $connection = $null
            try {
                $connection = New-Object Npgsql.NpgsqlConnection($connectionString)
                $connection.Open()
                $command = $connection.CreateCommand()
                $command.CommandText = $updateQuery
                
                # Добавляем параметр (безопасный способ)
                # Если тип ID в БД - UUID, используйте:
                # $command.Parameters.AddWithValue("TaskId", [Guid]$TaskId) | Out-Null
                # Если тип ID - текст, используйте:
                $command.Parameters.AddWithValue("TaskId", $TaskId) | Out-Null 

                $rowsAffected = $command.ExecuteNonQuery()
                
                if ($rowsAffected -gt 0) {
                    Write-Host "✅ Task status updated to 'DONE' in eng_it.tasks for Task ID: $TaskId." -ForegroundColor Green
                } else {
                    Write-Host "⚠️ Задача с ID $TaskId не найдена или статус не был обновлен." -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host "❌ Ошибка при выполнении SQL-запроса: $_" -ForegroundColor Red
                Write-Host "SQL: $updateQuery"
            }
            finally {
                # Всегда закрываем соединение
                if ($connection -and $connection.State -ne 'Closed') {
                    $connection.Close()
                }
            }
            break
        }
        "monitor-bot" {
            Write-Host "👀 Мониторинг активности бота..." -ForegroundColor Cyan
            # Мониторинг через логи и таблицы БД
            break
        }
        default {
            Write-Host "❌ Неизвестная команда: $Command" -ForegroundColor Red
            Write-Host "Доступные команды: get-tasks, create-task, update-status, monitor-bot" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "❌ Глобальная ошибка интеграции: $_" -ForegroundColor Red
}
