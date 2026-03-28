# Sales Coach Platform

AI-powered sales training platform for commercial insurance producers selling to contractors and the construction industry.

## Features

- **Voice Practice** - Real-time speech-to-speech practice calls using Grok Voice Agent API
- **Dynamic Personas** - AI generates realistic contractor prospects with varied personalities and objections
- **AI Scoring** - GPT-4 powered call analysis scoring sales skills and technical knowledge
- **Progress Tracking** - Dashboard with skill trends, recommendations, and performance metrics

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐     WebSocket      ┌─────────────────┐
│   Next.js       │◄──────────────────►│   FastAPI       │◄──────────────────►│   Grok Voice    │
│   Frontend      │                    │   Backend       │                    │   API (x.ai)    │
└─────────────────┘                    └─────────────────┘                    └─────────────────┘
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │         PostgreSQL            │
                              └───────────────────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Recharts
- **Backend**: Python FastAPI, SQLAlchemy, WebSockets
- **Database**: PostgreSQL
- **Voice**: Grok Voice Agent API (xAI)
- **Analysis**: OpenAI GPT-4

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL
- Grok API key (xAI)
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys and database URL

# Initialize database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Seed with sample data
python -m scripts.seed_data

# Run server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database Setup

```bash
# Create PostgreSQL database
createdb sales_coach

# Or using psql
psql -c "CREATE DATABASE sales_coach;"
```

## Environment Variables

### Backend (.env)

```env
XAI_API_KEY=your-xai-api-key
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sales_coach

# Optional S3 for audio storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_RECORDINGS_BUCKET=sales-coach-recordings
```

## Usage

1. Start the backend server: `uvicorn app.main:app --reload`
2. Start the frontend: `npm run dev`
3. Open http://localhost:3000
4. Click "Start Practice Call" on the dashboard
5. Select a scenario, prospect trade, and difficulty
6. Click "Start Call" and begin speaking
7. After the call, view your score and recommendations

## Call Scenarios

The platform includes 14 scenario types:
- Cold calls (job site visit, phone prospecting, networking follow-up)
- Warm leads (web inquiry, referral, GC requirement)
- Renewals (competitive defense, premium increase)
- Cross-sells (workers comp, builder's risk)
- Claims (first notice, claim frustration)
- Reviews (annual review, onboarding)

## Scoring Rubric

### Sales Skills (60% weight)
- Discovery/Needs Assessment (20%)
- Objection Handling (20%)
- Building Rapport (15%)
- Closing Techniques (15%)
- Active Listening (15%)
- Value Proposition (15%)

### Technical Knowledge (40% weight)
- Insurance Terminology (15%)
- Product Knowledge (25%)
- Construction Industry Risks (25%)
- Quoting/Coverage Discussions (20%)
- Regulatory Compliance (15%)

## API Endpoints

### Sessions
- `POST /api/sessions/` - Create new practice session
- `GET /api/sessions/` - List sessions
- `GET /api/sessions/{uuid}` - Get session details

### Scenarios
- `GET /api/scenarios/templates` - List scenario templates
- `GET /api/scenarios/business-contexts` - List trades/industries

### Analytics
- `GET /api/analytics/dashboard` - Dashboard summary
- `GET /api/analytics/session/{uuid}/score` - Session score details
- `GET /api/analytics/progress` - Progress over time

### WebSocket
- `WS /ws/voice/{session_uuid}` - Voice practice connection

## Project Structure

```
sales-coach-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/      # REST endpoints
│   │   │   └── websocket/   # Voice session handling
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy models
│   │   └── core/            # Config, database
│   ├── scripts/             # Seed data
│   └── alembic/             # Migrations
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Voice session hooks
│   │   └── lib/             # API client, utilities
│   └── public/
│       └── worklets/        # Audio processing
```

## License

MIT
