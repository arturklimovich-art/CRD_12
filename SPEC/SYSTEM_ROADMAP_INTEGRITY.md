# 🧭 Спецификация: Roadmap как Источник Истины

**Версия**: 1.0  
**Дата**: 11 ноября 2025  
**Автор**: System Integrity Module  
**Цель**: Описать архитектуру, правила и процедуры работы с Roadmap в БД для обеспечения целостности системы.

---

## 🔷 E1-B15: State_Persistence_System

Этот компонент обеспечивает сохранение состояния между рестартами контейнера engineer_b_api через Docker-тома.

### Volume Paths Configured:
  - /app/workspace/patches → ./docker_volumes/engineer_b_api/patches
  - /app/workspace/reports → ./docker_volumes/engineer_b_api/reports
  - /app/workspace/snapshots → ./docker_volumes/engineer_b_api/snapshots
  - /app/workspace/ADR → ./docker_volumes/engineer_b_api/adr
  - /app/workspace/logs → ./docker_volumes/engineer_b_api/logs
  - /app/workspace/patches_applied → ./docker_volumes/engineer_b_api/patches_applied

> ✅ Все пути сохраняют данные на хосте и выживают при пересоздании контейнера.

---

🎯 **Источник истины = Roadmap = Состояние системы.**  
Любое отклонение — ошибка архитектуры.
