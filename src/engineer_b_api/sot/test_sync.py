import sys
sys.path.insert(0, '/app/src/engineer_b_api')

from pathlib import Path
from sot.yaml_sync import YAMLSyncEngine

# Подключение к БД
db_dsn = 'postgresql://crd_user:crd12@crd12_pgvector:5432/crd12'
repo_root = Path('/app')

engine = YAMLSyncEngine(db_dsn, repo_root)

# Синхронизация Core-каталога
print('Синхронизация Core-каталога доменов...')
result = engine.sync_core_catalog()

print('Результат:')
print('  Status:', result['status'])
print('  Domains synced:', result.get('domains_synced', 0))
print('  Changes:', len(result.get('changes', [])))
for change in result.get('changes', []):
    print('    -', change)

if 'error' in result:
    print('  Error:', result['error'])
else:
    print('  Success')

engine.close()
