import asyncpg
import asyncio
import json

async def test_sql():
    try:
        print("Testing SQL connection and query...")
        conn = await asyncpg.connect("postgresql://crd_user:crd12@pgvector:5432/crd12")
        
        # Тест 1: Простой SELECT
        print("Test 1: Simple SELECT")
        count = await conn.fetchval("SELECT COUNT(*) FROM core.events")
        print(f"Current events count: {count}")
        
        # Тест 2: Простой INSERT без параметров
        print("Test 2: Simple INSERT with hardcoded values")
        result = await conn.fetchval(
            "INSERT INTO core.events (source, type) VALUES ('test', 'TEST') RETURNING id"
        )
        print(f"INSERT result: {result}")
        
        # Тест 3: INSERT с параметрами
        print("Test 3: INSERT with parameters")
        result2 = await conn.fetchval(
            "INSERT INTO core.events (source, type, job_id) VALUES (, , ) RETURNING id",
            'param_test', 'PARAM_TEST', 'job_123'
        )
        print(f"INSERT with params result: {result2}")
        
        await conn.close()
        print("All tests passed!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")

asyncio.run(test_sql())
