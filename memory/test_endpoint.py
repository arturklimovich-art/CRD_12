import requests, json
url = "http://127.0.0.1:8000/api/patches/f46262d1-ff1d-4612-909e-939b607b149a/apply?approve_token=test"
try:
    r = requests.post(url, timeout=5)
    print("Status:", r.status_code)
    print("Body:", json.dumps(r.json(), indent=2))
except Exception as e:
    print("Error:", e)
