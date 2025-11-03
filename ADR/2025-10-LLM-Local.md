# ADR — Local LLM (Ollama + OpenAI‑proxy), 7B‑Q4 on 6GB VRAM
Decision: use qwen2.5:7b‑instruct‑q4_K_M with FAST/LONG profiles; OpenAI‑compatible proxy (litellm).
Risks: VRAM pressure on LONG; mitigations: default FAST. Rollback: switch to cloud provider via ENV.
