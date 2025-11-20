with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add logging right after the if condition
old_code = '''                if curator_url and generated_code:
                    logger.info("[CURATOR] Condition TRUE - calling Curator API...")
                    try:
                        update.message.reply_text("Sending to Curator...")'''

new_code = '''                if curator_url and generated_code:
                    logger.info("[CURATOR] Condition TRUE - calling Curator API...")
                    logger.info(f"[CURATOR] curator_url={curator_url}")
                    logger.info(f"[CURATOR] generated_code length={len(generated_code)}")
                    try:
                        logger.info("[CURATOR] Sending message to user...")
                        update.message.reply_text("Sending to Curator...")
                        logger.info("[CURATOR] Message sent, preparing payload...")'''

content = content.replace(old_code, new_code)

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Inner logging added!")
