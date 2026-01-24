# Stripe Integration - Quick Start

## In 5 Minutes

### Step 1: Get Stripe Keys (2 min)
```
1. Go to stripe.com → Sign up/Login
2. Developers → API keys
3. Copy: Secret Key (sk_test_...) & Publishable Key (pk_test_...)
```

### Step 2: Add to Environment (1 min)
```bash
# Backend/.env
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx  # Get from Stripe CLI
FRONTEND_URL=http://localhost:3000

# frontend/.env
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Install & Run (2 min)
```bash
# Option A: Automated
./setup_stripe.sh

# Option B: Manual
cd Backend && pip install stripe==11.3.0
cd ../frontend && npm install @stripe/stripe-js @stripe/react-stripe-js
psql -d your_db -f Backend/migrations/add_stripe_fields.sql
```

## Test It

```bash
# Terminal 1: Backend
cd Backend && python main.py

# Terminal 2: Stripe webhooks
stripe listen --forward-to localhost:8000/api/payments/webhook

# Terminal 3: Frontend
cd frontend && npm run dev
```

Visit: `http://localhost:3000/pricing`

**Test Card:** 4242 4242 4242 4242 | 12/34 | 123 | 12345

## What You Can Do Now

- View pricing plans at `/pricing`
- Complete a test subscription
- View subscription in `/settings`
- Manage subscription via Stripe portal
- Webhooks handle payment events automatically

## File Structure

```
Backend/
├── routers/payments.py          # NEW: Payment API
├── migrations/add_stripe_fields.sql  # NEW: DB migration
├── requirements.txt             # MODIFIED: Added stripe
└── main.py                      # MODIFIED: Registered router

frontend/
├── src/app/
│   ├── pricing/page.tsx                # NEW: Pricing page
│   ├── payment/success/page.tsx        # NEW: Success page
│   ├── payment/cancel/page.tsx         # NEW: Cancel page
│   └── components/
│       ├── SubscriptionManager.tsx     # NEW: Subscription widget
│       └── dashboard/SettingsView.tsx  # MODIFIED: Added subscription
└── package.json                 # MODIFIED: Added Stripe libs
```

## Pricing Plans

| Plan | Price | Perfect For |
|------|-------|-------------|
| Starter | $40/mo | Small teams (up to 10) |
| Professional | TBD | Growing teams (up to 50) |
| Enterprise | TBD | Large organizations (unlimited) |

## API Endpoints

```
GET  /api/payments/plans                    # Get pricing
POST /api/payments/create-checkout-session  # Start payment
GET  /api/payments/subscription             # Get status
POST /api/payments/create-portal-session    # Manage subscription
POST /api/payments/webhook                  # Stripe events
```

## Environment Variables Checklist

**Backend:**
- [ ] `STRIPE_SECRET_KEY` - From Stripe Dashboard
- [ ] `STRIPE_WEBHOOK_SECRET` - From Stripe CLI or Dashboard
- [ ] `FRONTEND_URL` - Your frontend URL

**Frontend:**
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - From Stripe Dashboard
- [ ] `NEXT_PUBLIC_API_URL` - Your backend URL

## Production Checklist

Before going live:
- [ ] Replace test keys with live keys
- [ ] Set up production webhook endpoint (HTTPS required)
- [ ] Test complete payment flow
- [ ] Configure webhook events in Stripe Dashboard
- [ ] Enable Stripe Radar for fraud detection
- [ ] Set up payment failure notifications
- [ ] Test subscription cancellation
- [ ] Test plan upgrades/downgrades

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Webhook not working | Use `stripe listen --forward-to localhost:8000/api/payments/webhook` |
| Payment fails | Check Stripe Dashboard → Developers → Logs |
| Can't see plans | Verify `NEXT_PUBLIC_API_URL` is correct |
| Auth error | Ensure JWT token is in localStorage |
| DB error | Run migration: `psql -d db -f Backend/migrations/add_stripe_fields.sql` |

## Need Help?

- **Detailed Guide:** See `STRIPE_INTEGRATION_GUIDE.md`
- **Full Summary:** See `STRIPE_INTEGRATION_SUMMARY.md`
- **Automated Setup:** Run `./setup_stripe.sh`
- **Stripe Docs:** https://stripe.com/docs
- **Test Cards:** https://stripe.com/docs/testing

---

**Status:** Ready to test  
**Time to integrate:** ~5 minutes  
**Version:** 1.0.0
