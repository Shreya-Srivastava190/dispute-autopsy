# Dispute Autopsy

An evidence-based chargeback investigation engine. A deterministic rule
engine scores the evidence (payment, order, delivery, refund, support)
and produces a CONTEST / REVIEW / ACCEPT recommendation; an LLM only
*explains* that decision in plain language — it never sets the score
or the outcome itself.

On top of the individual-dispute engine, a set of platform-level
signals (cross-merchant pattern detection, courier fulfillment
anomalies, merchant dispute spikes) surface patterns a single
merchant's own dashboard structurally cannot see, since a single
merchant only ever sees their own transactions. Note: this is
demonstrated at small scale (25 seed disputes with deliberately planted
patterns, low flagging thresholds) — it's a proof of the
pattern-detection architecture, not a claim about production-scale
accuracy; see Limitations below.

## Features

- **Evidence scoring engine** (`investigator.py`) — deterministic,
  auditable, weighted scoring across payment/order/delivery/address/
  signature/refund/support signals
- **AI narrative layer** (`ai_investigator.py`) — reads the free-text
  customer/support note and produces a claim-vs-evidence contradiction
  analysis, not just a paraphrase of the structured facts. Falls back
  to a local deterministic report generator if no LLM key is set.
- **Cross-merchant network risk** (`network_risk.py`) — flags repeat
  customers, repeat merchants, and customers disputing multiple
  distinct merchants
- **Courier/fulfillment anomaly detection** (`courier_risk.py`) — flags
  couriers with an elevated non-delivery rate across merchants
- **Merchant dispute spike detection** (`merchant_spike.py`) — flags
  temporal clustering of disputes against one merchant
- **Relationship graph** (`risk_graph.py`) — visualizes a customer's
  disputes across merchants, shown only when there's more than one
  relationship to compare
- **Triage / Action Queue** (`triage.py`) — priority-sorted queue by
  amount × deadline urgency × evidence gap (a documented demo
  heuristic, not a calibrated model)
- **Seed dataset generator** (`data/generate_seed_disputes.py`) — 25
  reproducible demo disputes with deliberately planted, labeled
  patterns (cross-merchant serial disputer, merchant spike, courier
  concentration) so the platform-intelligence views have something
  real to show. Re-run with `python data/generate_seed_disputes.py`.
- **Scenario Lab** (`simulation.py`) — an in-memory sandbox to add a
  synthetic dispute and watch the risk signals update live; never
  touches real seed data, resets on server restart
- **Evaluation harness** (`evaluate.py`, `eval_data.py`) — measured
  precision/recall/F1 on a held-out synthetic test set, see
  `EVALUATION.md`
- **Real Razorpay webhook receiver** (`razorpay_webhook.py`) — see
  "Razorpay Integration" below

## Run it

**Backend**
```
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env             # then add your GROQ_API_KEY (free at console.groq.com — optional, falls back to a local report generator without it)
uvicorn main:app --reload
```

**Frontend**
```
cd frontend
npm install
cp .env.local.example .env.local   # edit if your backend isn't on 127.0.0.1:8000
npm run dev
```

Open http://localhost:3000. Run `python backend/test_backend.py` (with
the backend running) for an automated smoke test across every endpoint.

## AI provider

This uses **Groq** (free tier, OpenAI-compatible endpoint) instead of
OpenAI — get a key at https://console.groq.com and put it in
`backend/.env` as `GROQ_API_KEY=...`. Don't commit that file. Without
a key, the app still works fully — it just uses a local, rule-based
report generator instead of an LLM-written narrative.

## Razorpay Integration

`POST /webhook/razorpay` is a real webhook receiver for Razorpay's
`payment.dispute.created` event, built against Razorpay's documented
shapes (not guessed):

- **Signature verification**: HMAC-SHA256 over the raw request body,
  keyed with the webhook secret, checked against the
  `X-Razorpay-Signature` header — Razorpay's actual documented scheme.
  Requires `RAZORPAY_WEBHOOK_SECRET` to be set; the endpoint refuses
  everything if it isn't, rather than silently skipping verification.
