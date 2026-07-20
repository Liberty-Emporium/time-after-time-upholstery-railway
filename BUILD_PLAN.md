# Davis Carpet CRM — Build Plan

Client: Bryan Davis (owner, also a minister). Job codename "Mingo".
Repo: Liberty-Emporium/davis-carpet (private). Railway project: "Davis Carpets" (4f05a6fc).

## KEY DISCOVERY
The repo is NOT a basic HTML site. It is ALREADY a Django project with:
- `dashboard` app: SiteConfig (OpenRouter AI key/model/system prompt), ChatMessage (AI chat history)
- `gallery` app: Photo (image upload, categories, featured, sort), BusinessInfo (name/phone/address/hours/about — editable)
- Templates: login, home, upload, chat, users, settings, gallery/home
- Railway config (railway.toml, Procfile, nixpacks) already present
- AI chatbot already wired to OpenRouter

This means much of the foundation exists. We EXTEND, not rebuild.

## PHASE 1 — Landing page + login (FIRST, per Jay)
- Turn gallery/home.html into the public LANDING PAGE
- Apply changes from Bryan's note:
  - Header flooring types: CARPET · HARDWOOD · LVP
  - Phone: 336-653-4506 (Bryan's cell) [CONFIRM: paper says 4506, Jay earlier said 4906]
  - "By Appointment"
  - "2 Convenient Locations" / "Your Place or Ours" tagline
- Recolor theme from Telegram blue -> RED & BLACK, nice style
- Add a LOGIN entry point on the landing page
- Hero image (Jay providing)

## PHASE 2 — CRM core (business side)
Admin user manages everything. Business AI knows ONLY business context.
- Books / bookkeeping
- Inventory
- Customers
- Invoices
- Work orders
- Purchases from vendors
- Employees + their time
- Editable About text (self-service)
- Gallery: upload + delete photos (100+) — partially exists via Photo model
- Appointment booking (customers request; Bryan sees them in CRM)

## PHASE 3 — Ministry side (separate nav + separate AI)
Ministry AI knows ONLY ministry context (NOT business).
- Add/remove files
- AI analyzes files
- AI gives reasoning/ideas on those files
- AI creates PowerPoint presentations (for screen display)
- PPTX includes AI-generated images
- Possible ElevenLabs voice integration

## ARCHITECTURE NOTE — Two AIs
- Business AI: system prompt + context = business data only
- Ministry AI: system prompt + context = ministry files/content only
- Keep them structurally separate (separate SiteConfig-style config, separate chat sessions)

## STACK
Django 5, Pillow, gunicorn, whitenoise (current). Will add: python-pptx, OpenRouter image gen, possibly elevenlabs.

## RULES
- Data correctness #1
- Build once, don't churn working features
- Small chunks, one step at a time
- Confirm phone number before shipping
