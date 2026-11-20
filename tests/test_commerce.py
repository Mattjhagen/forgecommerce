import tempfile, unittest
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

if __name__=='__main__': unittest.main()
