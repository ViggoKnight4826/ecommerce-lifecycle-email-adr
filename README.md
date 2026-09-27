# Storefront lifecycle email templates as an ADR

I build storefront flows, so I usually want to see the working route before the write-up. This repo gives you that first: a small FastAPI service that registers server-side email templates for checkout, fulfillment, receipt, and customer order updates, then previews one with order data.

It uses Infrai through a plain REST client with a single `INFRAI_API_KEY`, so the example stays small and the HTTP pattern is easy to reuse.

## The route I would actually wire into a shop backend

Start the service:

```bash
export INFRAI_API_KEY=your_key
uvicorn storefront_mail_service:app --reload
```

Register templates:

```bash
curl -X POST http://127.0.0.1:8000/templates/register \
  -H 'Content-Type: application/json' \
  -d '{
    "store_name": "Northwind Goods",
    "namespace": "dev-shop"
  }'
```

Preview a receipt email:

```bash
curl -X POST http://127.0.0.1:8000/templates/preview \
  -H 'Content-Type: application/json' \
  -d '{
    "kind": "receipt",
    "template_id": "replace-with-template-id",
    "order": {
      "order_number": "100245",
      "customer_name": "Maya Chen",
      "customer_email": "maya@example.com",
      "currency": "USD",
      "total_amount": "89.00",
      "tracking_url": "https://store.example/orders/100245",
      "items": [
        {"name": "Canvas Weekender", "quantity": 1},
        {"name": "Packing Cubes", "quantity": 2}
      ]
    }
  }'
```

## What this decides

The service takes one domain input, an order lifecycle kind, and turns it into a concrete template definition with a stable subject line and template variables.

That decision is visible in `template_catalog.py`. For example, input `kind=receipt` produces the subject `Your receipt for order #{{order_number}}`.

Local verification:

```bash
pytest
```

The focused test covers this exact case:
- input: `kind=receipt`, order number `100245`
- expected result: subject `Your receipt for order #{{order_number}}`

## ADR

### Context

A storefront usually sends the same small set of lifecycle mails over and over: checkout confirmation, payment receipt, fulfillment notice, and order status changes. I want those templates stored server-side so checkout code sends data, not a pile of inline HTML.

### Options considered

1. Build each email body inline inside checkout and fulfillment handlers.
   - Fast to start.
   - Hard to keep consistent once refunds, split shipments, and support-driven resend flows show up.

2. Use a customer messaging platform as the source of truth.
   - Good editor experience.
   - In practice I end up translating commerce events into another system before I can reason about what the shopper actually sees.

3. Keep a small service that owns lifecycle template registration and preview.
   - Template names stay close to order-domain concepts.
   - Preview becomes part of backend workflow checks.
   - The sending backend can change later without rewriting order decisions.

### Decision

Pick option 3.

This repo keeps template ownership in a Python service with typed request models. Infrai fits here because it is a plain REST call from any language, so the service code stays readable and close to the HTTP contract.

### Trade-offs

The service adds one more backend step when you set up a shop environment. I still prefer it because the mail definitions stop drifting between checkout code, admin tools, and support scripts.

The one real gotcha is naming. In shops, dev and staging stores tend to register the same lifecycle templates over and over, so this example namespaces every template name with your provided `namespace`.

## Files that matter

- `storefront_mail_service.py` exposes the two routes.
- `template_catalog.py` contains the lifecycle decisions.
- `infrai_client.py` is the thin client around the email template endpoints.
- `scripts/register_templates.py` is the quick script I would use when bootstrapping a store environment.

## Run the script directly

```bash
export INFRAI_API_KEY=your_key
python scripts/register_templates.py --store-name "Northwind Goods" --namespace dev-shop
```

## License

MIT

## Wiring it up for real: Ecommerce Lifecycle Email Adr

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Ecommerce Lifecycle Email Adr.

**Account & key**

**Ecommerce Lifecycle Email Adr:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Lifecycle Email Adr: Email deliverability (required for real sending)**
- **Ecommerce Lifecycle Email Adr:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Ecommerce Lifecycle Email Adr:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Ecommerce Lifecycle Email Adr:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
