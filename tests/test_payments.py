import unittest
from forgecommerce.payments import PaymentError, SandboxPaymentProvider

class PaymentTests(unittest.TestCase):
    def test_sandbox_provider_is_idempotent_and_refundable(self):
        provider=SandboxPaymentProvider(); first=provider.charge('checkout-1',1200); self.assertEqual(provider.charge('checkout-1',1200),first); self.assertEqual(provider.refund(first.reference).status,'refunded')
        with self.assertRaises(PaymentError): provider.charge('',1)

if __name__=='__main__': unittest.main()
