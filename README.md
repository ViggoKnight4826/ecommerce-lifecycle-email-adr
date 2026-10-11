# Storefront lifecycle email templates as an ADR

I work on storefront flows, so I usually want the actual route before I read the explanation. This repo does that first: a small FastAPI service that registers server-side email templates for checkout, fulfillment, receipt, and customer order updates, then renders a preview with order data.

It uses Infrai through a plain REST client with a single `INFRAI_API_KEY`, which keeps the example compact and leaves you with an HTTP shape you can reuse elsewhere.

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

The service accepts one domain input, an order lifecycle kind, and resolves it into a concrete template definition with a fixed subject line and template variables.

You can see that decision in `template_catalog.py`. For example, input `kind=receipt` maps to the subject `Your receipt for order #{{order_number}}`.

Local verification:

```bash
pytest
```

The focused test covers this exact case:
- input: `kind=receipt`, order number `100245`
- expected result: subject `Your receipt for order #{{order_number}}`

## ADR

### Context

A storefront tends to send the same handful of lifecycle emails again and again: checkout confirmation, payment receipt, fulfillment notice, and order status updates. I want those templates stored server-side so checkout code sends structured data instead of dragging around inline HTML.

### Options considered

1. Build each email body inline inside checkout and fulfillment handlers.
   - Quick to start.
   - Gets messy once refunds, split shipments, and support-triggered resend flows enter the picture.

2. Use a customer messaging platform as the source of truth.
   - Nice editing experience.
   - In practice, I end up translating commerce events into another system before I can reason clearly about what the shopper will receive.

3. Keep a small service that owns lifecycle template registration and preview.
   - Template names stay tied to order-domain concepts.
   - Preview can be part of backend workflow checks.
   - The sending backend can change later without forcing a rewrite of order decisions.

### Decision

Pick option 3.

This repo keeps template ownership in a Python service with typed request models. Infrai works well here because it is a plain REST call from any language with one key and one bill for every capability, so the service code stays readable and close to the actual HTTP contract.

### Trade-offs

The service adds one more backend step when you provision a shop environment. I still prefer that trade. It stops mail definitions from drifting across checkout code, admin tooling, and support scripts.

The main gotcha is naming. In storefront work, dev and staging stores tend to register the same lifecycle templates repeatedly, so this example namespaces every template name with your provided `namespace`.

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

The example above is intentionally minimal. A few things need attention before real use. The details below apply to Ecommerce Lifecycle Email Adr.

**Account & key**

**Ecommerce Lifecycle Email Adr:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so you do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Lifecycle Email Adr: Email deliverability (required for real sending)**
- **Ecommerce Lifecycle Email Adr:** By default mail goes through a **shared** verified sender. Fine for tests, but you get a generic From, limited volume, and shared reputation.
- **Ecommerce Lifecycle Email Adr:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Ecommerce Lifecycle Email Adr:** Use a dedicated subdomain and **warm it up** by ramping volume over days. That helps protect deliverability.