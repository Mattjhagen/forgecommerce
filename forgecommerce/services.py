import json, re
from datetime import datetime, timedelta, timezone
from .security import hash_password, verify_password, token_hash, new_id

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
    def product_create(self, auth, data):
        name = str(data.get("name", "")).strip(); price = data.get("price_cents"); inventory = data.get("inventory", 0)
        if not name or not isinstance(price, int) or price < 0 or not isinstance(inventory, int) or inventory < 0: raise DomainError("name, non-negative integer price_cents and inventory required")
        pid = new_id(); slug = slugify(name)
        try: self.db.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?)", (pid, auth["tenant_id"], name[:200], slug, price, inventory, "active", now()))
        except Exception: raise DomainError("product slug already exists", 409)
        self.audit(auth["tenant_id"], auth["id"], "product.created", "product", pid, {"name": name})
        return self.product(auth, pid)
    def products(self, auth): return [dict(r) for r in self.db.execute("SELECT id,name,slug,price_cents,inventory,status,created_at FROM products WHERE tenant_id=? ORDER BY created_at", (auth["tenant_id"],))]
    def product(self, auth, pid):
        row = self.db.execute("SELECT id,name,slug,price_cents,inventory,status,created_at FROM products WHERE tenant_id=? AND id=?", (auth["tenant_id"], pid)).fetchone()
        if not row: raise DomainError("product not found", 404)
        return dict(row)
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
            self.db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", (oid,auth["tenant_id"],cid,email,cart["total_cents"],"paid_sandbox","unfulfilled",key,now()))
            for item in cart["items"]: self.db.execute("INSERT INTO order_items VALUES (?,?,?,?,?)", (oid,item["product_id"],item["name"],item["quantity"],item["unit_price_cents"]))
            self.db.execute("UPDATE carts SET status='converted',customer_email=? WHERE id=?",(email,cid)); self.db.execute("COMMIT")
        except DomainError: self.db.execute("ROLLBACK"); raise
        except Exception: self.db.execute("ROLLBACK"); raise DomainError("checkout could not be completed",409)
        self.audit(auth["tenant_id"],auth["id"],"order.created","order",oid,{"total_cents":cart["total_cents"]})
        return dict(self.db.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
