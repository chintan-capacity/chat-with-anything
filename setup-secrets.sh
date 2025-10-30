#!/bin/bash

# Setup GitHub Secrets for chat-with-anything
# Run this script after authenticating with: gh auth login

set -e

REPO="chintan-capacity/chat-with-anything"
SA_KEY_FILE="/Users/admin/Downloads/simulation-playground-471214-firebase-adminsdk-fbsvc-666bff2388.json"

echo "🔐 Setting up GitHub Secrets for $REPO"
echo ""

# Set GCP Project ID
echo "Setting GCP_PROJECT_ID..."
gh secret set GCP_PROJECT_ID --body "simulation-playground-471214" --repo $REPO

# Set GCP Region
echo "Setting GCP_REGION..."
gh secret set GCP_REGION --body "us-east1" --repo $REPO

# Set GCP Service Account Key
echo "Setting GCP_SA_KEY..."
gh secret set GCP_SA_KEY --body "$(cat $SA_KEY_FILE)" --repo $REPO

# Set Gemini API Key
echo "Setting GEMINI_API_KEY..."
gh secret set GEMINI_API_KEY --body "AIzaSyAJT-p-SlzHkSc8hQGb_0z3MbVE9IWfnBc" --repo $REPO

# Set WebShare Proxy Credentials
echo "Setting WEBSHARE_PROXY_USERNAME..."
gh secret set WEBSHARE_PROXY_USERNAME --body "xyjdcjab" --repo $REPO

echo "Setting WEBSHARE_PROXY_PASSWORD..."
gh secret set WEBSHARE_PROXY_PASSWORD --body "hbqb5sqmf0oi" --repo $REPO

echo ""
echo "✅ All secrets have been set successfully!"
echo ""
echo "You can verify by visiting:"
echo "https://github.com/$REPO/settings/secrets/actions"
echo ""
echo "🚀 Ready to deploy! Push to main branch or manually trigger workflow."
