import hashlib, hmac, json, re
from datetime import datetime, timedelta, timezone
from .security import api_key_hash, hash_password, verify_password, token_hash, new_id

def now(): return datetime.now(timezone.utc).isoformat()
def slugify(value): return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "store"

class DomainError(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

class Commerce:
    def __init__(self, conn, session_hours=24): self.db, self.session_hours = conn, session_hours
    def audit(self, tenant, user, action, resource_type=None, resource_id=None, metadata=None):
        self.db.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?)", (new_id(), tenant, user, action, resource_type, resource_id, json.dumps(metadata or {}, sort_keys=True), now()))
    def register(self, email, password, store_name):
        email = email.strip().lower()
        if "@" not in email or len(email) > 254: raise DomainError("valid email required")
        try: password_hash = hash_password(password)
        except ValueError as exc: raise DomainError(str(exc))
        tenant_id, user_id = new_id(), new_id()
        try:
            self.db.execute("BEGIN")
            self.db.execute("INSERT INTO tenants VALUES (?,?,?,?)", (tenant_id, store_name.strip()[:100], slugify(store_name), now()))
            self.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (user_id, tenant_id, email, password_hash, "owner", now()))
            self.db.execute("INSERT INTO tenant_limits (tenant_id) VALUES (?)", (tenant_id,))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise DomainError("email or store slug already exists", 409)
        self.audit(tenant_id, user_id, "merchant.registered", "tenant", tenant_id)
        return self.login(email, password)
    def login(self, email, password):
        row = self.db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if not row or not verify_password(password, row["password_hash"]): raise DomainError("invalid credentials", 401)
        raw = new_id() + new_id()
        expires = (datetime.now(timezone.utc) + timedelta(hours=self.session_hours)).isoformat()
        self.db.execute("INSERT INTO sessions VALUES (?,?,?,?,?)", (token_hash(raw), row["id"], row["tenant_id"], expires, now()))
        return {"token": raw, "user": {"id": row["id"], "email": row["email"], "role": row["role"], "tenant_id": row["tenant_id"]}}
    def authenticate(self, token):
        if not token: raise DomainError("authentication required", 401)
        row = self.db.execute("SELECT * FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?", (token_hash(token), now())).fetchone()
        if not row: raise DomainError("invalid or expired session", 401)
        return row
    def authenticate_api_key(self, key):
        row=self.db.execute("SELECT u.*,k.id AS api_key_id FROM users u JOIN api_keys k ON k.user_id=u.id WHERE k.key_hash=? AND k.revoked_at IS NULL",(api_key_hash(key),)).fetchone()
        if not row: raise DomainError("invalid or revoked API key",401)
        return row
    def api_keys(self, auth):
        return [dict(row) for row in self.db.execute("SELECT id,name,prefix,created_at,revoked_at FROM api_keys WHERE tenant_id=? ORDER BY created_at DESC",(auth["tenant_id"],))]
    def api_key_create(self, auth, name):
        if auth["role"] not in {"owner","admin"}: raise DomainError("admin access required",403)
        name=str(name or "").strip()
        if not name: raise DomainError("API key name required")
        raw="fc_live_"+new_id()+new_id(); kid=new_id(); prefix=raw[:14]
        self.db.execute("INSERT INTO api_keys VALUES (?,?,?,?,?,?,?,?)",(kid,auth["tenant_id"],auth["id"],name[:100],api_key_hash(raw),prefix,now(),None))
        self.audit(auth["tenant_id"],auth["id"],"api_key.created","api_key",kid,{"name":name})
        return {"id":kid,"name":name,"prefix":prefix,"key":raw}
    def api_key_revoke(self, auth, kid):
        if auth["role"] not in {"owner","admin"}: raise DomainError("admin access required",403)
        changed=self.db.execute("UPDATE api_keys SET revoked_at=? WHERE id=? AND tenant_id=? AND revoked_at IS NULL",(now(),kid,auth["tenant_id"]))
        if changed.rowcount != 1: raise DomainError("API key not found",404)
        self.audit(auth["tenant_id"],auth["id"],"api_key.revoked","api_key",kid); return {"id":kid,"revoked":True}
    def webhook_create(self, auth, data):
        if auth["role"] not in {"owner","admin"}: raise DomainError("admin access required",403)
        url=str(data.get("url","")).strip(); events=data.get("events",["order.created"])
        if not (url.startswith("https://") or url.startswith("http://localhost")) or not isinstance(events,list) or not events: raise DomainError("valid webhook URL and events required")
        wid=new_id(); secret="whsec_"+new_id()+new_id(); self.db.execute("INSERT INTO webhooks VALUES (?,?,?,?,?,?,?)",(wid,auth["tenant_id"],url,secret,json.dumps(events),1,now())); self.audit(auth["tenant_id"],auth["id"],"webhook.created","webhook",wid)
        return {"id":wid,"url":url,"events":events,"secret":secret}
    def webhooks(self, auth):
        return [{"id":r["id"],"url":r["url"],"events":json.loads(r["events_json"]),"active":bool(r["active"]),"created_at":r["created_at"]} for r in self.db.execute("SELECT id,url,events_json,active,created_at FROM webhooks WHERE tenant_id=? ORDER BY created_at DESC",(auth["tenant_id"],))]
    def webhook_deliveries(self, auth, wid):
        if not self.db.execute("SELECT 1 FROM webhooks WHERE id=? AND tenant_id=?",(wid,auth["tenant_id"])).fetchone(): raise DomainError("webhook not found",404)
        return [dict(r) for r in self.db.execute("SELECT id,event_type,payload_json,signature,status,created_at FROM webhook_deliveries WHERE webhook_id=? ORDER BY created_at DESC",(wid,))]
    def emit_webhook(self, tenant_id, event_type, payload):
        encoded=json.dumps(payload,sort_keys=True,separators=(",",":"))
        for hook in self.db.execute("SELECT * FROM webhooks WHERE tenant_id=? AND active=1",(tenant_id,)).fetchall():
            if event_type not in json.loads(hook["events_json"]) and "*" not in json.loads(hook["events_json"]): continue
            signature=hmac.new(hook["secret"].encode(),encoded.encode(),hashlib.sha256).hexdigest()
            self.db.execute("INSERT INTO webhook_deliveries VALUES (?,?,?,?,?,?,?)",(new_id(),hook["id"],event_type,encoded,signature,"queued",now()))
    def product_create(self, auth, data):
        limit=self.db.execute("SELECT product_limit FROM tenant_limits WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()
        if limit and self.db.execute("SELECT COUNT(*) FROM products WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0] >= limit[0]: raise DomainError("product quota exceeded",409)
        name = str(data.get("name", "")).strip(); price = data.get("price_cents"); inventory = data.get("inventory", 0)
        if not name or not isinstance(price, int) or price < 0 or not isinstance(inventory, int) or inventory < 0: raise DomainError("name, non-negative integer price_cents and inventory required")
        pid = new_id(); slug = slugify(name)
        try: self.db.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, auth["tenant_id"], name[:200], slug, price, inventory, "active", now()))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DomainError("product slug already exists", 409)
            raise
        self.audit(auth["tenant_id"], auth["id"], "product.created", "product", pid, {"name": name})
        return self.product(auth, pid)
    def products(self, auth): return [dict(r) for r in self.db.execute("SELECT id,name,slug,price_cents,inventory,status,created_at FROM products WHERE tenant_id=? ORDER BY created_at", (auth["tenant_id"],))]
    def product(self, auth, pid):
        row = self.db.execute("SELECT id,name,slug,price_cents,inventory,status,created_at FROM products WHERE tenant_id=? AND id=?", (auth["tenant_id"], pid)).fetchone()
        if not row: raise DomainError("product not found", 404)
        result=dict(row); result["variants"]=[dict(v) for v in self.db.execute("SELECT id,sku,name,price_cents,inventory,created_at FROM product_variants WHERE product_id=? AND tenant_id=? ORDER BY created_at",(pid,auth["tenant_id"]))]; return result
    def variants(self, auth, pid):
        self.product(auth,pid)
        return [dict(row) for row in self.db.execute("SELECT id,sku,name,price_cents,inventory,created_at FROM product_variants WHERE product_id=? AND tenant_id=? ORDER BY created_at",(pid,auth["tenant_id"]))]
    def variant_create(self, auth, pid, data):
        self.product(auth,pid); sku=str(data.get("sku","")).strip().upper(); name=str(data.get("name","")).strip(); price=data.get("price_cents"); inventory=data.get("inventory",0)
        if not sku or not name or not isinstance(price,int) or price<0 or not isinstance(inventory,int) or inventory<0: raise DomainError("sku, name, non-negative price_cents and inventory required")
        vid=new_id()
        try: self.db.execute("INSERT INTO product_variants VALUES (?,?,?,?,?,?,?,?)",(vid,pid,auth["tenant_id"],sku,name[:200],price,inventory,now()))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DomainError("SKU already exists",409)
            raise
        self.audit(auth["tenant_id"],auth["id"],"product.variant.created","product_variant",vid,{"sku":sku})
        return dict(self.db.execute("SELECT id,sku,name,price_cents,inventory,created_at FROM product_variants WHERE id=?",(vid,)).fetchone())
    def collection_create(self, auth, data):
        name=str(data.get("name","")).strip(); slug=slugify(str(data.get("slug") or name))
        if not name: raise DomainError("collection name required")
        cid=new_id()
        try: self.db.execute("INSERT INTO collections VALUES (?,?,?,?,?)",(cid,auth["tenant_id"],name[:200],slug,now()))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DomainError("collection slug already exists",409)
            raise
        self.audit(auth["tenant_id"],auth["id"],"collection.created","collection",cid)
        return self.collection(auth,cid)
    def collection(self, auth, cid):
        row=self.db.execute("SELECT id,name,slug,created_at FROM collections WHERE id=? AND tenant_id=?",(cid,auth["tenant_id"])).fetchone()
        if not row: raise DomainError("collection not found",404)
        result=dict(row); result["products"]=[dict(p) for p in self.db.execute("SELECT p.id,p.name,p.slug,p.price_cents,p.inventory FROM collection_products cp JOIN products p ON p.id=cp.product_id WHERE cp.collection_id=? AND cp.tenant_id=?",(cid,auth["tenant_id"]))]; return result
    def collection_add(self, auth, cid, pid):
        self.collection(auth,cid); self.product(auth,pid)
        try: self.db.execute("INSERT INTO collection_products VALUES (?,?,?)",(cid,pid,auth["tenant_id"]))
        except Exception:
            pass
        return self.collection(auth,cid)
    def public_collection(self, slug, collection_slug):
        tenant=self.tenant(slug); row=self.db.execute("SELECT id,name,slug FROM collections WHERE tenant_id=? AND slug=?",(tenant["id"],collection_slug)).fetchone()
        if not row: raise DomainError("collection not found",404)
        return {"id":row["id"],"name":row["name"],"slug":row["slug"],"products":[dict(p) for p in self.db.execute("SELECT p.id,p.name,p.slug,p.price_cents,p.inventory FROM collection_products cp JOIN products p ON p.id=cp.product_id WHERE cp.collection_id=? AND p.status='active'",(row["id"],))]}
    def inventory_update(self, auth, pid, inventory):
        if not isinstance(inventory, int) or inventory < 0: raise DomainError("inventory must be a non-negative integer")
        changed = self.db.execute("UPDATE products SET inventory=? WHERE id=? AND tenant_id=?", (inventory, pid, auth["tenant_id"]))
        if changed.rowcount != 1: raise DomainError("product not found", 404)
        self.audit(auth["tenant_id"], auth["id"], "inventory.updated", "product", pid, {"inventory": inventory})
        return self.product(auth, pid)
    def cart_create(self, auth):
        cid = new_id(); self.db.execute("INSERT INTO carts VALUES (?,?,?,?,?)", (cid, auth["tenant_id"], None, "open", now())); return {"id": cid, "items": [], "total_cents": 0}
    def cart_add(self, auth, cid, pid, quantity):
        if not isinstance(quantity, int) or quantity < 1: raise DomainError("quantity must be a positive integer")
        cart = self.db.execute("SELECT * FROM carts WHERE id=? AND tenant_id=? AND status='open'", (cid, auth["tenant_id"])).fetchone()
        product = self.db.execute("SELECT * FROM products WHERE id=? AND tenant_id=? AND status='active'", (pid, auth["tenant_id"])).fetchone()
        if not cart or not product: raise DomainError("cart or product not found", 404)
        old = self.db.execute("SELECT quantity FROM cart_items WHERE cart_id=? AND product_id=?", (cid,pid)).fetchone(); total = quantity + (old[0] if old else 0)
        if total > product["inventory"]: raise DomainError("insufficient inventory", 409)
        self.db.execute("INSERT INTO cart_items VALUES (?,?,?,?) ON CONFLICT(cart_id,product_id) DO UPDATE SET quantity=excluded.quantity", (cid,pid,total,product["price_cents"]))
        return self.cart(auth, cid)
    def cart(self, auth, cid):
        cart = self.db.execute("SELECT * FROM carts WHERE id=? AND tenant_id=?", (cid,auth["tenant_id"])).fetchone()
        if not cart: raise DomainError("cart not found",404)
        items = [dict(r) for r in self.db.execute("SELECT ci.product_id, p.name, ci.quantity, ci.unit_price_cents, ci.quantity*ci.unit_price_cents AS line_total_cents FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=?", (cid,))]
        return {"id":cid,"status":cart["status"],"items":items,"total_cents":sum(x["line_total_cents"] for x in items)}
    def checkout(self, auth, cid, email, key):
        if not key or len(key)>128: raise DomainError("Idempotency-Key required")
        existing = self.db.execute("SELECT * FROM orders WHERE tenant_id=? AND idempotency_key=?", (auth["tenant_id"],key)).fetchone()
        if existing: return dict(existing)
        cart = self.cart(auth,cid); email = email.strip().lower()
        if not cart["items"] or "@" not in email: raise DomainError("non-empty cart and valid customer_email required")
        oid = new_id()
        try:
            self.db.execute("BEGIN")
            for item in cart["items"]:
                changed = self.db.execute("UPDATE products SET inventory=inventory-? WHERE id=? AND tenant_id=? AND inventory>=?", (item["quantity"],item["product_id"],auth["tenant_id"],item["quantity"]))
                if changed.rowcount != 1: raise DomainError("inventory changed; retry checkout",409)
            timestamp=now(); customer=self.db.execute("SELECT id FROM customers WHERE tenant_id=? AND email=?",(auth["tenant_id"],email)).fetchone()
            if customer:
                self.db.execute("UPDATE customers SET order_count=order_count+1,total_spend_cents=total_spend_cents+?,updated_at=? WHERE id=?",(cart["total_cents"],timestamp,customer["id"]))
            else:
                self.db.execute("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)",(new_id(),auth["tenant_id"],email,None,1,cart["total_cents"],timestamp,timestamp))
            self.db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", (oid,auth["tenant_id"],cid,email,cart["total_cents"],"paid_sandbox","unfulfilled",key,now()))
            for item in cart["items"]: self.db.execute("INSERT INTO order_items VALUES (?,?,?,?,?)", (oid,item["product_id"],item["name"],item["quantity"],item["unit_price_cents"]))
            self.db.execute("UPDATE carts SET status='converted',customer_email=? WHERE id=?",(email,cid)); self.db.execute("COMMIT")
        except DomainError: self.db.execute("ROLLBACK"); raise
        except Exception: self.db.execute("ROLLBACK"); raise DomainError("checkout could not be completed",409)
        self.audit(auth["tenant_id"],auth["id"],"order.created","order",oid,{"total_cents":cart["total_cents"]})
        self.emit_webhook(auth["tenant_id"],"order.created",{"id":oid,"total_cents":cart["total_cents"],"customer_email":email})
        return dict(self.db.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
    def orders(self, auth, search=""):
        query="SELECT id,customer_email,total_cents,payment_status,fulfillment_status,created_at FROM orders WHERE tenant_id=?"; args=[auth["tenant_id"]]
        if search:
            query += " AND (customer_email LIKE ? OR id LIKE ?)"; needle=f"%{search}%"; args.extend([needle,needle])
        return [dict(row) for row in self.db.execute(query+" ORDER BY created_at DESC", args)]
    def order_status(self, auth, oid, status):
        if status not in {"unfulfilled", "processing", "fulfilled", "cancelled", "returned"}: raise DomainError("invalid fulfillment status")
        changed=self.db.execute("UPDATE orders SET fulfillment_status=? WHERE id=? AND tenant_id=?",(status,oid,auth["tenant_id"]))
        if changed.rowcount != 1: raise DomainError("order not found",404)
        self.audit(auth["tenant_id"],auth["id"],"order.status.updated","order",oid,{"status":status})
        return dict(self.db.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
    def customers(self, auth):
        return [dict(row) for row in self.db.execute("SELECT id,email,name,order_count,total_spend_cents,created_at,updated_at FROM customers WHERE tenant_id=? ORDER BY updated_at DESC", (auth["tenant_id"],))]
    def analytics(self, auth):
        tenant=auth["tenant_id"]
        totals=self.db.execute("SELECT COUNT(*) AS orders,COALESCE(SUM(CASE WHEN payment_status='paid_sandbox' THEN total_cents ELSE 0 END),0) AS gross_cents,COALESCE(SUM(CASE WHEN payment_status='refunded' THEN total_cents ELSE 0 END),0) AS refunded_cents FROM orders WHERE tenant_id=?",(tenant,)).fetchone()
        return {"orders":totals["orders"],"gross_cents":totals["gross_cents"],"refunded_cents":totals["refunded_cents"],"customers":self.db.execute("SELECT COUNT(*) FROM customers WHERE tenant_id=?",(tenant,)).fetchone()[0],"products":self.db.execute("SELECT COUNT(*) FROM products WHERE tenant_id=?",(tenant,)).fetchone()[0],"low_inventory_products":[dict(row) for row in self.db.execute("SELECT id,name,inventory FROM products WHERE tenant_id=? AND inventory<=5 ORDER BY inventory",(tenant,))]}
    def admin_health(self, auth):
        if auth["role"] != "owner": raise DomainError("owner access required",403)
        integrity=self.db.execute("PRAGMA integrity_check").fetchone()[0]
        return {"status":"ok" if integrity=="ok" else "degraded","database_integrity":integrity,"tenant_id":auth["tenant_id"],"table_counts":{"products":self.db.execute("SELECT COUNT(*) FROM products WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0],"orders":self.db.execute("SELECT COUNT(*) FROM orders WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0],"pages":self.db.execute("SELECT COUNT(*) FROM pages WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0]}}
    def usage(self, auth):
        if auth["role"] != "owner": raise DomainError("owner access required",403)
        limits=self.db.execute("SELECT plan,product_limit,page_limit,staff_limit FROM tenant_limits WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()
        return {"plan":limits["plan"],"limits":dict(limits),"usage":{"products":self.db.execute("SELECT COUNT(*) FROM products WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0],"pages":self.db.execute("SELECT COUNT(*) FROM pages WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0],"staff":self.db.execute("SELECT COUNT(*) FROM users WHERE tenant_id=? AND role!='owner'",(auth["tenant_id"],)).fetchone()[0]}}
    def refund(self, auth, oid):
        row = self.db.execute("SELECT * FROM orders WHERE id=? AND tenant_id=?", (oid, auth["tenant_id"])).fetchone()
        if not row: raise DomainError("order not found", 404)
        if row["payment_status"] == "refunded": return dict(row)
        self.db.execute("UPDATE orders SET payment_status='refunded' WHERE id=? AND tenant_id=?", (oid, auth["tenant_id"]))
        self.audit(auth["tenant_id"], auth["id"], "order.refunded", "order", oid)
        return dict(self.db.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone())
    def pages(self, auth):
        return [dict(row) for row in self.db.execute("SELECT id,slug,title,status,published_version,created_at,updated_at FROM pages WHERE tenant_id=? ORDER BY updated_at DESC", (auth["tenant_id"],))]
    def page(self, auth, page_id):
        row = self.db.execute("SELECT * FROM pages WHERE id=? AND tenant_id=?", (page_id, auth["tenant_id"])).fetchone()
        if not row: raise DomainError("page not found", 404)
        page = dict(row)
        versions = [dict(v) for v in self.db.execute("SELECT version,content_json,seo_json,created_by,created_at FROM page_versions WHERE page_id=? ORDER BY version DESC", (page_id,))]
        page["versions"] = versions
        return page
    def page_create(self, auth, data):
        limit=self.db.execute("SELECT page_limit FROM tenant_limits WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()
        if limit and self.db.execute("SELECT COUNT(*) FROM pages WHERE tenant_id=?",(auth["tenant_id"],)).fetchone()[0] >= limit[0]: raise DomainError("page quota exceeded",409)
        title = str(data.get("title", "")).strip(); slug = slugify(str(data.get("slug") or title))
        if not title: raise DomainError("title required")
        pid = new_id(); timestamp = now()
        try:
            self.db.execute("INSERT INTO pages VALUES (?,?,?,?,?,?,?,?)", (pid, auth["tenant_id"], slug, title[:200], "draft", None, timestamp, timestamp))
            self.db.execute("INSERT INTO page_versions VALUES (?,?,?,?,?,?)", (pid, 1, json.dumps(data.get("content", {"sections": []})), json.dumps(data.get("seo", {})), auth["id"], timestamp))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DomainError("page slug already exists", 409)
            raise
        self.audit(auth["tenant_id"], auth["id"], "page.created", "page", pid)
        return self.page(auth, pid)
    def page_version(self, auth, page_id, data):
        page = self.db.execute("SELECT * FROM pages WHERE id=? AND tenant_id=?", (page_id, auth["tenant_id"])).fetchone()
        if not page: raise DomainError("page not found", 404)
        version = self.db.execute("SELECT COALESCE(MAX(version),0)+1 FROM page_versions WHERE page_id=?", (page_id,)).fetchone()[0]
        self.db.execute("INSERT INTO page_versions VALUES (?,?,?,?,?,?)", (page_id, version, json.dumps(data.get("content", {})), json.dumps(data.get("seo", {})), auth["id"], now()))
        self.db.execute("UPDATE pages SET updated_at=? WHERE id=?", (now(), page_id))
        self.audit(auth["tenant_id"], auth["id"], "page.version.created", "page", page_id, {"version": version})
        return self.page(auth, page_id)
    def page_publish(self, auth, page_id, version=None):
        page = self.db.execute("SELECT * FROM pages WHERE id=? AND tenant_id=?", (page_id, auth["tenant_id"])).fetchone()
        if not page: raise DomainError("page not found", 404)
        version = version or self.db.execute("SELECT MAX(version) FROM page_versions WHERE page_id=?", (page_id,)).fetchone()[0]
        if not self.db.execute("SELECT 1 FROM page_versions WHERE page_id=? AND version=?", (page_id, version)).fetchone(): raise DomainError("page version not found", 404)
        self.db.execute("UPDATE pages SET status='published',published_version=?,updated_at=? WHERE id=?", (version, now(), page_id))
        self.audit(auth["tenant_id"], auth["id"], "page.published", "page", page_id, {"version": version})
        return self.page(auth, page_id)
    def page_rollback(self, auth, page_id, version):
        if not isinstance(version, int) or version < 1: raise DomainError("positive version required")
        return self.page_publish(auth, page_id, version)
    def flags(self, auth):
        return [dict(row) for row in self.db.execute("SELECT name,enabled FROM feature_flags WHERE tenant_id=? ORDER BY name", (auth["tenant_id"],))]
    def flag_set(self, auth, name, enabled):
        if not isinstance(name, str) or not name or not isinstance(enabled, bool): raise DomainError("name and boolean enabled required")
        self.db.execute("INSERT INTO feature_flags VALUES (?,?,?) ON CONFLICT(tenant_id,name) DO UPDATE SET enabled=excluded.enabled", (auth["tenant_id"], name[:100], int(enabled)))
        self.audit(auth["tenant_id"], auth["id"], "feature_flag.updated", "feature_flag", name, {"enabled": enabled})
        return {"name": name[:100], "enabled": enabled}
    def audit_events(self, auth):
        return [dict(row) for row in self.db.execute("SELECT action,resource_type,resource_id,metadata_json,created_at FROM audit_events WHERE tenant_id=? ORDER BY created_at DESC LIMIT 200", (auth["tenant_id"],))]
    def tenant(self, slug):
        row = self.db.execute("SELECT id,name,slug FROM tenants WHERE slug=?", (slug,)).fetchone()
        if not row: raise DomainError("store not found", 404)
        return row
    def public_products(self, slug):
        tenant = self.tenant(slug)
        return [dict(row) for row in self.db.execute("SELECT id,name,slug,price_cents,inventory FROM products WHERE tenant_id=? AND status='active' ORDER BY created_at", (tenant["id"],))]
    def public_page(self, slug, page_slug):
        tenant = self.tenant(slug)
        page = self.db.execute("SELECT * FROM pages WHERE tenant_id=? AND slug=? AND status='published'", (tenant["id"], page_slug)).fetchone()
        if not page: raise DomainError("published page not found", 404)
        version = self.db.execute("SELECT * FROM page_versions WHERE page_id=? AND version=?", (page["id"], page["published_version"])).fetchone()
        result = dict(page); result["content_json"] = version["content_json"]; result["seo_json"] = version["seo_json"]; return result
    def public_cart_create(self, slug):
        tenant = self.tenant(slug); cid = new_id(); self.db.execute("INSERT INTO carts VALUES (?,?,?,?,?)", (cid, tenant["id"], None, "open", now())); return {"id": cid, "store": slug, "items": [], "total_cents": 0}
    def public_cart_add(self, slug, cid, pid, quantity):
        tenant = self.tenant(slug); auth = {"tenant_id": tenant["id"]}; return self.cart_add(auth, cid, pid, quantity)
    def public_cart(self, slug, cid):
        tenant = self.tenant(slug); return self.cart({"tenant_id": tenant["id"]}, cid)
    def public_checkout(self, slug, cid, email, key):
        tenant = self.tenant(slug); owner = self.db.execute("SELECT id FROM users WHERE tenant_id=? AND role='owner' ORDER BY created_at LIMIT 1", (tenant["id"],)).fetchone()
        return self.checkout({"tenant_id": tenant["id"], "id": owner["id"] if owner else None}, cid, email, key)
    def staff_list(self, auth):
        if auth["role"] != "owner": raise DomainError("owner access required", 403)
        return [dict(row) for row in self.db.execute("SELECT id,email,role,created_at FROM users WHERE tenant_id=? ORDER BY created_at", (auth["tenant_id"],))]
    def staff_create(self, auth, data):
        if auth["role"] != "owner": raise DomainError("owner access required", 403)
        email = str(data.get("email", "")).strip().lower(); role = data.get("role", "manager")
        if role not in {"admin", "manager", "support", "fulfillment"} or "@" not in email: raise DomainError("valid email and staff role required")
        try: password = hash_password(str(data.get("password", "")))
        except ValueError as exc: raise DomainError(str(exc))
        uid = new_id()
        try: self.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (uid, auth["tenant_id"], email, password, role, now()))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper(): raise DomainError("email already exists", 409)
            raise
        self.audit(auth["tenant_id"], auth["id"], "staff.created", "user", uid, {"role": role})
        return dict(self.db.execute("SELECT id,email,role,created_at FROM users WHERE id=?", (uid,)).fetchone())
