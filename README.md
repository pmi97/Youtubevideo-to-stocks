# YouTube Video to Stocks Analyzer

Analyze YouTube investment videos and extract mentioned companies, sentiment, and presenter watchlists using AI.

> ⚠️ **Live Demo**: Try it at [https://d212hr2avz45hq.cloudfront.net](https://d212hr2avz45hq.cloudfront.net)  
> *(Available for limited time only)*

## Demo

<!-- TODO: Add demo GIF -->
![Demo](docs/demo.gif)

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, TailwindCSS, Vite |
| **Backend** | Python, FastAPI, LiteLLM |
| **Database** | DynamoDB (local/AWS) |
| **AI** | Google Gemini via LiteLLM |
| **Infra** | Docker, Terraform, AWS Lambda |

---

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- API Keys:
  - [Google AI Studio](https://aistudio.google.com/) (Gemini)
  - [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com)

### 1. Clone & Configure
```bash
git clone https://github.com/pmi97/Youtubevideo-to-stocks.git
cd Youtubevideo-to-stocks

cp .env.example .env
# Edit .env with your API keys
```

### 2. Run
```bash
docker-compose up -d --build
```

### 3. Open
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001

---

## AWS Deployment

### Prerequisites

1. **AWS Account** with IAM user configured
2. **API Keys** (same as local):
   - Gemini API key
   - YouTube Data API key
3. **Webshare Account** (for YouTube transcript fetching)
   - YouTube blocks cloud IPs, so a residential proxy is required
   - Sign up at [webshare.io](https://www.webshare.io/) (free tier: 10 proxies)
   - Get your proxy username/password from [Proxy Settings](https://dashboard.webshare.io/proxy/settings)
4. **Tools installed**:
   - AWS CLI (configured with credentials)
   - Terraform
   - Docker

### IAM Setup

Attach the `TerraformDeployPolicy` to your IAM user. See [docs/terraform-deploy-policy.md](docs/terraform-deploy-policy.md) for the full policy JSON.

### Deployment Steps

#### 1. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
GEMINI_API_KEY=your_gemini_key
YOUTUBE_API_KEY=your_youtube_key
FROM_EMAIL=your_email@gmail.com
SMTP_PASS=your_app_password
WEBSHARE_PROXY_USERNAME=your_webshare_username
WEBSHARE_PROXY_PASSWORD=your_webshare_password
```

#### 2. First-Time Deployment
```bash
./deploy.sh --init
```

This will:
1. Initialize Terraform
2. Create ECR repository (you'll approve)
3. Build and push Docker image
4. Create remaining infrastructure (you'll approve)
5. Build and deploy frontend

#### 3. Subsequent Deployments

After code changes:
```bash
./deploy.sh
```

### Tear Down

To destroy all AWS resources:
```bash
cd infrastructure
terraform destroy -var="alert_email=your@email.com"
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze-video` | Analyze a single YouTube video |
| POST | `/api/subscribe` | Subscribe to channel notifications |
| GET | `/api/subscriptions?email=` | Get subscriptions for an email |
| DELETE | `/api/unsubscribe?email=` | Unsubscribe from notifications |

## Project Structure

```
├── backend/          # FastAPI + LiteLLM
├── frontend/         # React + Vite
├── infrastructure/   # Terraform (AWS)
├── docs/             # Documentation
└── docker-compose.yml
```

## License

MIT
