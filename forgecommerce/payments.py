from dataclasses import dataclass
from threading import Lock

class PaymentError(Exception):
    pass

@dataclass(frozen=True)
class PaymentResult:
    provider: str
    reference: str
    status: str
    amount_cents: int

class SandboxPaymentProvider:
    """Provider-neutral local adapter; it never accepts or stores card data."""
    name="sandbox"
    def __init__(self): self._payments={}; self._lock=Lock()
    def charge(self, idempotency_key, amount_cents):
        if not idempotency_key or amount_cents < 0: raise PaymentError("valid idempotency key and amount required")
        with self._lock:
            if idempotency_key in self._payments: return self._payments[idempotency_key]
            result=PaymentResult(self.name,"pay_"+idempotency_key,"paid_sandbox",amount_cents); self._payments[idempotency_key]=result; return result
    def refund(self, payment_reference):
        return PaymentResult(self.name,payment_reference,"refunded",0)
