import psycopg2
conn = psycopg2.connect('postgresql://tradlab:crd12@localhost:5434/tradlab_db')
cur = conn.cursor()
cur.execute("SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY schemaname, tablename")
tables = cur.fetchall()
print(f'Found {len(tables)} tables:')
for schema, table in tables:
    print(f'{schema}.{table}')
conn.close()
