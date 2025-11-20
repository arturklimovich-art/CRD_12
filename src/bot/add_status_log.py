with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the line where status is extracted
old_line = '            status = result.get("engineer_status", "unknown")'
new_lines = '''            status = result.get("engineer_status", "unknown")
            logger.info(f"[DEBUG] Response from Engineer B: status={status}")
            logger.info(f"[DEBUG] Full result keys: {list(result.keys())}")
            logger.info(f"[DEBUG] Checking if status == 'passed': {status == 'passed'}")'''

content = content.replace(old_line, new_lines)

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Status logging added!")
