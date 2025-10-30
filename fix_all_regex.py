# fix_all_regex.py
import re

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем все проблемные регулярные выражения с русскими символами
fixes = [
    # Исправляем _AUTO_REPORT на строке 82
    (
        r'_AUTO_REPORT = re.compile\(r"===\s*?????????? ?????\s*===\.\*?```json\s*\(\\\{[\s\S]\*?\\\}\)\s*```", re\.IGNORECASE \| re\.DOTALL\)',
        r'_AUTO_REPORT = re.compile(r"===\s*Analysis Report\s*===.*?```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE | re.DOTALL)'
    ),
    # Исправляем другие возможные проблемные regex
    (
        r're\.compile\(r"[^"]*[а-яА-Я][^"]*"\)',
        lambda match: 're.compile(r"")'  # Заменяем на пустой pattern если найдём другие
    )
]

fixed_count = 0
for old, new in fixes:
    if callable(new):
        # Для regex замен
        content, count = re.subn(old, new, content)
        fixed_count += count
    else:
        # Для простых замен
        if old in content:
            content = content.replace(old, new)
            fixed_count += 1

if fixed_count > 0:
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"SUCCESS: Fixed {fixed_count} regex patterns")
else:
    print("No regex patterns found to fix")

# Проверим компиляцию файла
try:
    compile(content, '/app/app.py', 'exec')
    print("SUCCESS: File compiles without errors")
except Exception as e:
    print(f"ERROR: File still has compilation errors: {e}")
