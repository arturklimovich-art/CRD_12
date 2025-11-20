with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove await from reply_text call in Curator block
content = content.replace(
    'await update.message.reply_text("Sending to Curator...")',
    'update.message.reply_text("Sending to Curator...")'
)

# Also check if there are any other await calls that shouldn't be there
import re
# Find the function definition
match = re.search(r'(async )?def run_roadmap_command', content)
if match and not match.group(1):
    print("Function is NOT async - await should be removed")
else:
    print("Function IS async - await is correct")

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Await removed successfully!")
