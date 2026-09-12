import http.server
import json
import os
import socketserver

PORT = 3000
SERVER_NAME = os.environ.get("SERVER_NAME", "backend-default")

class EchoHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        client_direct_ip = self.client_address[0]
        x_real_ip = self.headers.get("X-Real-IP", "Yok (Header Gönderilmedi)")
        x_forwarded_for = self.headers.get("X-Forwarded-For", "Yok (Header Gönderilmedi)")
        host = self.headers.get("Host", "")

        response_data = {
            "status": "success",
            "served_by": SERVER_NAME,
            "analiz": {
                "dogrudan_baglanan_ip (Nginx)": client_direct_ip,
                "gercek_kullanici_ip (X-Real-IP)": x_real_ip,
                "proxy_zinciri (X-Forwarded-For)": x_forwarded_for,
                "istenen_host": host
            },
            "mesaj": f"Tebrikler! İstek Nginx üzerinden '{SERVER_NAME}' sunucusuna iletildi."
        }

        # Konsola log bas (docker compose logs ile izlemek için)
        print(f"[{SERVER_NAME}] İSTEK ALINDI! Doğrudan IP: {client_direct_ip} | Gerçek İstemci IP: {x_real_ip}", flush=True)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode("utf-8"))

if __name__ == "__main__":
    print(f"[{SERVER_NAME}] Dinleniyor: Port {PORT}...", flush=True)
    with socketserver.TCPServer(("", PORT), EchoHandler) as httpd:
        httpd.serve_forever()
