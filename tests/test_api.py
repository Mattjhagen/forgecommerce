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
    def test_storefront_and_editor_html_are_reachable(self):
        _, auth=self.call('POST','/api/auth/register',{'email':'html@example.com','password':'long enough password','store_name':'HTML Shop'})
        req=Request(self.base+'/store/html-shop',method='GET')
        with urlopen(req) as response:
            page=response.read().decode(); self.assertIn('HTML Shop',page); self.assertIn('Add to cart',page)
        req=Request(self.base+'/editor',method='GET')
        with urlopen(req) as response:
            editor=response.read().decode(); self.assertIn('Visual editor',editor); self.assertIn('/api/pages',editor); self.assertIn('Rollback to version 1',editor)
    def test_guest_storefront_browse_cart_and_checkout(self):
        _, auth=self.call('POST','/api/auth/register',{'email':'merchant@example.com','password':'long enough password','store_name':'Guest Shop'})
        _, product=self.call('POST','/api/products',{'name':'Hat','price_cents':1800,'inventory':1},auth['token'])
        _, listing=self.call('GET','/store/guest-shop/products')
        self.assertEqual(listing['products'][0]['id'],product['id'])
        _, cart=self.call('POST','/store/guest-shop/carts')
        self.call('POST','/store/guest-shop/carts/items',{'cart_id':cart['id'],'product_id':product['id'],'quantity':1})
        _, order=self.call('POST','/store/guest-shop/carts/checkout',{'cart_id':cart['id'],'customer_email':'guest@example.com'},headers={'Idempotency-Key':'guest-1'})
        self.assertEqual(order['payment_status'],'paid_sandbox')
    def test_public_search_and_sitemap(self):
        _, auth=self.call('POST','/api/auth/register',{'email':'seo@example.com','password':'long enough password','store_name':'SEO Shop'})
        _, product=self.call('POST','/api/products',{'name':'Blue Shoes','price_cents':3000,'inventory':4},auth['token'])
        result=self.call('GET','/store/seo-shop/search?q=shoes')[1]; self.assertEqual(result['products'][0]['id'],product['id'])
        req=Request(self.base+'/store/seo-shop/sitemap.xml',method='GET')
        with urlopen(req) as response: xml=response.read().decode(); self.assertIn("sitemaps.org",xml); self.assertIn('blue-shoes',xml)
    def test_published_page_seo_is_rendered_publicly(self):
        _, auth=self.call('POST','/api/auth/register',{'email':'page-seo@example.com','password':'long enough password','store_name':'Page SEO'})
        _, page=self.call('POST','/api/pages',{'title':'About','content':{'sections':[{'heading':'About us'}]},'seo':{'title':'About Page','description':'A safe description'}},auth['token'])
        self.call('POST',f"/api/pages/{page['id']}/publish",{},auth['token'])
        req=Request(self.base+'/store/page-seo/page/about',method='GET')
        with urlopen(req) as response: body=response.read().decode(); self.assertIn('<title>About Page</title>',body); self.assertIn('About us',body); self.assertIn('A safe description',body)
        _, unsafe=self.call('POST','/api/pages',{'title':'Safe','content':{'sections':[{'heading':'<script>alert(1)</script>'}]},'seo':{'title':'<script>x</script>','description':'"><script>x</script>'}},auth['token'])
        self.call('POST',f"/api/pages/{unsafe['id']}/publish",{},auth['token'])
        req=Request(self.base+'/store/page-seo/page/safe',method='GET')
        with urlopen(req) as response:
            body=response.read().decode(); self.assertNotIn('<title><script>',body); self.assertIn('&lt;script&gt;x&lt;/script&gt;',body)
    def test_page_translation_locale_overrides_default_and_falls_back(self):
        _, auth=self.call('POST','/api/auth/register',{'email':'locale@example.com','password':'long enough password','store_name':'Locale Shop'})
        _, page=self.call('POST','/api/pages',{'title':'Welcome','content':{'sections':[{'heading':'Welcome'}]},'seo':{'title':'Welcome'}},auth['token'])
        self.call('POST',f"/api/pages/{page['id']}/translations",{'locale':'fr-FR','content':{'sections':[{'heading':'Bienvenue'}]},'seo':{'title':'Bienvenue'}},auth['token'])
        self.call('POST',f"/api/pages/{page['id']}/publish",{},auth['token'])
        req=Request(self.base+'/store/locale-shop/page/welcome?lang=fr-FR',method='GET')
        with urlopen(req) as response: self.assertIn('Bienvenue',response.read().decode())
        req=Request(self.base+'/store/locale-shop/page/welcome?lang=de',method='GET')
        with urlopen(req) as response: self.assertIn('Welcome',response.read().decode())

if __name__=='__main__': unittest.main()
