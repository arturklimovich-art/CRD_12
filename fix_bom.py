# fix_bom.py
with open('/app/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("BOM removed")
