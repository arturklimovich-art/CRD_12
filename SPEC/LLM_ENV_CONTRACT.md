# Unified ENV Contract
- LLM_PROVIDER: local|cloud
- LLM_PROFILE: fast|long
- OFFLINE_MODE: true|false
- OPENAI_BASE_URL, OPENAI_API_KEY
- LLM_MODEL, LLM_CTX_LEN, LLM_KV_POLICY, LLM_BATCH_SIZE
- *_LOCAL & *_CLOUD mapped from provider/profile without changing business code
