# GitHub Secrets Setup Guide

Step-by-step instructions for configuring GitHub Secrets for the Kogna-AI CI/CD pipeline.

## Step-by-Step Instructions

### Step 1: Navigate to Your Repository Settings

1. Go to your GitHub repository: `https://github.com/Kogna-AI/Kogna-AI`
2. Click on the **Settings** tab (top navigation bar, far right)
   - Note: You need admin or write access to the repository to see this tab

### Step 2: Access Secrets and Variables

1. In the left sidebar, scroll down to the **Security** section
2. Click on **Secrets and variables**
3. Click on **Actions** from the dropdown

You should now see the "Actions secrets and variables" page.

### Step 3: Add Repository Secrets

For each secret below, follow these steps:

1. Click the **New repository secret** button (green button on the right)
2. Enter the **Name** exactly as shown below (case-sensitive)
3. Enter the **Secret** value (your actual API key or URL)
4. Click **Add secret**

## Secrets to Add

### Frontend Secrets (3 secrets)

#### 1. NEXT_PUBLIC_SUPABASE_URL
- **Name:** `NEXT_PUBLIC_SUPABASE_URL`
- **Value:** Your Supabase project URL (e.g., `https://abcdefghijk.supabase.co`)
- **Where to find it:**
  - Go to your Supabase dashboard: https://app.supabase.com
  - Select your project
  - Click on **Settings** (gear icon in the left sidebar)
  - Click on **API**
  - Copy the **Project URL**

#### 2. NEXT_PUBLIC_SUPABASE_ANON_KEY
- **Name:** `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Value:** Your Supabase anonymous/public key
- **Where to find it:**
  - Same location as above (Settings → API)
  - Copy the **anon/public** key (under "Project API keys")

#### 3. NEXT_PUBLIC_API_URL
- **Name:** `NEXT_PUBLIC_API_URL`
- **Value:** Your backend API URL
- **Examples:**
  - For production: `https://api.kogna.ai` (your actual domain)
  - For staging: `https://staging-api.kogna.ai`
  - For testing with localhost: `http://localhost:8000` (only for development)

---

### Backend Secrets (7 secrets)

#### 4. SUPABASE_URL
- **Name:** `SUPABASE_URL`
- **Value:** Same as `NEXT_PUBLIC_SUPABASE_URL` above
- **Where to find it:** Supabase Dashboard → Settings → API → Project URL

#### 5. SUPABASE_KEY
- **Name:** `SUPABASE_KEY`
- **Value:** Your Supabase **service_role** key (NOT the anon key)
- **Where to find it:**
  - Supabase Dashboard → Settings → API
  - Copy the **service_role** key (under "Project API keys")
  - ⚠️ **Warning:** This is a sensitive key with admin privileges. Keep it secret!

#### 6. DATABASE_URL
- **Name:** `DATABASE_URL`
- **Value:** PostgreSQL connection string
- **Format:** `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`
- **Where to find it:**
  - Supabase Dashboard → Settings → Database
  - Look for **Connection string** → **URI**
  - Copy the entire connection string
  - Make sure to replace `[YOUR-PASSWORD]` with your actual database password

