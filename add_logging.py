with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the Curator block with logging
old_code = '''                # Get generated code
                generated_code = result.get("generated_code", "")

                # Call Curator API
                curator_url = os.getenv("CURATOR_API_URL", "")

                if curator_url and generated_code:'''

new_code = '''                # Get generated code
                generated_code = result.get("generated_code", "")
                logger.info(f"[CURATOR] Generated code length: {len(generated_code)}")

                # Call Curator API
                curator_url = os.getenv("CURATOR_API_URL", "")
                logger.info(f"[CURATOR] CURATOR_API_URL: {curator_url}")
                logger.info(f"[CURATOR] Checking condition: curator_url={bool(curator_url)}, generated_code={bool(generated_code)}")

                if curator_url and generated_code:
                    logger.info("[CURATOR] Condition TRUE - calling Curator API...")'''

content = content.replace(old_code, new_code)

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Logging added successfully!")
