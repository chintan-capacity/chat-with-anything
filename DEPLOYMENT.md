# Deployment Guide

This guide will help you set up CI/CD for deploying the app to Google Cloud Run.

## Prerequisites

- Google Cloud Platform account
- GitHub repository
- `gcloud` CLI installed (for initial setup)

## Setup Instructions

### 1. Set up Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Create project (if needed)
gcloud projects create $PROJECT_ID

# Set as active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions" \
    --project=$PROJECT_ID

# Get service account email
SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:GitHub Actions" \
    --format="value(email)")

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=$SA_EMAIL

# Display key (copy this for GitHub secrets)
cat key.json
```

### 3. Configure GitHub Secrets

Go to your GitHub repository settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `GCP_PROJECT_ID` | your-project-id | Your GCP project ID |
| `GCP_REGION` | us-central1 | Deployment region (optional, defaults to us-central1) |
| `GCP_SA_KEY` | contents of key.json | Service account JSON key |
| `GEMINI_API_KEY` | your-gemini-key | Your Gemini API key |

### 4. Deploy

Push to main or production branch to trigger deployment:

```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

Or manually trigger deployment from GitHub Actions tab.

### 5. Verify Deployment

After deployment completes, check the Actions tab for the service URL.

## Manual Deployment (Optional)

To deploy manually without CI/CD:

```bash
# Build image
docker build -t gcr.io/$PROJECT_ID/chat-with-anything .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/chat-with-anything

# Deploy to Cloud Run
gcloud run deploy chat-with-anything \
    --image gcr.io/$PROJECT_ID/chat-with-anything \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GEMINI_API_KEY=your-key-here"
```

## Configuration

### Resource Limits

Default configuration in `deploy.yml`:
- Memory: 1Gi
- CPU: 1
- Timeout: 300s
- Min instances: 0
- Max instances: 10

Adjust these in the workflow file as needed.

### Environment Variables

Environment variables are set in the workflow. To add more:

```yaml
--set-env-vars "VAR1=value1,VAR2=value2"
```

Or use GCP Secret Manager:

```yaml
--set-secrets "API_KEY=api-key:latest"
```

## Monitoring

View logs in Google Cloud Console:
- Cloud Run → Select service → Logs tab

Or use gcloud:

```bash
gcloud run services logs read chat-with-anything --region=us-central1
```

## Troubleshooting

### Deployment fails
- Check GitHub Actions logs
- Verify all secrets are set correctly
- Ensure APIs are enabled in GCP

### App doesn't start
- Check Cloud Run logs
- Verify GEMINI_API_KEY is set
- Test Docker image locally

### Permission errors
- Verify service account has required roles
- Check IAM policy bindings

## Cleanup

To delete the service:

```bash
gcloud run services delete chat-with-anything --region=us-central1
```

To delete the project:

```bash
gcloud projects delete $PROJECT_ID
```
