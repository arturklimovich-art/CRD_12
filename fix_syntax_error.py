# fix_syntax_error.py
with open('/app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Исправляем строку 219 (индекс 218)
if len(lines) > 218:
    lines[218] = '            logger.info(f"[DEBUG] target_filepath: {target_filepath}, is_app_py: {is_app_py}")\n'
    print("Fixed syntax error on line 219")

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("SUCCESS: Syntax error fixed")
