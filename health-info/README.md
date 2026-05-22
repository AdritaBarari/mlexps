# CalorIQ — Agentic Calorie Tracker

A personal, zero-cost health app that tracks calorie intake and expenditure, estimates macronutrients via LLM (Groq), calculates recipe nutrition, and sends WhatsApp alerts via Twilio.

## Stack
- **Backend**: FastAPI + SQLite + Groq (llama-3.1-8b-instant)
- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **WhatsApp**: Twilio sandbox (free)

---

## Quick Start

### 1. Backend

```bash
cd health-info/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Copy and fill in your keys
cp ../.env.example .env

uvicorn main:app --reload
# API docs: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd health-info/frontend
npm install
npm run dev
# App: http://localhost:5173
```

---

## WhatsApp Setup (optional)

1. Sign up at [twilio.com](https://www.twilio.com) (free)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. WhatsApp the Twilio sandbox number and send the join code
4. Fill `TWILIO_*` keys and `USER_WHATSAPP` in `.env`
5. For webhook: run `ngrok http 8000`, paste the URL into Twilio sandbox webhook as `https://your-ngrok-url/webhook/whatsapp`

### WhatsApp commands
| Message | Action |
|---------|--------|
| `had 2 rotis and dal for lunch` | Log meal |
| `walked 8000 steps` | Log activity |
| `recipe: palak paneer - 200g paneer, 500g spinach` | Calculate recipe |
| `how am I doing today?` | Get daily summary |

---

## Features
- **Dashboard**: calorie ring, 7-day trend, macro bars, today's log
- **Log Meal**: natural language food entry, AI nutrition estimation
- **Activity**: manual step/workout logging with calorie burn estimate
- **Recipe Calculator**: paste any recipe → per-serving nutrition
- **Settings**: customise daily goals, WhatsApp number
- **Alerts**: WhatsApp warning at 90% and 100% of daily calorie goal
