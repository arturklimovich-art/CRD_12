import sys

with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check if dotenv already imported
has_dotenv_import = any('from dotenv import load_dotenv' in line for line in lines)
has_dotenv_call = any('load_dotenv()' in line for line in lines)

if not has_dotenv_import:
    # Find line with 'import os'
    for i, line in enumerate(lines):
        if line.strip() == 'import os':
            lines.insert(i + 1, 'from dotenv import load_dotenv\n')
            print(f"Added dotenv import after line {i+1}")
            break

if not has_dotenv_call:
    # Find line with 'import os' and add load_dotenv() after imports section
    for i, line in enumerate(lines):
        if i > 0 and lines[i-1].startswith('import ') and not line.startswith('import ') and not line.startswith('from '):
            lines.insert(i, '\n# Load environment variables\nload_dotenv()\n\n')
            print(f"Added load_dotenv() call at line {i}")
            break

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Dotenv configuration added successfully!")
