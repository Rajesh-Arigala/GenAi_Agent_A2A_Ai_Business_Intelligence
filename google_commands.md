# Google ADK Multi-Agent A2A Deployment Runbook

## Purpose

This runbook gives a complete command-by-command method to deploy the A2A Competitive Intelligence Platform on Google Cloud Run and connect it to a Render-hosted UI.

It is written so a beginner can follow it without guessing.

---

# 1. Final Target Architecture

```text
User Browser
    |
    v
Render Static UI
    |
    v
Cloud Run Host Agent
    |
    +--> Market Scanner Agent
    +--> Sentiment Analyzer Agent
    +--> Pricing Intelligence Agent
    +--> Report Generator Agent
    |
    v
Final Competitive Intelligence Report
```

---

# 2. Required Assumptions

Before starting, make sure:

```text
1. GitHub repo has correct code.
2. Google Cloud project exists.
3. Billing is enabled.
4. You are logged into Google Cloud Shell.
5. Region is us-central1.
6. Project ID is a2a-market-research.
```

---

# 3. Open Cloud Shell

Go to Google Cloud Console.

Open Cloud Shell.

Confirm project:

```bash
gcloud config get-value project
```

Expected:

```text
a2a-market-research
```

If incorrect:

```bash
gcloud config set project a2a-market-research
```

Confirm account:

```bash
gcloud auth list
```

If required:

```bash
gcloud auth login
```

---

# 4. Clean Existing Local Clone

This deletes only the Cloud Shell local copy, not GitHub.

```bash
cd ~

rm -rf GenAi_Agent_A2A_Ai_Business_Intelligence
```

Verify:

```bash
ls
```

---

# 5. Clone Fresh Repository

```bash
git clone https://github.com/Rajesh-Arigala/GenAi_Agent_A2A_Ai_Business_Intelligence

cd GenAi_Agent_A2A_Ai_Business_Intelligence

git status
```

Expected:

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

---

# 6. Set Variables

```bash
PROJECT_ID=a2a-market-research
PROJECT_NUMBER=16967482277
REGION=us-central1
REPO=cloud-run-source-deploy
```

Verify:

```bash
echo $PROJECT_ID
echo $PROJECT_NUMBER
echo $REGION
echo $REPO
```

---

# 7. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com
```

Expected:

```text
Operation finished successfully.
```

---

# 8. Check Artifact Registry

```bash
gcloud artifacts repositories list --location=$REGION
```

Expected to see:

```text
cloud-run-source-deploy
```

If missing:

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="Cloud Run Source Deployments"
```

---

# 9. Grant IAM to Cloud Build Service Account

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud artifacts repositories add-iam-policy-binding $REPO \
  --location=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud artifacts repositories add-iam-policy-binding $REPO \
  --location=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"
```

---

# 10. Grant IAM to Compute Default Service Account

This is important because Cloud Build may actually execute using this account.

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud artifacts repositories add-iam-policy-binding $REPO \
  --location=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud artifacts repositories add-iam-policy-binding $REPO \
  --location=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"
```

Expected:

```text
Updated IAM policy.
```

---

# 11. Optional Single-Service Build Test

Do this before full deployment if you want to verify build and push.

```bash
cd ~/GenAi_Agent_A2A_Ai_Business_Intelligence/agents/market_scanner

gcloud builds submit . \
  --region=$REGION \
  --tag us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/market-scanner:test
```

Expected:

```text
SUCCESS
```

Optional direct deploy:

```bash
gcloud run deploy market-scanner \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/market-scanner:test \
  --region=$REGION
```

Return to root:

```bash
cd ~/GenAi_Agent_A2A_Ai_Business_Intelligence
```

---

# 12. Run Full Deployment

```bash
cd ~/GenAi_Agent_A2A_Ai_Business_Intelligence

chmod +x deploy.sh

./deploy.sh
```

Expected final output:

```text
All 5 agents deployed successfully!
```

Services expected:

```text
market-scanner
sentiment-analyzer
pricing-intel
report-generator
competitive-intel-host
```

---

# 13. Fix Public Access for All Services

Because organization policy may block `allUsers`, use `--no-invoker-iam-check`.

```bash
gcloud run services update market-scanner \
  --region=$REGION \
  --no-invoker-iam-check

gcloud run services update sentiment-analyzer \
  --region=$REGION \
  --no-invoker-iam-check

gcloud run services update pricing-intel \
  --region=$REGION \
  --no-invoker-iam-check

gcloud run services update report-generator \
  --region=$REGION \
  --no-invoker-iam-check

gcloud run services update competitive-intel-host \
  --region=$REGION \
  --no-invoker-iam-check
```

Expected:

```text
Service has been updated.
```

---

# 14. List Cloud Run Services

```bash
gcloud run services list --region=$REGION
```

Expected:

```text
market-scanner
sentiment-analyzer
pricing-intel
report-generator
competitive-intel-host
```

---

# 15. Verify Host Service

```bash
curl -v https://competitive-intel-host-16967482277.us-central1.run.app
```

Expected:

```text
HTTP 404
{"detail":"Not Found"}
```

This is okay. It means the service is reachable, but `/` is not a valid endpoint.

---

# 16. Verify OpenAPI

```bash
curl https://competitive-intel-host-16967482277.us-central1.run.app/openapi.json
```

Expected:

```json
{"openapi":"3.1.0","info":{"title":"Competitive Intelligence A2A Host","version":"1.0.0"},"paths":{}}
```

If this returns 500, check `main.py` OpenAPI override.

