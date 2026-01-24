-- Migration: Add Stripe payment fields to users and organizations tables
-- Date: 2026-01-24

-- Add Stripe customer ID to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) UNIQUE;

-- Add subscription fields to organizations table
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(50),
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255) UNIQUE;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_subscription_id ON organizations(stripe_subscription_id);

-- Add comments for documentation
COMMENT ON COLUMN users.stripe_customer_id IS 'Stripe customer ID for payment processing';
COMMENT ON COLUMN organizations.subscription_plan IS 'Active subscription plan (starter, professional, enterprise)';
COMMENT ON COLUMN organizations.subscription_status IS 'Subscription status (active, cancelled, past_due, etc.)';
COMMENT ON COLUMN organizations.stripe_subscription_id IS 'Stripe subscription ID';
