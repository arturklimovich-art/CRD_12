import urllib.request, urllib.error, sys, py_compile
print("--- py_compile ---")
try:
    py_compile.compile("/app/app.py", doraise=True)
    print("✅ py_compile OK")
except Exception as e:
    print("❌ py_compile ERR:", type(e).__name__, e)
    sys.exit(1)
print("--- HTTP checks ---")
for url in ("http://127.0.0.1:8000/ready","http://127.0.0.1:8000/system/health"):
    try:
        r = urllib.request.urlopen(url, timeout=3)
        body = r.read().decode("utf-8","replace")
        print(url, "->", r.status, body[:300].replace("\n"," "))
    except Exception as e:
        print(url, "-> ERR:", type(e).__name__, e)
