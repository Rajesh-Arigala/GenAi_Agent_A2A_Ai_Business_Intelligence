# A2A Competitive Intelligence Platform – Complete Deployment & Debugging Guide

---

# Purpose

This document captures the complete deployment journey of the **Google ADK Multi-Agent A2A Competitive Intelligence Platform**, including every major mistake, how each issue was diagnosed, and the exact fixes that led to a successful deployment.

The document is written for someone with little or no Google Cloud experience.

---

# Final Architecture

```text
                Browser
          (Localhost / Render)
                    │
                    │
                    ▼
          Competitive Intel UI
                    │
                    ▼
         Cloud Run Host Agent
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
Market Scanner  Sentiment AI  Pricing AI
                    │
                    ▼
          Report Generator
                    │
                    ▼
           Final Markdown Report
```

---

# Technology Stack

| Component | Technology |
|-----------|------------|
| UI | HTML + JavaScript |
| Backend | Google ADK |
| API | FastAPI |
| Runtime | Cloud Run |
| Container | Docker |
| Build | Cloud Build |
| Registry | Artifact Registry |
| Streaming | SSE |
| Deployment | Cloud Run |
| UI Hosting | Render |

---

# Phase 1 — Initial Deployment

## Objective

Deploy all five Google ADK agents using

```bash
chmod +x deploy.sh && ./deploy.sh
```

---

## Mistake

Executed the command from the wrong folder.

Example

```bash
chmod +x deploy.sh
```

returned

```
No such file or directory
```

---

## Root Cause

Cloud Shell was opened in

```
~
```

instead of

```
GenAi_Agent_A2A_Ai_Business_Intelligence
```

---

## Fix

```bash
cd ~/GenAi_Agent_A2A_Ai_Business_Intelligence

chmod +x deploy.sh

./deploy.sh
```

---

# Lesson Learned

Always verify your working directory first.

Useful command

```bash
pwd
```

---

# Phase 2 — Cloud Build Failure

Deployment started.

Docker build appeared to fail.

Cloud Run reported

```
Build failed
```

---

## Investigation

Instead of guessing, inspect Cloud Build.

```bash
gcloud builds log BUILD_ID \
--region=us-central1
```

and

```bash
gcloud builds describe BUILD_ID \
--region=us-central1
```

---

## Discovery

Docker build completed successfully.

```
run-docker-build
Status : SUCCESS
```

Overall build

```
FAILURE
```

Therefore Docker was NOT the issue.

The failure occurred after image creation.

---

# Lesson Learned

Never assume Docker is broken.

Always inspect Cloud Build first.

---

# Phase 3 — Artifact Registry

Next suspicion

Artifact Registry

---

Verified repository

```bash
gcloud artifacts repositories list \
--location=us-central1
```

Output showed

```
cloud-run-source-deploy
```

already existed.

---

## Conclusion

Repository existed.

The problem had to be permissions.

---

# Phase 4 — IAM Permissions

Initially permissions were granted to

```
PROJECT_NUMBER@cloudbuild.gserviceaccount.com
```

using

```bash
gcloud projects add-iam-policy-binding ...
```

---

## Result

Deployment still failed.

---

## Investigation

Looked carefully at Cloud Build logs.

Discovered build was actually executing as

```
PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

NOT

```
PROJECT_NUMBER@cloudbuild.gserviceaccount.com
```

---

# Root Cause

Wrong Service Account.

---

# Fix

Granted

Artifact Registry Writer

Artifact Registry Reader

Logging Log Writer

to BOTH service accounts.

Project level

```bash
gcloud projects add-iam-policy-binding
```

Repository level

```bash
gcloud artifacts repositories add-iam-policy-binding
```

---

# Lesson Learned

Never assume which service account is executing.

Always verify.

---

# Phase 5 — Isolate the Problem

Instead of deploying all five services repeatedly

only one service was tested.

```
market_scanner
```

---

Command

```bash
cd agents/market_scanner

gcloud builds submit .
```

---

## Why

If one service cannot build

the platform cannot build.

Testing one service reduces debugging time.

---

# Lesson Learned

Reduce problem size.

Debug one service first.

---

# Phase 6 — Successful Docker Build

After IAM fixes

Docker image

built

and

pushed successfully

to Artifact Registry.

---

Deployment finally succeeded.

---

# Phase 7 — Public Access

Browser returned

```
403 Forbidden
```

---

Initially attempted

```bash
gcloud run services add-iam-policy-binding
```

with

```
allUsers
```

---

Google returned

```
FAILED_PRECONDITION
```

because organization policy blocked public invoker.

---

# Fix

Instead of IAM

used

```bash
gcloud run services update SERVICE_NAME \
--no-invoker-iam-check
```

Applied to

```
market-scanner

