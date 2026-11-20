import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .config import Settings
from .db import connect
from .services import Commerce, DomainError

class Handler(BaseHTTPRequestHandler):
    server_version = "ForgeCommerce/0.1"
    def send_json(self, status, value):
        raw=json.dumps(value, separators=(",",":"), default=str).encode(); self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
    def body(self):
        length=int(self.headers.get("Content-Length","0"));
        if length > self.server.settings.max_body_bytes: raise DomainError("request body too large",413)
        try: return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError: raise DomainError("invalid JSON")
    def auth(self): return self.server.commerce.authenticate(self.headers.get("Authorization","").removeprefix("Bearer ").strip())
    def do_GET(self):
        try:
            path=urlparse(self.path).path
            if path=="/health": return self.send_json(200,{"status":"ok","service":"forgecommerce"})
            parts=path.strip("/").split("/")
            if len(parts)==3 and parts[0]=="store" and parts[2]=="products": return self.send_json(200,{"products":self.server.commerce.public_products(parts[1])})
            if len(parts)==4 and parts[0]=="store" and parts[2]=="pages": return self.send_json(200,self.server.commerce.public_page(parts[1],parts[3]))
            auth=self.auth()
            if path=="/api/products": return self.send_json(200,{"products":self.server.commerce.products(auth)})
            if path.startswith("/api/products/"): return self.send_json(200,self.server.commerce.product(auth,path.rsplit("/",1)[1]))
            if path.startswith("/api/carts/"): return self.send_json(200,self.server.commerce.cart(auth,path.rsplit("/",1)[1]))
            if path=="/api/orders": return self.send_json(200,{"orders":self.server.commerce.orders(auth)})
            if path=="/api/pages": return self.send_json(200,{"pages":self.server.commerce.pages(auth)})
            if path.startswith("/api/pages/"): return self.send_json(200,self.server.commerce.page(auth,path.rsplit("/",1)[1]))
            if path=="/api/feature-flags": return self.send_json(200,{"flags":self.server.commerce.flags(auth)})
            if path=="/api/audit-events": return self.send_json(200,{"events":self.server.commerce.audit_events(auth)})
            if path=="/api/staff": return self.send_json(200,{"staff":self.server.commerce.staff_list(auth)})
            raise DomainError("route not found",404)
        except DomainError as e: self.send_json(e.status,{"error":e.message})
        except Exception: self.send_json(500,{"error":"internal server error"})
    def do_POST(self):
        try:
            path=urlparse(self.path).path; data=self.body(); c=self.server.commerce
            if path=="/api/auth/register": return self.send_json(201,c.register(data.get("email",""),data.get("password",""),data.get("store_name","")))
            if path=="/api/auth/login": return self.send_json(200,c.login(data.get("email",""),data.get("password","")))
            parts=path.strip("/").split("/")
            if len(parts)==3 and parts[0]=="store" and parts[2]=="carts": return self.send_json(201,c.public_cart_create(parts[1]))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="carts" and parts[3]=="checkout": return self.send_json(201,c.public_checkout(parts[1],data.get("cart_id"),data.get("customer_email",""),self.headers.get("Idempotency-Key","")))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="carts" and parts[3]=="items": return self.send_json(200,c.public_cart_add(parts[1],data.get("cart_id"),data.get("product_id"),data.get("quantity")))
            auth=self.auth()
            if path=="/api/products": return self.send_json(201,c.product_create(auth,data))
            if path.startswith("/api/products/") and path.endswith("/inventory"):
                return self.send_json(200,c.inventory_update(auth,path.split("/")[3],data.get("inventory")))
            if path=="/api/carts": return self.send_json(201,c.cart_create(auth))
            if path.startswith("/api/carts/") and path.endswith("/items"):
                return self.send_json(200,c.cart_add(auth,path.split("/")[3],data.get("product_id"),data.get("quantity")))
            if path=="/api/checkout": return self.send_json(201,c.checkout(auth,data.get("cart_id"),data.get("customer_email",""),self.headers.get("Idempotency-Key","")))
            if path=="/api/pages": return self.send_json(201,c.page_create(auth,data))
            if path.startswith("/api/pages/") and path.endswith("/versions"):
                return self.send_json(201,c.page_version(auth,path.split("/")[3],data))
            if path.startswith("/api/pages/") and path.endswith("/publish"):
                return self.send_json(200,c.page_publish(auth,path.split("/")[3],data.get("version")))
            if path.startswith("/api/orders/") and path.endswith("/refund"):
                return self.send_json(200,c.refund(auth,path.split("/")[3]))
            if path=="/api/feature-flags": return self.send_json(200,c.flag_set(auth,data.get("name"),data.get("enabled")))
            if path=="/api/staff": return self.send_json(201,c.staff_create(auth,data))
            raise DomainError("route not found",404)
        except DomainError as e: self.send_json(e.status,{"error":e.message})
        except Exception: self.send_json(500,{"error":"internal server error"})
    def log_message(self, *_): pass

def make_server(settings=None):
    settings=settings or Settings(); server=ThreadingHTTPServer((settings.host,settings.port),Handler); server.settings=settings; server.commerce=Commerce(connect(settings.db_path),settings.session_hours); return server

if __name__ == "__main__":
    server=make_server(); print(f"ForgeCommerce listening on http://{server.settings.host}:{server.settings.port}",flush=True); server.serve_forever()
