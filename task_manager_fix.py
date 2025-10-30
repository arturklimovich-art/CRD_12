# ЭКСТРЕННЫЙ ПАТЧ ДЛЯ task_manager.py
# ЗАМЕНИТЕ текущий цикл в функции optimized_task_search на:

async def optimized_task_search(self):
    \"\"\"ОПТИМИЗИРОВАННЫЙ цикл поиска задач\"\"\"
    short_sleep = 30   # 30 секунд когда есть задачи
    long_sleep = 300   # 5 минут когда задач нет
    
    while True:
        task = await self.find_next_task()
        if task:
            await self.process_task(task)
            await asyncio.sleep(short_sleep)
        else:
            self.logger.info(\"💤 Задач нет. Перехожу в длительный сон (5 минут)...\")
            await asyncio.sleep(long_sleep)
