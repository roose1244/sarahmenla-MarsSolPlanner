"""Tiny static server so the live dashboard can fetch demo/plan.json.

Usage:
    python serve.py            # http://localhost:8000/demo/dashboard.html
    python serve.py --port 9000
"""
import argparse, http.server, socketserver, os

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", args.port),
                                http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Serving on http://localhost:{args.port}")
        print(f"→ Live dashboard: http://localhost:{args.port}/demo/dashboard.html")
        print(f"→ 3D scene:       http://localhost:{args.port}/demo/plan_three.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nBye.")
