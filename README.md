# HireLog

A serverless job application tracker built on AWS — designed to demonstrate cloud-native backend architecture as a contrast to traditional containerized deployments.

Track job applications, auto-detect ghosted employers, and manage everything through a secure REST API — no servers to manage.

---

## Architecture

```
Client
  │
  ▼
API Gateway (HTTP API)
  │
  ├── POST   /auth/register   →  RegisterFunction  (Lambda)
  ├── POST   /auth/login      →  LoginFunction     (Lambda)
  ├── POST   /jobs            →  CreateJobFunction (Lambda)
  ├── GET    /jobs            →  GetJobsFunction   (Lambda)
  └── PATCH  /jobs/{job_id}   →  UpdateJobFunction (Lambda)

EventBridge Scheduler (daily cron)
  └── GhostCheckerFunction (Lambda) → scans + updates stale jobs

All Lambdas → DynamoDB (hirelog-users, hirelog-jobs)
```

**Stack:** Python 3.12 · AWS Lambda · API Gateway (HTTP) · DynamoDB · EventBridge Scheduler · AWS SAM · GitHub Actions

---

## Features

- **JWT Authentication** — stateless auth on every protected route via `Authorization: Bearer <token>` header
- **Bcrypt password hashing** — passwords are never stored in plain text
- **Ghost checker** — EventBridge cron runs daily and automatically flips stale `applied`/`interviewing` jobs to `ghosted` after 21 days of inactivity
- **Least-privilege IAM** — each Lambda only has permission to the exact DynamoDB operations it needs
- **CORS configured** — ready for a frontend to connect
- **CI/CD** — GitHub Actions runs `sam build` + `sam deploy` on every push to `main`

---

## Project Structure

```
HireLog/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
│
├── lambdas/
│   ├── auth/
│   │   ├── login.py            # POST /auth/login
│   │   └── register.py         # POST /auth/register
│   ├── jobs/
│   │   ├── create_job.py       # POST /jobs
│   │   ├── get_jobs.py         # GET  /jobs
│   │   └── update_job.py       # PATCH /jobs/{job_id}
│   └── scheduler/
│       └── ghost_checker.py    # EventBridge daily cron
│
├── shared/
│   ├── auth_helper.py          # JWT create/decode, @require_auth decorator, response helpers
│   └── db.py                   # All DynamoDB operations
│
├── template.yaml               # AWS SAM infrastructure-as-code
├── requirements.txt
└── .env                        # Local dev secrets (never committed)
```

---

## API Reference

All protected routes require the header:
```
Authorization: Bearer <token>
```

### Auth

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register` | Create account, returns JWT |
| POST | `/auth/login` | Verify credentials, returns JWT |

**Register / Login body:**
```json
{
  "email": "chris@example.com",
  "password": "yourpassword"
}
```

---

### Jobs

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/jobs` | Create a new job application |
| GET | `/jobs` | Get all your job applications |
| GET | `/jobs?status=applied` | Filter by status |
| PATCH | `/jobs/{job_id}` | Update a job application |

**POST /jobs body:**
```json
{
  "company": "Google",
  "role": "Backend Engineer",
  "status": "applied",
  "notes": "Referral from John",
  "next_step": "Technical screen",
  "follow_up_date": "2025-07-01"
}
```

Valid statuses: `applied` · `interviewing` · `offer` · `rejected` · `ghosted`

**PATCH /jobs/{job_id} body** (all fields optional):
```json
{
  "status": "interviewing",
  "notes": "Passed phone screen",
  "next_step": "Onsite interview",
  "follow_up_date": "2025-07-10"
}
```

---

## Local Development

**Prerequisites:** Python 3.12, AWS SAM CLI, AWS CLI configured

**1. Clone and install dependencies**
```bash
git clone https://github.com/your-username/hirelog.git
cd hirelog
pip install -r requirements.txt
```

**2. Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your values
```

`.env` variables:
```
AWS_REGION=us-east-1
USERS_TABLE_NAME=hirelog-users
JOBS_TABLE_NAME=hirelog-jobs
JWT_SECRET=your-super-secret-key-change-this
ALLOWED_ORIGIN=*
```

**3. Build and deploy**
```bash
sam build
sam deploy --guided   # first time — walks you through setup
sam deploy            # every time after
```

`--guided` will ask for stack name, region, and parameter values (JWT secret, allowed origin). It saves your choices to `samconfig.toml` for future deploys.

---

## CI/CD

Every push to `main` automatically triggers a GitHub Actions workflow that builds and deploys to AWS.

**Required GitHub Secrets** (Settings → Secrets and variables → Actions):

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `JWT_SECRET` | Secret used to sign JWTs |
| `ALLOWED_ORIGIN` | Frontend domain (or `*` for dev) |

---

## DynamoDB Schema

**hirelog-users**
| Field | Type | Key |
|-------|------|-----|
| `email` | String | Partition key |
| `user_id` | String | — |
| `password` | String (bcrypt hash) | — |

**hirelog-jobs**
| Field | Type | Key |
|-------|------|-----|
| `job_id` | String | Partition key |
| `user_id` | String | GSI partition key (`user_id-index`) |
| `company` | String | — |
| `role` | String | — |
| `status` | String | — |
| `notes` | String | — |
| `next_step` | String | — |
| `follow_up_date` | String | — |
| `created_at` | String (ISO 8601) | — |
| `updated_at` | String (ISO 8601) | — |

---

## Related Projects

**[OCR REST API](https://github.com/ChrisNg333/ocr-api)** — Containerized backend built with FastAPI, PostgreSQL, and Docker. Together these two projects demonstrate contrasting backend paradigms: traditional containerized deployment vs. serverless cloud-native architecture.
