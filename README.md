# Dispute Autopsy

AI-assisted payment dispute investigator. A deterministic rule engine scores
the evidence (payment, order, delivery, refund, support) and produces a
CONTEST / REVIEW / ACCEPT recommendation; an LLM only explains that decision
in plain language — it never sets the score or the outcome itself.

## What changed in this upgrade

- `backend/data/disputes.json` is now a real list (4 sample disputes covering
  CONTEST, REVIEW, ACCEPT, and the "refund already issued" edge case) instead
  of a single hardcoded object.
- `backend/main.py` looks up disputes by ID for real, adds a `GET /disputes`
  endpoint for the inbox list, and adds CORS middleware so the frontend can
  actually call it.
- `backend/investigator.py`: a refund already issued now forces `ACCEPT`
  regardless of score (contesting a dispute you already refunded doesn't make
  sense), and weak/missing evidence is now surfaced explicitly instead of
  silently contributing nothing.
- `frontend/src/app/page.tsx` fetches the dispute list from the backend
  instead of hardcoding one dispute, and reads the API URL from
  `NEXT_PUBLIC_API_URL` instead of a hardcoded `127.0.0.1:8000`.

## Run it

**Backend**
```
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env             # then add your GROQ_API_KEY (free at console.groq.com — optional, falls back to a local report generator without it)
uvicorn main:app --reload
```

**Frontend**
```
cd frontend
npm install
cp .env.local.example .env.local   # edit if your backend isn't on 127.0.0.1:8000
npm run dev
```

Open http://localhost:3000, pick a dispute from the inbox, and it calls
`GET /autopsy/{dispute_id}` on the backend.

## AI provider

This uses **Groq** (free tier, OpenAI-compatible endpoint) instead of OpenAI —
get a key at https://console.groq.com and put it in `backend/.env` as
`GROQ_API_KEY=...`. Don't commit that file. Without a key, the app still
works fully — it just uses a local, rule-based report generator instead of
an LLM-written narrative.
