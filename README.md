# ProCom • AI-Integrated Communication Platform

> Enterprise-grade communication platform with real-time messaging, WebRTC audio/video calling, AI-powered NLP reminder extraction, meeting scheduling with RSVP tracking, communities & broadcast channels, and Neon Cloud PostgreSQL.

## ✨ Features

- **🔥 Real-Time Messaging** — WebSocket-powered instant messaging across DMs, groups, communities & broadcasts
- **📹 WebRTC Video/Audio Calling** — HD peer-to-peer calls with screen sharing and AI transcription notes
- **🤖 AI NLP Reminder Engine** — Automatically extracts deadlines, meetings and tasks from natural language messages
- **📅 Calendar & Meeting Scheduler** — Schedule meetings with unique join codes, RSVP tracking, and auto-reminders
- **🌐 Organization Directory** — Search users by #user_id, name, department; search messages and files
- **👥 Groups, Communities & Broadcasts** — Multi-channel community spaces with organized channels
- **📎 File & Photo Uploads** — Share images, documents with inline preview in chat
- **🎨 7 Variable Themes + Custom Colors** — Dark Obsidian, Light Slate, Midnight Blue, Forest, Sunset, Rose, Ocean, and custom color picker
- **⚡ Neon Cloud PostgreSQL** — Production-ready with Neon database + SQLite fallback
- **🔔 Toast Notification System** — Elegant toast notifications for all platform events

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy, Uvicorn |
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Database | Neon Cloud PostgreSQL (with SQLite fallback) |
| Real-Time | WebSockets, WebRTC |
| AI/NLP | Custom NLP engine (Python) |
| Deployment | Vercel (serverless) |

## 🚀 Local Development

### 1. Clone & Install
```bash
git clone https://github.com/felix-10fb/ProConnect.git
cd ProConnect
pip install -r requirements.txt
```

### 2. Configure Database
Create a `.env` file in the project root:
```bash
DATABASE_URL=postgresql://neondb_owner:password@ep-xyz.neon.tech/neondb?sslmode=require
PORT=8000
HOST=0.0.0.0
```
> Without `DATABASE_URL`, the app falls back to local SQLite automatically.

### 3. Run
```bash
python run.py
```
Open **http://localhost:8000** — you'll see the ProCom splash login screen.

## ☁️ Vercel Deployment

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Set Environment Variables
In your Vercel project settings, add:
- `DATABASE_URL` → Your Neon PostgreSQL connection string

### 3. Deploy
```bash
vercel --prod
```

The `vercel.json` is pre-configured to:
- Route `/api/*` to the Python FastAPI serverless function
- Serve frontend static files from `frontend/`
- Support SPA routing

> **Note**: WebSocket connections (for real-time messaging & calling) require a persistent server and won't work in Vercel's serverless environment. The REST API, file uploads, NLP analysis, and all CRUD operations work perfectly on Vercel.

## 📁 Project Structure

```
ProConnect/
├── api/
│   └── index.py          # Vercel serverless entry point
├── backend/
│   ├── main.py           # FastAPI app (routes, WebSocket, endpoints)
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── database.py        # Database engine (Neon PostgreSQL + SQLite fallback)
│   ├── nlp_engine.py      # AI reminder extraction engine
│   ├── seed_data.py       # Demo data seeder
│   └── uploads/           # Uploaded files storage
├── frontend/
│   ├── index.html         # SPA entry (splash screen, chat, calendar, settings)
│   ├── css/style.css      # 7 theme presets + custom color system
│   └── js/
│       ├── api.js         # REST API client
│       ├── app.js         # Main controller (themes, auth, messaging, settings)
│       ├── ws.js          # WebSocket real-time engine
│       ├── webrtc.js      # WebRTC calling engine
│       ├── calendar.js    # Calendar & meetings manager
│       ├── reminders.js   # AI reminders manager
│       └── sound.js       # Notification sounds
├── vercel.json            # Vercel deployment configuration
├── requirements.txt       # Python dependencies
├── run.py                 # Local development server
└── .env                   # Environment variables (not tracked)
```

## 🎨 Theme System

ProCom includes **7 built-in themes** and a **custom color picker**:

| Theme | Description |
|-------|------------|
| Dark Obsidian | Default dark theme with indigo/cyan accents |
| Light Slate | Clean light theme |
| Midnight Blue | Deep blue with azure accents |
| Forest | Dark green with emerald tones |
| Sunset | Warm orange/amber palette |
| Rose | Pink/magenta dark theme |
| Ocean | Teal/cyan deep water palette |
| Custom | User-defined primary, background, surface, and accent colors |

Themes persist across sessions via `localStorage`.

## 📄 License

MIT License — Built with ❤️ for ProCom Organization

---

**Organization**: ProCom | **Platform Version**: 2.5.0 | **AI Engine**: Active
