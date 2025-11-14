# Техническое задание: E1-B16-IMPL-PATCHSERVICE Рефакторинг app.py: выделение PatchService для централизации логики применения патчей

**Дата создания:** 2025-11-13 18:05:19 UTC  
**Автор:** arturklimovich-art  
**Статус:** in_progress  
**Блок:** E1-B16 (Patch Manager Integration)

---

## 1. ЦЕЛЬ ЗАДАЧИ

Выделить логику применения патчей из app.py в отдельный сервис PatchService для устранения дублирования и улучшения архитектуры. Удалить дублирующую функцию _apply_code_changes, использовать единый механизм через PatchManager.

---

## 2. ТРЕБОВАНИЯ

### 2.1 Функциональные требования
- [ ] Создать модуль services/patch_service.py
- [ ] Реализовать класс PatchService с методом apply_patch()
- [ ] Интегрировать PatchService в app.py
- [ ] Удалить дублирующую функцию _apply_code_changes из app.py
- [ ] Обеспечить совместимость с существующим интерфейсом

### 2.2 Нефункциональные требования
- Производительность: без ухудшения производительности
- Безопасность: сохранить все проверки и валидации
- Кодировка: UTF-8
- Совместимость: Docker, PostgreSQL 16, Python 3.11

---

## 3. ТЕХНИЧЕСКИЕ ДЕТАЛИ

### 3.1 Затрагиваемые файлы
- \src/engineer_b_api/app.py\
- \src/engineer_b_api/services/patch_service.py\ (новый файл)
- \src/engineer_b_api/patch_manager.py\ (для интеграции)

### 3.2 API Endpoints
- \POST /agent/analyze\ - будет использовать PatchService вместо прямого вызова _apply_code_changes

---

## 4. DEFINITION OF DONE (DoD)

- [ ] PatchService создан и функционирует
- [ ] app.py обновлен для использования PatchService
- [ ] Функция _apply_code_changes удалена из app.py
- [ ] Тесты пройдены (smoke tests)
- [ ] Документация обновлена
- [ ] Код задеплоен в production

---

## 5. РИСКИ И ЗАВИСИМОСТИ

- **Риски:** Возможные проблемы с кодировкой UTF-8 при работе с патчами
- **Зависимости:** PatchManager должен быть доступен

---

## 6. ССЫЛКИ

- Roadmap: http://localhost:8001/roadmap
- Task Code: E1-B16-IMPL-PATCHSERVICE