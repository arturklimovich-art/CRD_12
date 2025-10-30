import requests, concurrent.futures

URL = "http://localhost:8000/tasks"

def send_request(i):
    try:
        r = requests.post(URL, json={"user_input": f"test {i}", "topic": "load"}, timeout=5)
        return r.status_code
    except Exception:
        return 0

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(send_request, range(50)))
    print("Results:", results.count(200), "successes of", len(results))
