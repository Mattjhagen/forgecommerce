import html, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from .config import Settings
from .db import connect
from .services import Commerce, DomainError
from .security import RateLimiter

class Handler(BaseHTTPRequestHandler):
    server_version = "ForgeCommerce/0.1"
    def send_json(self, status, value):
        raw=json.dumps(value, separators=(",",":"), default=str).encode(); self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
    def send_html(self, status, value):
        raw=value.encode(); self.send_response(status); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.send_header("Content-Security-Policy","default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'"); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
    def send_xml(self, status, value):
        raw=value.encode(); self.send_response(status); self.send_header("Content-Type","application/xml; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(raw)
    def storefront_html(self, slug):
        store=self.server.commerce.tenant(slug)
        return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>%s</title><style>body{font:16px system-ui;margin:0;color:#172033;background:#f6f7fb}header{padding:28px 7vw;background:#172033;color:white}main{padding:32px 7vw;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}.card{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:20px;box-shadow:0 5px 18px #17203312}.price{font-weight:700;font-size:1.2rem}button{background:#3457d5;color:#fff;border:0;border-radius:8px;padding:10px 14px;cursor:pointer}</style></head><body><header><small>ForgeCommerce storefront</small><h1>%s</h1></header><main id='products'><p>Loading products…</p></main><script>const slug=%s;const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));fetch('/store/'+slug+'/products').then(r=>r.json()).then(({products})=>{document.querySelector('#products').innerHTML=products.map(p=>`<article class="card"><h2>${esc(p.name)}</h2><p class="price">$${(p.price_cents/100).toFixed(2)}</p><p>${Number(p.inventory)} available</p><button onclick="add('${encodeURIComponent(p.id)}')">Add to cart</button></article>`).join('')});let cart=null;async function add(id){id=decodeURIComponent(id);if(!cart)cart=await (await fetch('/store/'+slug+'/carts',{method:'POST'})).json();await fetch('/store/'+slug+'/carts/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cart_id:cart.id,product_id:id,quantity:1})});alert('Added to cart');}</script></body></html>""" % (html.escape(store["name"]), html.escape(store["name"]), json.dumps(slug))
    def public_page_html(self, slug, page_slug, locale=None):
        page=self.server.commerce.public_page(slug,page_slug,locale); seo=json.loads(page["seo_json"] or "{}"); content=json.loads(page["content_json"] or "{}"); title=html.escape(str(seo.get("title") or page["title"])); description=html.escape(str(seo.get("description") or "")); headings=[]
        for section in content.get("sections",[]) if isinstance(content,dict) else []:
            if isinstance(section,dict) and section.get("heading"): headings.append(f"<h2>{html.escape(str(section['heading']))}</h2>")
        return f"<!doctype html><html><head><meta charset='utf-8'><meta name='description' content='{description}'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title></head><body><main>{''.join(headings) or '<p>Published page</p>'}</main></body></html>"
    def editor_html(self):
        return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ForgeCommerce Editor</title><style>body{font:15px system-ui;margin:0;background:#eef1f7;color:#172033}header{background:#172033;color:white;padding:18px 5vw}main{max-width:1100px;margin:28px auto;display:grid;grid-template-columns:280px 1fr;gap:22px;padding:0 18px}.panel,.canvas{background:white;border-radius:14px;padding:22px;box-shadow:0 8px 30px #17203312}.canvas{min-height:480px;border:2px dashed #cad2e2}label{display:block;margin:12px 0 5px;font-weight:600}input,textarea{width:100%;box-sizing:border-box;padding:9px;border:1px solid #cbd5e1;border-radius:7px}button{margin-top:12px;background:#3457d5;color:white;border:0;border-radius:7px;padding:10px 14px;cursor:pointer}.muted{color:#64748b}</style></head><body><header><strong>ForgeCommerce</strong> · Visual editor</header><main><section class='panel'><h2>Page setup</h2><label>Bearer token<input id='token' placeholder='Paste merchant token'></label><label>Title<input id='title' value='Home'></label><label>Content JSON<textarea id='content'>{"sections":[{"type":"hero","heading":"Welcome"}]}</textarea><button onclick='createPage()'>Create draft</button><button onclick='publish()'>Publish latest</button><button onclick='rollback()'>Rollback to version 1</button><p id='status' class='muted'>Drafts are versioned and publishable.</p></section><section class='canvas'><h2 id='preview'>Preview</h2><p>This responsive canvas is the local editor preview surface.</p><pre id='json'></pre></section></main><script>let page=null;const auth=()=>({'Authorization':'Bearer '+document.querySelector('#token').value,'Content-Type':'application/json'});function show(){document.querySelector('#json').textContent=JSON.stringify(page,null,2);document.querySelector('#preview').textContent=page?.title||'Preview'}async function createPage(){let r=await fetch('/api/pages',{method:'POST',headers:auth(),body:JSON.stringify({title:title.value,content:JSON.parse(content.value)})});page=await r.json();status.textContent=r.ok?'Draft created with version 1':page.error;show()}async function publish(){if(!page)return;let r=await fetch('/api/pages/'+page.id+'/publish',{method:'POST',headers:auth(),body:'{}'});page=await r.json();status.textContent=r.ok?'Published version '+page.published_version:page.error;show()}async function rollback(){if(!page)return;let r=await fetch('/api/pages/'+page.id+'/rollback',{method:'POST',headers:auth(),body:JSON.stringify({version:1})});page=await r.json();status.textContent=r.ok?'Rolled back to version 1':page.error;show()}</script></body></html>"""
    def body(self):
        length=int(self.headers.get("Content-Length","0"));
        if length > self.server.settings.max_body_bytes: raise DomainError("request body too large",413)
        try: return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError: raise DomainError("invalid JSON")
    def auth(self):
        if self.headers.get("X-API-Key"): return self.server.commerce.authenticate_api_key(self.headers["X-API-Key"])
        return self.server.commerce.authenticate(self.headers.get("Authorization","").removeprefix("Bearer ").strip())
    def do_GET(self):
        try:
            if not self.server.limiter.allow(self.client_address[0]): return self.send_json(429,{"error":"rate limit exceeded"})
            path=urlparse(self.path).path
            if path=="/health": return self.send_json(200,{"status":"ok","service":"forgecommerce"})
            parts=path.strip("/").split("/")
            if len(parts)==2 and parts[0]=="store": return self.send_html(200,self.storefront_html(parts[1]))
            if path=="/editor": return self.send_html(200,self.editor_html())
            if len(parts)==3 and parts[0]=="store" and parts[2]=="products": return self.send_json(200,{"products":self.server.commerce.public_products(parts[1])})
            if len(parts)==3 and parts[0]=="store" and parts[2]=="search": return self.send_json(200,{"products":self.server.commerce.public_search(parts[1],parse_qs(urlparse(self.path).query).get("q",[""])[0])})
            if len(parts)==3 and parts[0]=="store" and parts[2]=="sitemap.xml": return self.send_xml(200,self.server.commerce.sitemap(parts[1]))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="pages": return self.send_json(200,self.server.commerce.public_page(parts[1],parts[3],parse_qs(urlparse(self.path).query).get("lang",[None])[0]))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="page": return self.send_html(200,self.public_page_html(parts[1],parts[3],parse_qs(urlparse(self.path).query).get("lang",[None])[0]))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="collections": return self.send_json(200,self.server.commerce.public_collection(parts[1],parts[3]))
            auth=self.auth()
            if path=="/api/products": return self.send_json(200,{"products":self.server.commerce.products(auth)})
            if path.startswith("/api/products/") and path.endswith("/variants"):
                return self.send_json(200,{"variants":self.server.commerce.variants(auth,path.split("/")[3])})
            if path.startswith("/api/products/"): return self.send_json(200,self.server.commerce.product(auth,path.rsplit("/",1)[1]))
            if path.startswith("/api/carts/"): return self.send_json(200,self.server.commerce.cart(auth,path.rsplit("/",1)[1]))
            if path=="/api/orders": return self.send_json(200,{"orders":self.server.commerce.orders(auth,parse_qs(urlparse(self.path).query).get("search",[""])[0])})
            if path=="/api/pages": return self.send_json(200,{"pages":self.server.commerce.pages(auth)})
            if path.startswith("/api/pages/") and path.endswith("/translations"): return self.send_json(200,{"translations":self.server.commerce.translations(auth,path.split("/")[3])})
            if path.startswith("/api/pages/"): return self.send_json(200,self.server.commerce.page(auth,path.rsplit("/",1)[1]))
            if path=="/api/feature-flags": return self.send_json(200,{"flags":self.server.commerce.flags(auth)})
            if path=="/api/audit-events": return self.send_json(200,{"events":self.server.commerce.audit_events(auth)})
            if path=="/api/staff": return self.send_json(200,{"staff":self.server.commerce.staff_list(auth)})
            if path=="/api/customers": return self.send_json(200,{"customers":self.server.commerce.customers(auth)})
            if path=="/api/analytics": return self.send_json(200,self.server.commerce.analytics(auth))
            if path=="/api/admin/health": return self.send_json(200,self.server.commerce.admin_health(auth))
            if path=="/api/admin/usage": return self.send_json(200,self.server.commerce.usage(auth))
            if path=="/api/api-keys": return self.send_json(200,{"keys":self.server.commerce.api_keys(auth)})
            if path=="/api/webhooks": return self.send_json(200,{"webhooks":self.server.commerce.webhooks(auth)})
            if path.startswith("/api/webhooks/") and path.endswith("/deliveries"): return self.send_json(200,{"deliveries":self.server.commerce.webhook_deliveries(auth,path.split("/")[3])})
            raise DomainError("route not found",404)
        except DomainError as e: self.send_json(e.status,{"error":e.message})
        except Exception: self.send_json(500,{"error":"internal server error"})
    def do_POST(self):
        try:
            if not self.server.limiter.allow(self.client_address[0]): return self.send_json(429,{"error":"rate limit exceeded"})
            path=urlparse(self.path).path; data=self.body(); c=self.server.commerce
            if path=="/api/auth/register": return self.send_json(201,c.register(data.get("email",""),data.get("password",""),data.get("store_name","")))
            if path=="/api/auth/login": return self.send_json(200,c.login(data.get("email",""),data.get("password","")))
            parts=path.strip("/").split("/")
            if len(parts)==3 and parts[0]=="store" and parts[2]=="carts": return self.send_json(201,c.public_cart_create(parts[1]))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="carts" and parts[3]=="checkout": return self.send_json(201,c.public_checkout(parts[1],data.get("cart_id"),data.get("customer_email",""),self.headers.get("Idempotency-Key","")))
            if len(parts)==4 and parts[0]=="store" and parts[2]=="carts" and parts[3]=="items": return self.send_json(200,c.public_cart_add(parts[1],data.get("cart_id"),data.get("product_id"),data.get("quantity")))
            auth=self.auth()
            if path=="/api/products": return self.send_json(201,c.product_create(auth,data))
            if path=="/api/collections": return self.send_json(201,c.collection_create(auth,data))
            if path.startswith("/api/collections/") and path.endswith("/products"):
                return self.send_json(200,c.collection_add(auth,path.split("/")[3],data.get("product_id")))
            if path.startswith("/api/products/") and path.endswith("/variants"):
                return self.send_json(201,c.variant_create(auth,path.split("/")[3],data))
            if path.startswith("/api/products/") and path.endswith("/inventory"):
                return self.send_json(200,c.inventory_update(auth,path.split("/")[3],data.get("inventory")))
            if path=="/api/carts": return self.send_json(201,c.cart_create(auth))
            if path.startswith("/api/carts/") and path.endswith("/items"):
                return self.send_json(200,c.cart_add(auth,path.split("/")[3],data.get("product_id"),data.get("quantity")))
            if path=="/api/checkout": return self.send_json(201,c.checkout(auth,data.get("cart_id"),data.get("customer_email",""),self.headers.get("Idempotency-Key","")))
            if path=="/api/pages": return self.send_json(201,c.page_create(auth,data))
            if path.startswith("/api/pages/") and path.endswith("/translations"):
                return self.send_json(200,c.translation_upsert(auth,path.split("/")[3],data.get("locale"),data))
            if path.startswith("/api/pages/") and path.endswith("/versions"):
                return self.send_json(201,c.page_version(auth,path.split("/")[3],data))
            if path.startswith("/api/pages/") and path.endswith("/publish"):
                return self.send_json(200,c.page_publish(auth,path.split("/")[3],data.get("version")))
            if path.startswith("/api/pages/") and path.endswith("/rollback"):
                return self.send_json(200,c.page_rollback(auth,path.split("/")[3],data.get("version")))
            if path.startswith("/api/orders/") and path.endswith("/refund"):
                return self.send_json(200,c.refund(auth,path.split("/")[3]))
            if path.startswith("/api/orders/") and path.endswith("/status"):
                return self.send_json(200,c.order_status(auth,path.split("/")[3],data.get("status")))
            if path=="/api/feature-flags": return self.send_json(200,c.flag_set(auth,data.get("name"),data.get("enabled")))
            if path=="/api/api-keys": return self.send_json(201,c.api_key_create(auth,data.get("name")))
            if path.startswith("/api/api-keys/") and path.endswith("/revoke"): return self.send_json(200,c.api_key_revoke(auth,path.split("/")[3]))
            if path=="/api/webhooks": return self.send_json(201,c.webhook_create(auth,data))
            if path=="/api/staff": return self.send_json(201,c.staff_create(auth,data))
            raise DomainError("route not found",404)
        except DomainError as e: self.send_json(e.status,{"error":e.message})
        except Exception: self.send_json(500,{"error":"internal server error"})
    def log_message(self, *_): pass

def make_server(settings=None):
    settings=settings or Settings(); server=ThreadingHTTPServer((settings.host,settings.port),Handler); server.settings=settings; server.commerce=Commerce(connect(settings.db_path),settings.session_hours); server.limiter=RateLimiter(); return server

if __name__ == "__main__":
    server=make_server(); print(f"ForgeCommerce listening on http://{server.settings.host}:{server.settings.port}",flush=True); server.serve_forever()
