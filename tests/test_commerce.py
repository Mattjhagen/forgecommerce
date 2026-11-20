import hashlib, hmac, json, tempfile, unittest
from forgecommerce.db import connect
from forgecommerce.services import Commerce, DomainError

class CommerceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.NamedTemporaryFile(suffix='.sqlite3'); self.c=Commerce(connect(self.tmp.name))
        self.a=self.c.register('owner-a@example.com','correct horse battery staple','Alpha Store')
        self.b=self.c.register('owner-b@example.com','correct horse battery staple','Beta Store')
        self.aa=self.c.authenticate(self.a['token']); self.bb=self.c.authenticate(self.b['token'])
    def tearDown(self): self.tmp.close()
    def test_tenant_isolation_and_inventory(self):
        p=self.c.product_create(self.aa, {'name':'Mug','price_cents':1200,'inventory':3})
        self.assertEqual(len(self.c.products(self.bb)),0)
        with self.assertRaises(DomainError): self.c.product(self.bb,p['id'])
        self.assertEqual(self.c.inventory_update(self.aa,p['id'],5)['inventory'],5)
    def test_checkout_idempotency_and_refund(self):
        p=self.c.product_create(self.aa, {'name':'Book','price_cents':2500,'inventory':2})
        cart=self.c.cart_create(self.aa); self.c.cart_add(self.aa,cart['id'],p['id'],1)
        order=self.c.checkout(self.aa,cart['id'],'buyer@example.com','order-1')
        again=self.c.checkout(self.aa,cart['id'],'buyer@example.com','order-1')
        self.assertEqual(order['id'],again['id']); self.assertEqual(self.c.product(self.aa,p['id'])['inventory'],1)
        self.assertEqual(self.c.refund(self.aa,order['id'])['payment_status'],'refunded')
    def test_page_versions_publish_and_flags(self):
        page=self.c.page_create(self.aa,{'title':'Home','content':{'sections':['hero']}})
        page=self.c.page_version(self.aa,page['id'],{'content':{'sections':['hero','products']},'seo':{'title':'Alpha'}})
        self.assertEqual(len(page['versions']),2)
        self.assertEqual(self.c.page_publish(self.aa,page['id'],1)['published_version'],1)
        self.assertEqual(self.c.page_rollback(self.aa,page['id'],2)['published_version'],2)
        self.assertEqual(self.c.flag_set(self.aa,'new_editor',True)['enabled'],True)
        self.assertEqual(self.c.flags(self.bb),[])
    def test_invalid_password_and_cross_tenant_cart_are_rejected(self):
        with self.assertRaises(DomainError): self.c.login('owner-a@example.com','wrong password')
        cart=self.c.cart_create(self.aa)
        with self.assertRaises(DomainError): self.c.cart(self.bb,cart['id'])
    def test_owner_can_manage_staff_but_staff_cannot(self):
        staff=self.c.staff_create(self.aa,{'email':'manager@alpha.example','password':'manager password','role':'manager'})
        self.assertEqual(staff['role'],'manager'); self.assertEqual(len(self.c.staff_list(self.aa)),2)
        staff_auth=self.c.authenticate(self.c.login('manager@alpha.example','manager password')['token'])
        with self.assertRaises(DomainError): self.c.staff_list(staff_auth)
    def test_customer_record_order_search_and_fulfillment_status(self):
        p=self.c.product_create(self.aa, {'name':'Socks','price_cents':900,'inventory':2})
        cart=self.c.cart_create(self.aa); self.c.cart_add(self.aa,cart['id'],p['id'],1)
        order=self.c.checkout(self.aa,cart['id'],'buyer@search.example','search-1')
        self.assertEqual(self.c.customers(self.aa)[0]['order_count'],1)
        self.assertEqual(len(self.c.orders(self.aa,'search.example')),1)
        self.assertEqual(self.c.order_status(self.aa,order['id'],'fulfilled')['fulfillment_status'],'fulfilled')
    def test_variants_are_tenant_scoped_and_sku_unique(self):
        p=self.c.product_create(self.aa, {'name':'Tee','price_cents':2000,'inventory':0})
        variant=self.c.variant_create(self.aa,p['id'],{'sku':'TEE-RED-M','name':'Red / Medium','price_cents':2200,'inventory':4})
        self.assertEqual(self.c.product(self.aa,p['id'])['variants'][0]['sku'],'TEE-RED-M')
        with self.assertRaises(DomainError): self.c.product(self.bb,p['id'])
        with self.assertRaises(DomainError): self.c.variant_create(self.aa,p['id'],{'sku':'TEE-RED-M','name':'Duplicate','price_cents':1,'inventory':1})
    def test_collections_are_tenant_scoped(self):
        p=self.c.product_create(self.aa, {'name':'Cap','price_cents':1500,'inventory':2})
        collection=self.c.collection_create(self.aa,{'name':'Summer Picks'})
        self.c.collection_add(self.aa,collection['id'],p['id'])
        self.assertEqual(self.c.collection(self.aa,collection['id'])['products'][0]['id'],p['id'])
        with self.assertRaises(DomainError): self.c.collection(self.bb,collection['id'])
    def test_analytics_and_admin_health_are_scoped_to_owner(self):
        p=self.c.product_create(self.aa, {'name':'Analytics Item','price_cents':1000,'inventory':1})
        cart=self.c.cart_create(self.aa); self.c.cart_add(self.aa,cart['id'],p['id'],1); self.c.checkout(self.aa,cart['id'],'metrics@example.com','metrics-1')
        metrics=self.c.analytics(self.aa); self.assertEqual(metrics['orders'],1); self.assertEqual(metrics['gross_cents'],1000); self.assertEqual(self.c.admin_health(self.aa)['status'],'ok')
        staff=self.c.staff_create(self.aa,{'email':'metrics-staff@example.com','password':'staff password','role':'manager'})
        staff_auth=self.c.authenticate(self.c.login('metrics-staff@example.com','staff password')['token'])
        with self.assertRaises(DomainError): self.c.admin_health(staff_auth)
        usage=self.c.usage(self.aa); self.assertEqual(usage['plan'],'starter'); self.assertEqual(usage['usage']['products'],1)
        with self.assertRaises(DomainError): self.c.usage(staff_auth)
    def test_api_key_authentication_and_signed_webhook_delivery(self):
        key=self.c.api_key_create(self.aa,'integration'); api_auth=self.c.authenticate_api_key(key['key']); self.assertEqual(api_auth['tenant_id'],self.aa['tenant_id'])
        product=self.c.product_create(self.aa,{'name':'Webhook Item','price_cents':700,'inventory':1}); hook=self.c.webhook_create(self.aa,{'url':'https://example.test/webhook','events':['order.created']})
        cart=self.c.cart_create(self.aa); self.c.cart_add(self.aa,cart['id'],product['id'],1); order=self.c.checkout(self.aa,cart['id'],'hook@example.com','hook-1')
        deliveries=self.c.webhook_deliveries(self.aa,hook['id']); self.assertEqual(deliveries[0]['event_type'],'order.created'); self.assertEqual(deliveries[0]['signature'],hmac.new(hook['secret'].encode(),deliveries[0]['payload_json'].encode(),hashlib.sha256).hexdigest()); self.assertEqual(json.loads(deliveries[0]['payload_json'])['id'],order['id'])
        self.c.api_key_revoke(self.aa,key['id'])
        with self.assertRaises(DomainError): self.c.authenticate_api_key(key['key'])
    def test_sandbox_subscription_changes_update_limits(self):
        self.assertEqual(self.c.subscription(self.aa)['plan'],'starter')
        self.assertEqual(self.c.subscription_change(self.aa,'growth')['status'],'active'); self.assertEqual(self.c.usage(self.aa)['limits']['product_limit'],1000)
        staff=self.c.staff_create(self.aa,{'email':'billing-staff@example.com','password':'staff password','role':'manager'}); staff_auth=self.c.authenticate(self.c.login('billing-staff@example.com','staff password')['token'])
        with self.assertRaises(DomainError): self.c.subscription_change(staff_auth,'scale')
    def test_platform_admin_provisions_lists_and_suspends_tenants(self):
        import tempfile
        db=tempfile.NamedTemporaryFile(suffix='.sqlite3'); platform=Commerce(connect(db.name),platform_admin_token='platform-secret')
        provisioned=platform.platform_provision('platform-secret',{'email':'platform@example.com','password':'long enough password','store_name':'Platform Shop'})
        self.assertEqual(platform.platform_tenants('platform-secret')[0]['status'],'active')
        with self.assertRaises(DomainError): platform.platform_tenants('wrong')
        tenant=platform.tenant('platform-shop'); user=platform.login('platform@example.com','long enough password'); self.assertEqual(platform.platform_set_status('platform-secret','platform-shop','suspended')['status'],'suspended')
        with self.assertRaises(DomainError): platform.authenticate(user['token'])
        self.assertEqual(platform.platform_migrations('platform-secret')['pending'],0); self.assertEqual(platform.platform_migrations('platform-secret',True)['current'],1)
        db.close()

if __name__=='__main__': unittest.main()
