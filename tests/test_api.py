import json, tempfile, threading, unittest
from urllib.request import Request, urlopen
from forgecommerce.app import make_server
from forgecommerce.config import Settings

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.NamedTemporaryFile(suffix='.sqlite3')
        self.server=make_server(Settings(db_path=self.tmp.name, host='127.0.0.1', port=0))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_address[1]}'
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.tmp.close()
    def call(self, method, path, body=None, token=None, headers=None):
        h={'Content-Type':'application/json'}; h.update(headers or {})
        if token: h['Authorization']='Bearer '+token
        req=Request(self.base+path,method=method,headers=h,data=json.dumps(body or {}).encode())
        with urlopen(req) as response: return response.status,json.loads(response.read())
    def test_register_product_cart_checkout_over_http(self):
        status, auth=self.call('POST','/api/auth/register',{'email':'api@example.com','password':'long enough password','store_name':'HTTP Shop'})
        self.assertEqual(status,201)
        status, product=self.call('POST','/api/products',{'name':'Pen','price_cents':500,'inventory':2},auth['token'])
        status, cart=self.call('POST','/api/carts',token=auth['token'])
        self.call('POST',f"/api/carts/{cart['id']}/items",{'product_id':product['id'],'quantity':1},auth['token'])
        status, order=self.call('POST','/api/checkout',{'cart_id':cart['id'],'customer_email':'customer@example.com'},auth['token'],{'Idempotency-Key':'http-1'})
        self.assertEqual(status,201); self.assertEqual(order['payment_status'],'paid_sandbox')
        self.assertEqual(self.call('GET','/api/orders',token=auth['token'])[1]['orders'][0]['id'],order['id'])
    def test_health_is_public(self):
        self.assertEqual(self.call('GET','/health')[1]['status'],'ok')

if __name__=='__main__': unittest.main()
