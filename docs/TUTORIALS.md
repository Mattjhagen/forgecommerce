# Tutorials

## Register a merchant and create a product

1. `POST /api/auth/register` with `{email,password,store_name}`.
2. Use the returned bearer token in `Authorization: Bearer ...`.
3. `POST /api/products` with `{name,price_cents,inventory}`.
4. Browse with `GET /api/products` and add the product id to a cart.
5. `POST /api/checkout` with `cart_id`, `customer_email`, and an `Idempotency-Key`.

Run `python3 -m unittest discover -s tests -v` to exercise the complete foundation and checkout flow. For a failed request, inspect the JSON `error` field and the audit log; do not inspect or log passwords or payment credentials.

## Publish a versioned page

1. `POST /api/pages` with a title and JSON content creates draft version 1.
2. `POST /api/pages/{page_id}/versions` stores a new immutable version.
3. `POST /api/pages/{page_id}/publish` with an optional version selects the live version.
4. `GET /api/pages/{page_id}` returns the page and its version history.

The page content is stored as JSON so a visual editor can evolve its section schema without coupling persistence to one frontend implementation. Test this with `test_page_versions_publish_and_flags`.