#### 7. OPENAI_API_KEY
- **Name:** `OPENAI_API_KEY`
- **Value:** Your OpenAI API key (starts with `sk-`)
- **Where to find it:**
  - Go to https://platform.openai.com/api-keys
  - Click **Create new secret key**
  - Copy the key immediately (you can't view it again)
  - Name it something like "Kogna-AI Production"

#### 8. ANTHROPIC_API_KEY
- **Name:** `ANTHROPIC_API_KEY`
- **Value:** Your Anthropic (Claude) API key (starts with `sk-ant-`)
- **Where to find it:**
  - Go to https://console.anthropic.com/
  - Navigate to **API Keys**
  - Click **Create Key**
  - Copy the key immediately

#### 9. GOOGLE_API_KEY
- **Name:** `GOOGLE_API_KEY`
- **Value:** Your Google API key
- **Where to find it:**
  - Go to https://console.cloud.google.com/
  - Select your project (or create a new one)
  - Navigate to **APIs & Services** → **Credentials**
  - Click **Create Credentials** → **API Key**
  - Copy the generated key
  - Enable the required APIs (e.g., Google Search API, Generative AI API)

#### 10. SERP_API_KEY
- **Name:** `SERP_API_KEY`
- **Value:** Your SerpAPI key
- **Where to find it:**
  - Go to https://serpapi.com/
  - Sign up or log in
  - Go to **Dashboard** → **API Key**
  - Copy your private API key

---

### AWS Secrets (2 secrets)

#### 11. AWS_ACCESS_KEY_ID
- **Name:** `AWS_ACCESS_KEY_ID`
- **Value:** Your AWS access key ID
- **Where to find it:**
  - Go to AWS Console: https://console.aws.amazon.com/
  - Click on your username (top right) → **Security credentials**
  - Scroll to **Access keys**
  - Click **Create access key**
  - Select **Use case:** "Application running on AWS compute service" or "Other"
  - Download the CSV file or copy the Access Key ID
  - ⚠️ **Note:** Create a dedicated IAM user for CI/CD with limited permissions (not your root account)

#### 12. AWS_SECRET_ACCESS_KEY
- **Name:** `AWS_SECRET_ACCESS_KEY`
- **Value:** Your AWS secret access key
- **Where to find it:**
  - Same process as above
  - Copy the **Secret Access Key** when creating the access key
  - ⚠️ **Important:** You can only view this once! Save it securely.
  - If you lose it, you'll need to create a new access key

---

## IAM User Setup for AWS (Recommended)

Instead of using your root AWS credentials, create a dedicated IAM user:

### Step 1: Create IAM User

```bash
# Using AWS CLI (if you have it installed)
aws iam create-user --user-name github-actions-kogna-ai
```

Or via AWS Console:
1. Go to **IAM** → **Users** → **Add users**
2. Username: `github-actions-kogna-ai`
3. Select **Access key - Programmatic access**
4. Click **Next**

### Step 2: Attach Permissions

Create and attach this policy to the user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecs:DescribeTasks"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/ecsTaskExecutionRole"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Create Access Keys

1. Select the newly created user
2. Go to **Security credentials** tab
3. Click **Create access key**
4. Select **Application running on AWS compute service**
5. Download the CSV or copy the keys
6. Use these for `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

---

## Verification Steps

### After Adding All Secrets

1. Go back to **Settings** → **Secrets and variables** → **Actions**
2. You should see all 12 repository secrets listed:
   - ANTHROPIC_API_KEY
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - DATABASE_URL
   - GOOGLE_API_KEY
   - NEXT_PUBLIC_API_URL
   - NEXT_PUBLIC_SUPABASE_ANON_KEY
   - NEXT_PUBLIC_SUPABASE_URL
   - OPENAI_API_KEY
   - SERP_API_KEY
   - SUPABASE_KEY
   - SUPABASE_URL

3. **Note:** You cannot view the secret values after saving (only the names)
4. To update a secret, click on it and choose **Update secret**

---

## Testing Your Secrets

After adding all secrets, test that they work:

### Option 1: Trigger CI Workflow

```bash
# Push a change to trigger the CI
git checkout -b test-secrets
echo "# Testing secrets" >> README.md
git add README.md
git commit -m "test: verify CI/CD secrets configuration"
git push origin test-secrets
```

Then create a pull request and check if the workflows run successfully.

### Option 2: Manual Workflow Dispatch

1. Go to **Actions** tab in your repository
2. Select **Frontend CI** or **Backend CI** workflow
3. Click **Run workflow** dropdown
4. Select the branch
5. Click **Run workflow**
6. Monitor the workflow run for any secret-related errors

---

## Common Issues and Solutions

### Issue 1: "Secret not found" Error

**Problem:** Workflow fails with `secret not found` error

**Solution:**
- Check that the secret name matches exactly (case-sensitive)
- Verify the secret was added at the repository level, not environment level
- Make sure you have the correct permissions

### Issue 2: Invalid Supabase Credentials

**Problem:** Build fails with Supabase authentication errors

**Solution:**
- Verify you're using the correct project URL (ends with `.supabase.co`)
- For frontend, use the `anon` key
- For backend, use the `service_role` key
- Double-check there are no extra spaces when copying

### Issue 3: AWS Permissions Error

**Problem:** Deployment fails with "Access Denied" errors

**Solution:**
- Verify the IAM user has the correct permissions (see policy above)
- Check that both access key ID and secret key are correct
- Ensure the region matches (`us-east-1` by default)
- Verify ECR repositories and ECS cluster exist

### Issue 4: Database Connection Error

**Problem:** Backend fails to connect to database

**Solution:**
- Verify `DATABASE_URL` format is correct
- Ensure password is properly URL-encoded (special characters need encoding)
- Check that Supabase database is accessible
- Verify IP allowlist settings in Supabase (should allow all for cloud deployments)

---

## Security Best Practices

1. **Never commit secrets to git**
   - Always use GitHub Secrets for sensitive data
   - Add `.env` files to `.gitignore`

2. **Rotate secrets regularly**
   - Change API keys every 90 days
   - Update secrets in GitHub when rotated

3. **Use different keys for different environments**
   - Separate keys for development, staging, and production
   - Use GitHub Environments for environment-specific secrets

4. **Limit AWS IAM permissions**
   - Only grant necessary permissions
   - Don't use root account credentials
   - Enable MFA on AWS account

5. **Monitor secret usage**
   - Check GitHub Actions logs for unauthorized access
   - Monitor AWS CloudTrail for API usage
   - Review Supabase logs regularly

6. **Delete unused secrets**
   - Remove secrets from GitHub when no longer needed
   - Revoke old API keys from service providers

---

## Optional: Environment-Specific Secrets

If you want to use different secrets for staging vs production:

### Create Environments

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create environments: `staging` and `production`
4. Add environment-specific secrets to each

### Update Workflow

Modify `.github/workflows/deploy-aws-ecs.yml` to use environments:

```yaml
deploy-backend:
  name: Deploy Backend to ECS
  needs: build-and-push-backend
  runs-on: ubuntu-latest
  environment: production  # Add this line
  # ... rest of the job
```

---

## Need Help?

If you encounter issues:

1. Check the GitHub Actions logs for specific error messages
2. Verify each secret is correctly copied (no extra spaces/characters)
3. Test locally with `.env` file first
4. Review the [CI-CD-SETUP.md](./CI-CD-SETUP.md) documentation
5. Check AWS CloudWatch logs if deployment fails

---

**Last Updated:** 2025-01-22
