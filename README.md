# YouTube Video to Stocks Analyzer

Analyze YouTube investment videos and extract mentioned companies, sentiment, and presenter watchlists using AI.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, TailwindCSS, Vite |
| **Backend** | Python, FastAPI, LiteLLM |
| **Database** | DynamoDB (local/AWS) |
| **AI** | Google Gemini via LiteLLM |
| **Infra** | Docker, Terraform |

## Quick Start (Local)

### Prerequisites
- Docker & Docker Compose
- API Keys:
  - [Google AI Studio](https://aistudio.google.com/) (Gemini)
  - [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com)

### 1. Clone & Configure
```bash
git clone https://github.com/pmi97/Youtubevideo-to-stocks.git
cd Youtubevideo-to-stocks

# Create .env from template
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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze-video` | Analyze a single YouTube video |
| POST | `/api/subscribe` | Subscribe to channel notifications |
| GET | `/api/subscriptions?email=` | Get subscriptions for an email |
| DELETE | `/api/unsubscribe?email=` | Unsubscribe from notifications |
| POST | `/api/check-videos` | Manually trigger video check |

## Project Structure

```
├── backend/          # FastAPI + LiteLLM
├── frontend/         # React + Vite
├── infrastructure/   # Terraform (AWS)
└── docker-compose.yml
```

## AWS Deployment

> 🚧 **Coming Soon** — Terraform configuration for Lambda + S3/CloudFront deployment.

See `infrastructure/` for the Terraform modules.

## License

MIT
