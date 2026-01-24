# Stripe Payment Integration Guide for Kogna AI

This guide will help you complete the Stripe payment integration for Kogna AI.

## What's Been Implemented

### Backend (FastAPI)
- Stripe payment router (`/Backend/routers/payments.py`)
- Pricing plans configuration (Starter, Professional, Enterprise)
- Checkout session creation
- Webhook handling for payment events
- Subscription management endpoints
- Customer portal integration

### Frontend (Next.js)
- Pricing page (`/pricing`)
- Payment success page (`/payment/success`)
- Payment cancel page (`/payment/cancel`)
- Subscription manager component
- Stripe React components added to package.json

### Database
- Migration script for adding Stripe fields

## Setup Instructions

### 1. Install Dependencies

#### Backend
```bash
cd Backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### 2. Configure Stripe Account

1. **Create a Stripe Account**
   - Go to [https://stripe.com](https://stripe.com)
   - Sign up or log in

2. **Get Your API Keys**
   - Navigate to Developers → API keys
   - Copy your:
     - **Secret key** (starts with `sk_test_...` or `sk_live_...`)
     - **Publishable key** (starts with `pk_test_...` or `pk_live_...`)

3. **Set Up Webhook**
   - Go to Developers → Webhooks
   - Click "Add endpoint"
   - Enter your webhook URL: `https://your-domain.com/api/payments/webhook`
   - Select events to listen to:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Copy the **Webhook signing secret** (starts with `whsec_...`)

### 3. Configure Environment Variables

#### Backend (.env)
```bash
# Add these to your Backend/.env file
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
FRONTEND_URL=http://localhost:3000  # Update for production
```

#### Frontend (.env)
```bash
# Add these to your frontend/.env file
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
NEXT_PUBLIC_API_URL=http://localhost:8000  # Update for production
```

### 4. Run Database Migration

```bash
# Connect to your PostgreSQL database and run:
psql -U your_user -d your_database -f Backend/migrations/add_stripe_fields.sql

# Or using psycopg2 in Python:
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

with open('Backend/migrations/add_stripe_fields.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
conn.close()
print('Migration completed successfully!')
"
```

### 5. Test Webhooks Locally (Development)

For local development, use Stripe CLI to forward webhooks:

```bash
# Install Stripe CLI
# macOS: brew install stripe/stripe-cli/stripe
# Windows: scoop install stripe
# Linux: Download from https://github.com/stripe/stripe-cli/releases

# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8000/api/payments/webhook

# This will give you a webhook signing secret starting with whsec_
# Update your Backend/.env with this secret
```

### 6. Test Stripe Integration

#### Test Credit Cards
Use these test cards in development mode:

| Card Number | Type | Description |
|-------------|------|-------------|
| 4242 4242 4242 4242 | Visa | Successful payment |
| 4000 0025 0000 3155 | Visa | Requires authentication (3D Secure) |
| 4000 0000 0000 9995 | Visa | Always fails |

- Use any future expiration date (e.g., 12/34)
- Use any 3-digit CVC
- Use any 5-digit ZIP code

#### Testing Flow
1. Start your backend: `cd Backend && python main.py`
2. Start your frontend: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3000/pricing`
4. Click "Get Started" on any plan
5. Fill in the Stripe checkout form with test card
6. Verify redirect to success page
7. Check webhook events in Stripe Dashboard

## API Endpoints

### Get Pricing Plans
```
GET /api/payments/plans
```

### Create Checkout Session
```
POST /api/payments/create-checkout-session
Headers: Authorization: Bearer {token}
Body: { "plan_id": "starter" | "professional" | "enterprise" }
```

### Get Checkout Session
```
GET /api/payments/session/{session_id}
Headers: Authorization: Bearer {token}
```

### Get Subscription Status
```
GET /api/payments/subscription
Headers: Authorization: Bearer {token}
```

### Create Customer Portal Session
```
POST /api/payments/create-portal-session
Headers: Authorization: Bearer {token}
```

### Webhook Endpoint
```
POST /api/payments/webhook
Headers: stripe-signature: {signature}
```

## Frontend Integration

### Using the Subscription Manager Component

Add to your settings page:

```tsx
import SubscriptionManager from "../components/SubscriptionManager";

export default function SettingsPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      
      {/* Subscription Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Subscription</h2>
        <SubscriptionManager />
      </div>
      
      {/* Other settings... */}
    </div>
  );
}
```

### Adding a "Upgrade" Button

```tsx
import { useRouter } from "next/navigation";

function UpgradeButton() {
  const router = useRouter();
  
  return (
    <button 
      onClick={() => router.push("/pricing")}
      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
    >
      Upgrade Plan
    </button>
  );
}
```

## Security Considerations

1. **Never expose secret keys** - Keep `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` on the backend only
2. **Verify webhook signatures** - Always validate webhook events using the signature
3. **Use HTTPS in production** - Stripe requires HTTPS for webhooks in production
4. **Validate user permissions** - Ensure users can only manage their own subscriptions
5. **Handle edge cases** - Account for failed payments, subscription cancellations, etc.

## Production Checklist

Before going live:

- [ ] Switch from test keys to live keys in environment variables
- [ ] Update webhook endpoint in Stripe Dashboard to production URL
- [ ] Test webhook delivery in production
- [ ] Set up monitoring for failed payments
- [ ] Configure email notifications for subscription events
- [ ] Test all payment flows end-to-end
- [ ] Set up customer support flow for payment issues
- [ ] Review and update pricing plans if needed
- [ ] Enable Stripe Radar for fraud prevention
- [ ] Set up proper error logging and monitoring

## Customizing Pricing Plans

Edit the pricing plans in `/Backend/routers/payments.py`:

```python
PRICING_PLANS = {
    "starter": {
        "name": "Starter Plan",
        "price": 40,  # Price in dollars
        "interval": "month",  # or "year"
        "trial_days": 30,  # Free trial period
        "features": [
            "Feature 1",
            "Feature 2",
            # Add more features
        ]
    },
    # Add more plans...
}
```

## Next Steps

1. **Customize the pricing page** to match your brand
2. **Add usage limits** based on subscription plans
3. **Implement plan upgrade/downgrade flows**
4. **Add email notifications** for subscription events
5. **Create admin dashboard** to view subscription analytics
6. **Add proration** for mid-cycle plan changes
7. **Implement trials** if you want to offer free trials

## Useful Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/customer-portal)
- [Stripe Testing](https://stripe.com/docs/testing)

## Troubleshooting

### Webhook not receiving events
- Verify webhook URL is accessible from internet
- Check webhook signing secret is correct
- Ensure webhook endpoint is in Stripe Dashboard
- Use Stripe CLI for local testing

### Payment fails in production
- Ensure using live keys, not test keys
- Check webhook endpoint uses HTTPS
- Verify webhook signing secret is for live mode

### Session expires before payment
- Sessions expire after 24 hours by default
- Create a new session if needed

## Support

If you encounter any issues:
1. Check Stripe Dashboard → Developers → Logs
2. Review webhook delivery attempts
3. Check backend logs for errors
4. Verify environment variables are set correctly

---

Happy integrating!
