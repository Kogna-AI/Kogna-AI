"""
Stripe Payment Integration Router
Handles subscription creation, checkout sessions, and webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import stripe
import os
import logging
from datetime import datetime

from core.database import get_db
from auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Pricing Plans Configuration
PRICING_PLANS = {
    "starter": {
        "name": "Starter Plan",
        "price": 40,
        "interval": "month",
        "trial_days": 30,  # 1 month free trial
        "features": [
            "Up to 10 team members",
            "Basic analytics",
            "2 data connectors",
            "Email support"
        ]
    },
    "professional": {
        "name": "Professional Plan",
        "price": None,  # TBD
        "price_display": "TBD",
        "interval": "month",
        "features": [
            "Up to 50 team members",
            "Advanced analytics",
            "10 data connectors",
            "Priority support",
            "AI-powered insights"
        ]
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price": None,  # TBD
        "price_display": "TBD",
        "interval": "month",
        "features": [
            "Unlimited team members",
            "Custom analytics",
            "Unlimited data connectors",
            "24/7 dedicated support",
            "Custom AI models",
            "White-label options"
        ]
    }
}


@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    return {"plans": PRICING_PLANS}


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a Stripe Checkout Session for subscription
    """
    try:
        body = await request.json()
        plan_id = body.get("plan_id")
        
        if plan_id not in PRICING_PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan selected")
        
        plan = PRICING_PLANS[plan_id]
        
        # Check if plan has pricing set
        if plan["price"] is None:
            raise HTTPException(
                status_code=400, 
                detail="This plan is not yet available. Please contact sales for more information."
            )
        
        # Get user's stripe_customer_id from database
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_customer_id FROM users WHERE id = %s",
            (current_user["id"],)
        )
        user_result = cursor.fetchone()
        stripe_customer_id = user_result["stripe_customer_id"] if user_result else None
        
        # Create or retrieve Stripe customer
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user["email"],
                metadata={
                    "user_id": str(current_user["id"]),
                    "organization_id": str(current_user["organization_id"])
                }
            )
            stripe_customer_id = customer.id
            
            # Update user with stripe_customer_id
            cursor.execute(
                "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                (stripe_customer_id, current_user["id"])
            )
            db.commit()
        
        # Create Checkout Session
        session_params = {
            "customer": stripe_customer_id,
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": plan["name"],
                            "description": f"Kogna AI - {plan['name']}",
                        },
                        "unit_amount": plan["price"] * 100,  # Convert to cents
                        "recurring": {
                            "interval": plan["interval"]
                        }
                    },
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{FRONTEND_URL}/payment/cancel",
            "metadata": {
                "user_id": str(current_user["id"]),
                "organization_id": str(current_user["organization_id"]),
                "plan_id": plan_id
            },
            # Enable Stripe's built-in promotion code field
            "allow_promotion_codes": True
        }
        
        # Add free trial if plan includes it
        if plan.get("trial_days"):
            session_params["subscription_data"] = {
                "trial_period_days": plan["trial_days"]
            }
            # Optional: Don't require payment method during trial
            # Uncomment if you want truly no credit card required:
            # session_params["payment_method_collection"] = "if_required"
        
        checkout_session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created checkout session {checkout_session.id} for user {current_user['id']}")
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/session/{session_id}")
async def get_checkout_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve checkout session details
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "status": session.payment_status,
            "customer_email": session.customer_details.email if session.customer_details else None,
            "amount_total": session.amount_total,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-portal-session")
async def create_portal_session(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a Stripe Customer Portal session for managing subscriptions
    """
    try:
        # Get user's stripe_customer_id from database
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_customer_id FROM users WHERE id = %s",
            (current_user["id"],)
        )
        user_result = cursor.fetchone()
        stripe_customer_id = user_result["stripe_customer_id"] if user_result else None
        
        if not stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail="No active subscription found"
            )
        
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{FRONTEND_URL}/settings",
        )
        
        return {"url": portal_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription")
async def get_subscription_status(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current subscription status
    """
    try:
        # Get user's stripe_customer_id from database
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_customer_id FROM users WHERE id = %s",
            (current_user["id"],)
        )
        user_result = cursor.fetchone()
        stripe_customer_id = user_result["stripe_customer_id"] if user_result else None
        
        if not stripe_customer_id:
            return {
                "has_subscription": False,
                "plan": None,
                "status": None
            }
        
        # Retrieve customer's subscriptions
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=1
        )
        
        if not subscriptions.data:
            return {
                "has_subscription": False,
                "plan": None,
                "status": None
            }
        
        subscription = subscriptions.data[0]
        
        return {
            "has_subscription": True,
            "plan": subscription.metadata.get("plan_id"),
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event["type"]
    logger.info(f"Received Stripe webhook: {event_type}")
    
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(session, db)
        
    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await handle_subscription_updated(subscription, db)
        
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(subscription, db)
        
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        await handle_payment_succeeded(invoice, db)
        
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        await handle_payment_failed(invoice, db)
    
    return {"status": "success"}


async def handle_checkout_completed(session, db):
    """Handle successful checkout"""
    try:
        user_id = session["metadata"].get("user_id")
        organization_id = session["metadata"].get("organization_id")
        plan_id = session["metadata"].get("plan_id")
        
        # Update organization with subscription details
        if organization_id:
            cursor = db.cursor()
            cursor.execute(
                """
                UPDATE organizations 
                SET subscription_plan = %s,
                    subscription_status = %s,
                    stripe_subscription_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (plan_id, "active", session.get("subscription"), organization_id)
            )
            db.commit()
            logger.info(f"Updated organization {organization_id} with subscription {plan_id}")
    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}")
        db.rollback()


async def handle_subscription_updated(subscription, db):
    """Handle subscription updates"""
    try:
        customer_id = subscription["customer"]
        cursor = db.cursor()
        
        # Find user by stripe_customer_id
        cursor.execute(
            "SELECT id, organization_id FROM users WHERE stripe_customer_id = %s",
            (customer_id,)
        )
        user = cursor.fetchone()
        
        if user and user["organization_id"]:
            cursor.execute(
                """
                UPDATE organizations 
                SET subscription_status = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (subscription["status"], user["organization_id"])
            )
            db.commit()
            logger.info(f"Updated subscription status for organization {user['organization_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")
        db.rollback()


async def handle_subscription_deleted(subscription, db):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription["customer"]
        cursor = db.cursor()
        
        # Find user by stripe_customer_id
        cursor.execute(
            "SELECT id, organization_id FROM users WHERE stripe_customer_id = %s",
            (customer_id,)
        )
        user = cursor.fetchone()
        
        if user and user["organization_id"]:
            cursor.execute(
                """
                UPDATE organizations 
                SET subscription_status = %s,
                    subscription_plan = NULL,
                    updated_at = NOW()
                WHERE id = %s
                """,
                ("cancelled", user["organization_id"])
            )
            db.commit()
            logger.info(f"Cancelled subscription for organization {user['organization_id']}")
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")
        db.rollback()


async def handle_payment_succeeded(invoice, db):
    """Handle successful payment"""
    logger.info(f"Payment succeeded for invoice {invoice['id']}")
    # You can add logic to log successful payments or send notifications


async def handle_payment_failed(invoice, db):
    """Handle failed payment"""
    logger.warning(f"Payment failed for invoice {invoice['id']}")
    # You can add logic to notify the customer or take action
