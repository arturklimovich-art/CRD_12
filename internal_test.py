import asyncio
from app import app
from fastapi.testclient import TestClient

def test_jobs_api_internally():
    with TestClient(app) as client:
        print('Внутренний тест FastAPI:')
        
        # Тест health
        response = client.get('/health')
        print(f'  /health: {response.status_code}')
        
        # Тест jobs endpoints
        endpoints = [
            ('/api/v1/jobs/test', 'GET'),
            ('/api/v1/jobs/list', 'GET'),
            ('/api/v1/jobs/create', 'POST')
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == 'POST' and endpoint == '/api/v1/jobs/create':
                    response = client.post(endpoint, json={'source': 'internal_test', 'task_type': 'test'})
                else:
                    response = client.get(endpoint)
                print(f'  {endpoint}: {response.status_code}')
                if response.status_code == 200:
                    print(f'    Success: {response.json()}')
            except Exception as e:
                print(f'  {endpoint}: ERROR - {e}')

if __name__ == '__main__':
    test_jobs_api_internally()
