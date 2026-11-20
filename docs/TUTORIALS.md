# Tutorials

## Register a merchant and create a product

1. `POST /api/auth/register` with `{email,password,store_name}`.
2. Use the returned bearer token in `Authorization: Bearer ...`.
3. `POST /api/products` with `{name,price_cents,inventory}`.
4. Browse with `GET /api/products` and add the product id to a cart.
5. `POST /api/checkout` with `cart_id`, `customer_email`, and an `Idempotency-Key`.

Run `python3 -m unittest discover -s tests -v` to exercise the complete foundation and checkout flow. For a failed request, inspect the JSON `error` field and the audit log; do not inspect or log passwords or payment credentials.