---

# 17. Verify Swagger Docs

```bash
curl https://competitive-intel-host-16967482277.us-central1.run.app/docs
```

Expected:

```text
HTML response
```

---

# 18. Create ADK Session

```bash
curl -X POST \
https://competitive-intel-host-16967482277.us-central1.run.app/apps/host/users/ui_user/sessions \
-H "Content-Type: application/json" \
-d '{}'
```

Expected:

```json
{
  "id": "SESSION_ID",
  "appName": "host",
  "userId": "ui_user",
  "state": {},
  "events": []
}
```

Copy the `id`.

---

# 19. Test SSE Streaming

Replace `SESSION_ID_HERE` with the real session ID.

```bash
curl -N \
-X POST \
https://competitive-intel-host-16967482277.us-central1.run.app/run_sse \
-H "Content-Type: application/json" \
-d '{
  "app_name":"host",
  "user_id":"ui_user",
  "session_id":"SESSION_ID_HERE",
  "new_message":{
    "role":"user",
    "parts":[
      {
        "text":"Analyze competitor: OpenAI"
      }
    ]
  }
}'
```

Expected:

```text
data: {...}
data: {...}
data: {...}
```

This confirms backend streaming works.

---

# 20. Read Logs If Needed

Host logs:

```bash
gcloud run services logs read competitive-intel-host \
  --region=$REGION \
  --limit=100
```

Market scanner logs:

```bash
gcloud run services logs read market-scanner \
  --region=$REGION \
  --limit=100
```

Sentiment analyzer logs:

```bash
gcloud run services logs read sentiment-analyzer \
  --region=$REGION \
  --limit=100
```

Pricing logs:

```bash
gcloud run services logs read pricing-intel \
  --region=$REGION \
  --limit=100
```

Report generator logs:

```bash
gcloud run services logs read report-generator \
  --region=$REGION \
  --limit=100
```

---

# 21. Render UI Deployment

Render should deploy only the UI.

Settings:

```text
Service Type: Static Site
Root Directory: ui
Build Command: blank
Publish Directory: .
```

Do not use:

```bash
python -m http.server 8000
```

on Render.

That is only for local testing.

---

# 22. Host URL for UI

Use:

```text
https://competitive-intel-host-16967482277.us-central1.run.app
```

Test query:

```text
Analyze competitor: OpenAI
```

---

# 23. Local UI Test

```bash
cd ui

python -m http.server 8000
```

Open browser:

```text
http://localhost:8000
```

Paste host URL:

```text
https://competitive-intel-host-16967482277.us-central1.run.app
```

---

# 24. Common Errors and Fixes

## Error: deploy.sh not found

Cause:

Wrong directory.

Fix:

```bash
cd ~/GenAi_Agent_A2A_Ai_Business_Intelligence
```

---

## Error: Project your-gcp-project-id not found

Cause:

Placeholder still exists in `deploy.sh`.

Fix:

Edit `deploy.sh`.

```bash
nano deploy.sh
```

Replace:

```text
your-gcp-project-id
```

with:

```text
a2a-market-research
```

---

## Error: Artifact upload denied

Cause:

Wrong service account lacks Artifact Registry Writer.

Fix:

Grant permissions to:

```text
PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

---

## Error: 403 Forbidden on Cloud Run URL

Cause:

Invoker IAM check still active.

Fix:

```bash
gcloud run services update SERVICE_NAME \
  --region=$REGION \
  --no-invoker-iam-check
```

---

## Error: /openapi.json returns 500

Cause:

FastAPI/Pydantic schema error.

Fix:

Use custom OpenAPI override in `main.py`.

---

## UI stuck on Connecting

Causes:

```text
1. Session API failing
2. Backend not public
3. JavaScript fetch error
4. Session creation outside try/catch
```

Fix:

Test session manually:

```bash
curl -X POST \
https://competitive-intel-host-16967482277.us-central1.run.app/apps/host/users/ui_user/sessions \
-H "Content-Type: application/json" \
-d '{}'
```

---

# 25. Final Success Checklist

```text
[ ] Correct project selected
[ ] Fresh repo cloned
[ ] APIs enabled
[ ] Artifact Registry exists
[ ] Cloud Build SA has permissions
[ ] Compute SA has permissions
[ ] deploy.sh completed
[ ] All 5 services deployed
[ ] Invoker IAM check disabled
[ ] Host URL reachable
[ ] /openapi.json works
[ ] /docs works
[ ] Session creation works
[ ] /run_sse streams data
[ ] Render UI loads
[ ] Render UI connects to Host
[ ] All 4 specialist agents execute
[ ] Final report appears in browser
```

---

# 26. Final Working URLs

Host:

```text
https://competitive-intel-host-16967482277.us-central1.run.app
```

Market Scanner:

```text
https://market-scanner-16967482277.us-central1.run.app
```

Sentiment Analyzer:

```text
https://sentiment-analyzer-16967482277.us-central1.run.app
```

Pricing Intelligence:

```text
https://pricing-intel-16967482277.us-central1.run.app
```

Report Generator:

```text
https://report-generator-16967482277.us-central1.run.app
```

---

# 27. Final Lesson

Follow this order every time:

```text
1. Project
2. Repo
3. APIs
4. IAM
5. Artifact Registry
6. One-service build test
7. Full deploy
8. Public access
9. Host test
10. OpenAPI test
11. Session test
12. SSE test
13. UI test
14. Render test
```

Do not jump directly to the UI before the backend passes curl tests.