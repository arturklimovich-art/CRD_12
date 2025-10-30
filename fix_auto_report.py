# fix_auto_report.py
with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем _AUTO_REPORT
old_auto_report = '_AUTO_REPORT = re.compile(r"===\s*?????????? ?????\s*===.*?```json\s*(\\{[\\s\\S]*?\\})\s*```", re.IGNORECASE | re.DOTALL)'
new_auto_report = '_AUTO_REPORT = re.compile(r"===\s*Analysis Report\s*===.*?```json\s*(\\{[\\s\\S]*?\\})\s*```", re.IGNORECASE | re.DOTALL)'

if old_auto_report in content:
    content = content.replace(old_auto_report, new_auto_report)
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed _AUTO_REPORT regex")
else:
    print("ERROR: _AUTO_REPORT pattern not found")
    
    # Альтернативный поиск
    import re
    auto_report_pattern = r'_AUTO_REPORT = re\.compile\(r"[^"]*?????????? ?????[^"]*", re\.IGNORECASE \| re\.DOTALL\)'
    if re.search(auto_report_pattern, content):
        print("Found _AUTO_REPORT with Russian chars using regex")