sentiment-analyzer

pricing-intel

report-generator

competitive-intel-host
```

---

# Lesson Learned

Organization Policies override IAM.

---

# Phase 8 — Verify Host

Tested

```bash
curl HOST_URL
```

Initially

```
403
```

After IAM fix

```
404
```

---

404 is GOOD.

It means

Cloud Run

is alive.

Only

```
/
```

doesn't exist.

---

# Phase 9 — FastAPI

Checked

```
/docs
```

Worked.

Checked

```
/openapi.json
```

Returned

```
500
```

---

Cloud Run logs

showed

```
PydanticInvalidForJsonSchema

httpx.Client
```

---

Root Cause

FastAPI tried to generate JSON schema

for

```
httpx.Client
```

which is unsupported.

---

# Fix

Override

```python
app.openapi
```

using a minimal custom schema.

Problem solved.

---

# Lesson Learned

Application bugs

are different from infrastructure bugs.

---

# Phase 10 — Session API

Instead of testing the browser

tested backend.

Created session

```bash
curl -X POST \
HOST/apps/host/users/ui_user/sessions
```

Returned

```
Session ID
```

Meaning

Host

ADK

Session Service

were working.

---

# Lesson Learned

Always test APIs directly before testing UI.

---

# Phase 11 — SSE

Next tested

```
POST /run_sse
```

using curl.

Received

streaming output.

Meaning

Host Agent

Market Scanner

Streaming

were all functioning.

---

# Phase 12 — UI Bug

Browser

stayed forever on

```
Connecting...
```

---

Root Cause

Session creation

was outside

JavaScript

```
try/catch
```

Therefore

errors disappeared

without showing the user anything.

---

# Fix

Moved

session creation

inside

```
try
```

Added proper

```
catch
```

block.

---

# Lesson Learned

Always wrap

network calls

inside

try/catch.

---

# Phase 13 — Render

Initially uncertainty

about deploying UI.

Solution

Deploy ONLY

```
ui/
```

as

Render Static Site.

No Python server required.

---

Settings

Root Directory

```
ui
```

Publish Directory

```
.
```

Build Command

Blank

---

# Phase 14 — Final Validation

Validated

```
Cloud Build
```

Validated

```
Artifact Registry
```

Validated

```
Cloud Run
```

Validated

```
FastAPI
```

Validated

```
OpenAPI
```

Validated

```
Sessions
```

Validated

```
SSE
```

Validated

```
Streaming
```

Validated

```
Market Scanner
```

Validated

```
Sentiment Analyzer
```

Validated

```
Pricing Intelligence
```

Validated

```
Report Generator
```

Validated

```
Render UI
```

---

# Final Working Flow

```text
User
 │
 ▼
Render UI
 │
 ▼
Cloud Run Host
 │
 ├────────► Market Scanner
 │
 ├────────► Sentiment Analyzer
 │
 ├────────► Pricing Intelligence
 │
 └────────► Report Generator
 │
 ▼
Markdown Report
 │
 ▼
Browser
```

---

# Biggest Lessons Learned

## 1

Never guess.

Always inspect logs.

---

## 2

Cloud Build logs are the first place to investigate.

---

## 3

Verify which Service Account is actually executing.

---

## 4

Debug one microservice before debugging the platform.

---

## 5

Separate

Infrastructure

from

Application

issues.

---

## 6

Use

```
curl
```

before debugging UI.

---

## 7

Cloud Run logs are the source of truth.

---

## 8

Fix problems layer by layer.

```text
Authentication

↓

Cloud Build

↓

Artifact Registry

↓

Docker

↓

Cloud Run

↓

IAM

↓

OpenAPI

↓

Sessions

↓

Streaming

↓

UI
```

---

# Final Outcome

Successfully deployed

✅ Market Scanner

✅ Sentiment Analyzer

✅ Pricing Intelligence

✅ Report Generator

✅ Competitive Intel Host

Successfully integrated

✅ Google ADK

✅ FastAPI

✅ Cloud Run

✅ Artifact Registry

✅ Cloud Build

✅ SSE Streaming

✅ Render

✅ Multi-Agent Orchestration

The browser now successfully orchestrates all specialist agents and produces the final competitive intelligence report end-to-end.