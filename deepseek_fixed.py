from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class DeepSeekProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    
    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return self.rfile.read(content_length)
        return b''
    
    def _send_response(self, data, status=200, content_type="application/json"):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.wfile.flush()

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send_response("OK", content_type="text/plain")
        else:
            self._send_response("OK", content_type="text/plain")

    def do_POST(self):
        if self.path.startswith("/llm/complete"):
            # Читаем тело запроса
            body = self._read_body()
            print(f"Received POST to /llm/complete, body: {body}")
            
            # Возвращаем стабильный ответ
            response = {"output": "[stub response]"}
            self._send_response(response)
        else:
            self._send_response("Not found", status=404)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8010), DeepSeekProxyHandler)
    print("DeepSeek Proxy running on port 8010...")
    server.serve_forever()