- **Payload mapping**: pulls real fields from Razorpay's dispute
  entity (`id`, `payment_id`, `amount`, `currency`, `reason_code`,
  `respond_by`, `phase`, `evidence.summary`, etc.) into Dispute
  Autopsy's internal format, then runs it through the same evidence
  engine as everything else.

**Honest limitation**: Razorpay's dispute webhook gives you payment-
level facts but does *not* include delivery/fulfillment data (was it
delivered, is there a signature, does the address match) — that lives
in the merchant's own order management system, not Razorpay's. Those
fields are mapped as `"unconfirmed"` rather than invented. A real
integration would correlate this webhook with the merchant's OMS to
complete the evidence picture; that correlation step doesn't exist
here since there's no real OMS to connect to in a hackathon prototype.

**Also handled**: Razorpay's real payloads frequently omit optional
fields like `payment.entity.created_at` — the mapping falls back to
the dispute's own `created_at` when that happens, and
`investigator.build_timeline()` itself drops any event with no
timestamp rather than crashing a sort on it, so a payload missing
optional fields degrades gracefully instead of 500ing. Covered by an
automated check in `test_backend.py`.

Test it locally:
```bash
# Requires RAZORPAY_WEBHOOK_SECRET set in backend/.env
python -c "
import hmac, hashlib, json
secret = 'your_test_secret'
body = json.dumps({'event': 'payment.dispute.created', 'account_id': 'acc_test', 'payload': {...}}).encode()
sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
print('X-Razorpay-Signature:', sig)
"
# then curl -X POST http://127.0.0.1:8000/webhook/razorpay -H "X-Razorpay-Signature: <sig>" -d '<body>'
```

## Evaluation

Per a "measured precision and recall on a held-out test set"
requirement: `EVALUATION.md` documents the full methodology and
results, including a genuine before/after threshold recalibration with
disclosed trade-offs. Run `python backend/evaluate.py` to reproduce it
yourself, or hit `GET /evaluation` / `GET /evaluation/multi-seed` on
the running API.

## Limitations & Next Steps

Said plainly, in one place, rather than only scattered across code
comments:

- **Synthetic data only.** No real historical dispute outcomes were
  available for this prototype. The evaluation set (`eval_data.py`) is
  synthetic, with documented, deliberately-injected noise — not a
  claim about real-world accuracy.
- **Rule-based core, by design.** The scoring engine is deterministic
  and auditable rather than a trained model — a decision made for
  explainability, not a limitation of time. See `EVALUATION.md` for
  why an opaque model wasn't the right trade here.
- **Small seed dataset, though larger than a single hand-written
  example.** `data/generate_seed_disputes.py` builds 25 disputes with
  deliberately planted patterns (a cross-merchant serial disputer, a
  4-dispute merchant spike, a courier flagged across 11 disputes and
  multiple merchants) so the Dashboard/Triage/network-risk views have
  enough volume to demonstrate the architecture. The flagging
  thresholds (e.g. "2 disputes" triggers a network-risk flag) are
  still intentionally low relative to real platform volume. A
  production version
  processing real volume would need thresholds calibrated against
  actual base rates, not fixed small integers.
- **No production security hardening.** CORS defaults to an open
  origin list unless `FRONTEND_ORIGINS` is set; there's an optional,
  opt-in API key check on write endpoints (`DEMO_API_KEY`) but no full
  auth system — appropriate for a hackathon demo, not a claim of
  production readiness.
- **Razorpay integration is a real webhook receiver, not a full
  production integration.** It correctly verifies and parses
  Razorpay's actual payload shape, but doesn't (and can't, without a
  real merchant's order system) fill in delivery/fulfillment evidence
  automatically.

**Honest next step if this moved past prototype stage**: retrospective
validation against real historical dispute resolutions, and a real
OMS correlation step for the webhook path.