# 🚀 DTM-CHATSPACE • AI-Integrated Communication Platform

A next-generation real-time collaboration and communication platform featuring **audio/video calling**, **calendar meeting scheduling**, **automatic AI reminder extraction from text**, and structured spaces (**Groups**, **Communities with sub-channels**, and **Broadcasts**), backed by **Python (FastAPI)** and **Neon Cloud PostgreSQL**.

---

## 🌟 Key Features

### 1. 🤖 Intelligent AI Text Analysis & Auto-Scheduling Engine
- **Text-to-Reminder Engine**: Monitors chat messages, discussions, and text inputs in real-time.
- **Entity & Temporal Extraction**: Detects dates (*"tomorrow at 5pm"*, *"this Friday at 3:00 PM"*, *"in 2 hours"*), action intents (*"submit report"*, *"review PR"*, *"emergency server maintenance"*), and urgency/priority levels (*High*, *Medium*, *Low*).
- **Automated Scheduling**: Automatically inserts extracted tasks into the user's Reminders & Calendar without manual entry, or renders interactive **"AI Action Detected" cards** with 1-click scheduling.
- **NLP Text Scanner Playground**: Interactive laboratory in the UI where users can paste any arbitrary email or message and watch the AI extract and schedule reminders in real-time.
- **Workspace Copilot (`@AI`)**: Tag `@AI` in any chat to request conversation summaries (`@AI summarize`), meeting agendas (`@AI create agenda`), and draft replies.

### 2. 📞 Audio & Video Calling (WebRTC Conference Suite)
- **High-Definition Calling**: Peer-to-peer WebRTC video and voice channels with fallback canvas streams.
- **Rich Call Controls**: Camera on/off, microphone mute/unmute, screen sharing (`getDisplayMedia`), and call duration timer.
- **Interactive Sound Synthesizer**: Web Audio API generated ringtones (outgoing rings, incoming melodies, connect beeps, hangup tones) with zero external media files.
- **Live AI Call Notes & Transcripts**: Generates real-time meeting notes and captures action items during the call.
- **Call Session Logging**: Automatically stores call logs and durations in the database.

### 3. 📅 Interactive Calendar & Meeting Scheduling
- **Visual Calendar**: Monthly interactive calendar with event indicators and day selection.
- **Meeting Management**: Schedule video/audio calls with custom codes, dates, times, and agendas.
- **Live RSVPs**: Team members can mark status as *Going*, *Maybe*, or *Declined* with real-time attendee counts.
- **1-Click Room Join**: Directly enter conference video calls from the calendar.

### 4. 👥 Groups, Communities & Broadcast Channels
- **Direct Messages (1-on-1)**: Private communication with online presence indicators.
- **Collaborative Groups**: Multi-user team channels for engineering, design, and operations.
- **Communities**: Discord/Slack-style organization spaces with categorized sub-channels (`#announcements`, `#general-chat`, `#neon-postgresql`, `#stage-audio-video`).
- **Broadcast Channels**: 1-to-many official announcement feeds with styled cards and release notes.

### 5. ⚡ Neon Cloud PostgreSQL & Resilient Database
- Native support for **Neon PostgreSQL** via `DATABASE_URL` in `.env`.
- Connection pooling, SSL enforcement (`sslmode=require`), and automatic sequence synchronization.
- **Zero-Downtime Fallback**: If offline or if credentials are misconfigured, gracefully falls back to local SQLite with identical schemas.
- In-app Database Settings Modal to test, monitor, and update your Neon connection string dynamically.

---

## 🛠️ Architecture & Tech Stack

- **Backend**: Python 3.13 + FastAPI + Uvicorn
- **ORM & Database**: SQLAlchemy 2.0 + psycopg2-binary + Neon Cloud PostgreSQL
- **Real-Time Communication**: WebSockets (`/ws/{user_id}`) for messaging, presence, and WebRTC signaling
- **Frontend**: Vanilla HTML5, CSS3 (Ultra-modern glassmorphic dark theme, CSS custom properties, responsive grid), Vanilla JavaScript ES6+
- **Audio**: Web Audio API Sound Synthesis

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure Python 3.10+ is installed:
```bash
python --version
pip --version
```

### 2. Database Setup (Neon PostgreSQL)
Your Neon PostgreSQL connection string is pre-configured in `.env`:
```env
DATABASE_URL=postgresql://neondb_owner:npg_5XeHTZLVw1Oo@ep-delicate-fire-b4s8apcf-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require
PORT=8000
HOST=0.0.0.0
```

### 3. Launch the Platform
Run the launcher:
```bash
python run.py
```

### 4. Open in Browser
Open your browser and navigate to:
```
http://localhost:8000
```
- **Interactive UI**: `http://localhost:8000`
- **Interactive API Swagger Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing the Core Features

1. **AI Text Reminder Auto-Scheduling**:
   - Open a chat with Sarah Chen or Core Engineering.
   - Type: `"Need to submit the final security audit report tomorrow at 5pm urgent"` and hit Enter.
   - Notice the **AI Action Detected** badge with High Priority and auto-scheduled reminder tag.
   - Switch to the **Reminders** tab on the left rail to see the countdown timer and manage the task!

2. **Video & Audio Calling**:
   - In any chat, click the **"Video Call"** button in the header.
   - Experience the incoming/outgoing ringtones, active video feeds, mute toggle, screen share, and live AI notes drawer.

3. **Calendar & Meeting RSVPs**:
   - Click the **Calendar** tab on the left rail.
   - Click **"+ Schedule Meeting"** to create a meeting or click **"Going" / "Maybe"** on existing meetings.
   - Click **"🎥 Join Room"** to instantly launch the meeting conference.

4. **Switching User Profiles**:
   - Use the profile selector in the top-right header to switch between *Alex Morgan*, *Sarah Chen*, *Marcus Vance*, and *Elena Rostova* to test multi-party collaboration and RSVPs!
