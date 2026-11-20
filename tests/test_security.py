import unittest
from forgecommerce.security import RateLimiter

class SecurityTests(unittest.TestCase):
    def test_rate_limiter_bounds_requests_and_expires_window(self):
        limiter=RateLimiter(limit=2,window_seconds=10)
        self.assertTrue(limiter.allow('client',0)); self.assertTrue(limiter.allow('client',1)); self.assertFalse(limiter.allow('client',2)); self.assertTrue(limiter.allow('client',11))

if __name__=='__main__': unittest.main()
