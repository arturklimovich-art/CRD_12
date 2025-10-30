# fix_regex_error.py
import re

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем проблемное регулярное выражение
old_regex = r'_FILEPATH_RE = re.compile(r"(?:Modify|Patch|Edit|Fix|???????????|??????|?????|??????)\s+([\w\./\-_]+\.py)", re.IGNORECASE)'
new_regex = r'_FILEPATH_RE = re.compile(r"(?:Modify|Patch|Edit|Fix)\s+([\w\./\-_]+\.py)", re.IGNORECASE)'

if old_regex in content:
    content = content.replace(old_regex, new_regex)
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed regex error - removed Russian characters")
else:
    print("ERROR: Regex pattern not found")
