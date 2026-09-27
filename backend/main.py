import os
import json
import uuid
import datetime
import shutil
from typing import Dict, List, Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import engine, get_db, SessionLocal, Base, get_db_status, NEON_DATABASE_URL
from backend.models import User, Conversation, ConversationMember, CommunityChannel, Message, Reminder, Meeting, CallLog
from backend.schemas import (
    UserResponse, ConversationCreate, ConversationResponse,
    MessageCreate, MessageResponse, ReminderCreate, ReminderResponse, ReminderUpdate,
    MeetingCreate, MeetingResponse, MeetingRSVP, TextAnalysisRequest, TextAnalysisResponse,
    CallInitiateRequest, CallLogResponse, LoginRequest, RegisterRequest, EmojiReactionRequest
)
from backend.nlp_engine import IntelligentReminderExtractor, WorkspaceAIAssistant
from backend.seed_data import seed_database

# Create uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize seed data
with SessionLocal() as db:
    seed_database(db)

app = FastAPI(
    title="ProCom • AI-Integrated Communication Platform",
    description="Enterprise AI collaboration platform with calling, auto-reminders, meeting scheduling, organization search, communities, and Neon PostgreSQL",
    version="2.5.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static folder
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# -------------------------------------------------------------
# WebSocket Connection & Real-Time Signaling Manager
# -------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self.broadcast_status(user_id, "online")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception:
                self.disconnect(user_id)

    async def broadcast(self, message: dict, exclude_user_id: Optional[int] = None):
        for uid, conn in list(self.active_connections.items()):
            if exclude_user_id is not None and uid == exclude_user_id:
                continue
            try:
                await conn.send_json(message)
            except Exception:
                self.disconnect(uid)

    async def broadcast_status(self, user_id: int, status: str):
        await self.broadcast({
            "type": "presence_update",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "chat_message")

            # WebRTC Signaling Relay
            if event_type in ["call_offer", "call_answer", "ice_candidate", "call_reject", "call_end", "call_ringing"]:
                target_user_id = data.get("target_user_id")
                target_conv_id = data.get("conversation_id")
                
                payload = {
                    "type": event_type,
                    "sender_id": user_id,
                    "sender_name": data.get("sender_name", f"User {user_id}"),
                    "conversation_id": target_conv_id,
                    "call_type": data.get("call_type", "video"),
                    "data": data.get("data", {})
                }

                if target_user_id and target_user_id in manager.active_connections:
                    await manager.send_personal_message(payload, target_user_id)
                elif target_conv_id:
                    await manager.broadcast(payload, exclude_user_id=user_id)

            elif event_type == "typing":
                conv_id = data.get("conversation_id")
                await manager.broadcast({
                    "type": "typing",
                    "user_id": user_id,
                    "conversation_id": conv_id,
                    "is_typing": data.get("is_typing", True)
                }, exclude_user_id=user_id)

            elif event_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast_status(user_id, "offline")
    except Exception:
        manager.disconnect(user_id)

# -------------------------------------------------------------
# Database Diagnostics & Configuration Endpoints
# -------------------------------------------------------------
@app.get("/api/database/status")
def database_status(db: Session = Depends(get_db)):
    status = get_db_status()
    status["user_count"] = db.query(User).count()
    status["conversation_count"] = db.query(Conversation).count()
    status["message_count"] = db.query(Message).count()
    status["reminder_count"] = db.query(Reminder).count()
    status["meeting_count"] = db.query(Meeting).count()
    status["organization"] = "ProCom"
    return status

@app.post("/api/database/configure")
def configure_database(payload: dict):
    new_url = payload.get("database_url", "").strip()
    if not new_url:
        raise HTTPException(status_code=400, detail="Database URL cannot be empty")
    
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "w") as f:
        f.write(f"DATABASE_URL={new_url}\nPORT=8000\nHOST=0.0.0.0\n")
        
    return {
        "success": True,
        "message": "Database URL saved to backend/.env. Please restart the server to switch to your Neon database!",
        "database_url": new_url[:20] + "..." if len(new_url) > 20 else new_url
    }

# -------------------------------------------------------------
# Authentication & ProCom Organization Directory
# -------------------------------------------------------------
@app.post("/api/auth/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = None
    if payload.user_id:
        user = db.query(User).filter(User.id == payload.user_id).first()
    elif payload.username_or_email:
        query = payload.username_or_email.strip()
        user = db.query(User).filter(
            or_(User.username == query, User.email == query)
        ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found in ProCom directory. Check user_id or register.")
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "avatar": user.avatar,
        "department": getattr(user, 'department', 'Engineering') or 'Engineering',
        "organization": "ProCom",
        "status": user.status
    }

@app.post("/api/auth/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing = db.query(User).filter(or_(User.username == payload.username, User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered in ProCom.")

    avatar = payload.avatar
    if not avatar:
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={payload.username}"

    new_user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        avatar=avatar,
        department=payload.department or "Engineering",
        organization="ProCom",
        status="online",
        status_text="ProCom Team Member"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Automatically add to default ProCom Community & Group
    for conv_id in [2, 3]:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            member = ConversationMember(conversation_id=conv_id, user_id=new_user.id, role="member")
            db.add(member)
    db.commit()

    return {
        "id": new_user.id,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "email": new_user.email,
        "avatar": new_user.avatar,
        "department": new_user.department,
        "organization": new_user.organization,
        "status": new_user.status
    }

# -------------------------------------------------------------
# File & Custom Photo Upload Endpoints
# -------------------------------------------------------------
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Ensure safe filename with UUID prefix
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    file_url = f"/uploads/{unique_name}"

    is_image = file_ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]
    file_type = "image" if is_image else "document"

    return {
        "url": file_url,
        "original_name": file.filename,
        "file_name": unique_name,
        "file_type": file_type,
        "file_size": file_size,
        "is_image": is_image
    }

@app.post("/api/users/{user_id}/avatar")
async def upload_user_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.avatar = f"/uploads/{unique_name}"
    db.commit()
    db.refresh(user)

    return {"id": user.id, "avatar": user.avatar}

# -------------------------------------------------------------
# Organization Search (Users by user_id/name/dept, Channels, Messages)
# -------------------------------------------------------------
@app.get("/api/search")
def organization_search(q: str = Query("", min_length=1), org: str = "ProCom", db: Session = Depends(get_db)):
    query_str = q.strip().lower()
    
    # 1. Search Users / Members
    users_query = db.query(User)
    # Check if query is numeric (search by user_id)
    if query_str.isdigit():
        users = users_query.filter(User.id == int(query_str)).all()
    elif query_str.startswith("#") and query_str[1:].isdigit():
        users = users_query.filter(User.id == int(query_str[1:])).all()
    else:
        users = users_query.filter(
            or_(
                User.full_name.ilike(f"%{query_str}%"),
                User.username.ilike(f"%{query_str}%"),
                User.email.ilike(f"%{query_str}%"),
                User.department.ilike(f"%{query_str}%")
            )
        ).limit(10).all()

    # 2. Search Conversations & Channels
    convs = db.query(Conversation).filter(
        or_(
            Conversation.title.ilike(f"%{query_str}%"),
            Conversation.description.ilike(f"%{query_str}%")
        )
    ).limit(8).all()

    # 3. Search Messages & Files
    messages = db.query(Message).filter(
        or_(
            Message.content.ilike(f"%{query_str}%"),
            Message.file_name.ilike(f"%{query_str}%")
        )
    ).order_by(desc(Message.created_at)).limit(10).all()

    # 4. Search Reminders
    reminders = db.query(Reminder).filter(
        Reminder.title.ilike(f"%{query_str}%")
    ).limit(5).all()

    # 5. Search Meetings
    meetings = db.query(Meeting).filter(
        Meeting.title.ilike(f"%{query_str}%")
    ).limit(5).all()

    return {
        "organization": "ProCom",
        "query": q,
        "users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "department": getattr(u, 'department', 'Engineering') or 'Engineering',
                "status": u.status
            }
            for u in users
        ],
        "conversations": [
            {"id": c.id, "title": c.title, "type": c.type, "description": c.description}
            for c in convs
        ],
        "messages": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "content": m.content,
                "file_url": getattr(m, 'file_url', ''),
                "file_name": getattr(m, 'file_name', ''),
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ],
        "reminders": [{"id": r.id, "title": r.title, "due_date": r.due_date.isoformat()} for r in reminders],
        "meetings": [{"id": mt.id, "title": mt.title, "start_time": mt.start_time.isoformat()} for mt in meetings]
    }

# -------------------------------------------------------------
# User Profile Endpoints
# -------------------------------------------------------------
@app.get("/api/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# -------------------------------------------------------------
# Conversation Endpoints (DMs, Groups, Communities, Broadcasts)
# -------------------------------------------------------------
@app.get("/api/conversations")
def get_conversations(db: Session = Depends(get_db)):
    convs = db.query(Conversation).all()
    results = []
    for c in convs:
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(desc(Message.created_at)).first()
        channels = db.query(CommunityChannel).filter(CommunityChannel.conversation_id == c.id).order_by(CommunityChannel.position).all()
        member_count = db.query(ConversationMember).filter(ConversationMember.conversation_id == c.id).count()

        results.append({
            "id": c.id,
            "title": c.title,
            "type": c.type,
            "description": c.description,
            "avatar": c.avatar,
            "icon": c.icon,
            "member_count": member_count,
            "channels": [
                {"id": ch.id, "name": ch.name, "topic": ch.topic, "channel_type": ch.channel_type}
                for ch in channels
            ],
            "last_message": last_msg.content if last_msg else None,
            "last_message_time": last_msg.created_at.isoformat() if last_msg else None,
            "created_at": c.created_at.isoformat()
        })
    return results

@app.post("/api/conversations")
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    new_conv = Conversation(
        title=payload.title,
        type=payload.type,
        description=payload.description or "",
        avatar=payload.avatar or "",
        icon=payload.icon or ("globe" if payload.type == "community" else "users" if payload.type == "group" else "radio" if payload.type == "broadcast" else "chat")
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)

    if payload.type == "community":
        channels = payload.initial_channels or ["announcements", "general", "resources"]
        for idx, ch_name in enumerate(channels):
            ch_type = "announcements" if ch_name == "announcements" else "text"
            channel = CommunityChannel(
                conversation_id=new_conv.id,
                name=ch_name,
                topic=f"{ch_name.replace('-', ' ').title()} channel",
                channel_type=ch_type,
                position=idx + 1
            )
            db.add(channel)

    members = payload.member_ids or [1]
    if 1 not in members:
        members.append(1)
    for uid in members:
        member = ConversationMember(
            conversation_id=new_conv.id,
            user_id=uid,
            role="owner" if uid == 1 else "member"
        )
        db.add(member)

    welcome_msg = Message(
        conversation_id=new_conv.id,
        sender_id=5,  # Nova AI
        content=f"🚀 Welcome to **{new_conv.title}**! ProCom space initialized.",
        message_type="system"
    )
    db.add(welcome_msg)
    db.commit()

    return {"id": new_conv.id, "title": new_conv.title, "type": new_conv.type}

@app.post("/api/conversations/{conv_id}/channels")
def add_channel(conv_id: int, payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name", "").strip().lower().replace(" ", "-")
    topic = payload.get("topic", "")
    ch_type = payload.get("channel_type", "text")
    if not name:
        raise HTTPException(status_code=400, detail="Channel name is required")

    ch = CommunityChannel(
        conversation_id=conv_id,
        name=name,
        topic=topic,
        channel_type=ch_type
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return {"id": ch.id, "name": ch.name, "topic": ch.topic, "channel_type": ch.channel_type}

# -------------------------------------------------------------
# Messages & AI Text Analysis / File Sharing
# -------------------------------------------------------------
@app.get("/api/conversations/{conv_id}/messages")
def get_messages(conv_id: int, channel_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Message).filter(Message.conversation_id == conv_id)
    if channel_id:
        query = query.filter(Message.channel_id == channel_id)
    messages = query.order_by(Message.created_at).all()

    res = []
    for m in messages:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        res.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "channel_id": m.channel_id,
            "sender_id": m.sender_id,
            "sender_name": sender.full_name if sender else "Unknown",
            "sender_avatar": sender.avatar if sender else "",
            "content": m.content,
            "message_type": m.message_type,
            "file_url": getattr(m, 'file_url', '') or '',
            "file_name": getattr(m, 'file_name', '') or '',
            "file_type": getattr(m, 'file_type', '') or '',
            "file_size": getattr(m, 'file_size', 0) or 0,
            "reactions": json.loads(getattr(m, 'reactions_json', '{}') or '{}'),
            "has_action_item": m.has_action_item,
            "action_item_json": m.action_item_json,
            "created_at": m.created_at.isoformat()
        })
    return res

@app.post("/api/messages")
async def send_message(payload: MessageCreate, db: Session = Depends(get_db)):
    # 1. Analyze text for action items
    extracted = IntelligentReminderExtractor.analyze_message(payload.content)
    has_action = extracted.get("detected", False)
    action_json_str = json.dumps(extracted) if has_action else ""

    # Message type determination
    msg_type = payload.message_type or "text"
    if payload.file_url:
        msg_type = "image" if payload.file_type == "image" else "file"

    msg = Message(
        conversation_id=payload.conversation_id,
        channel_id=payload.channel_id,
        sender_id=payload.sender_id,
        content=payload.content,
        message_type=msg_type,
        file_url=payload.file_url or "",
        file_name=payload.file_name or "",
        file_type=payload.file_type or "",
        file_size=payload.file_size or 0,
        reactions_json="{}",
        has_action_item=has_action,
        action_item_json=action_json_str
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    auto_reminder_obj = None

    # 2. Auto-schedule reminder if detected and requested
    if has_action and (payload.auto_schedule_reminder or extracted.get("confidence", 0) >= 0.75):
        due_dt = None
        if extracted.get("due_datetime"):
            try:
                due_dt = datetime.datetime.fromisoformat(extracted["due_datetime"])
            except Exception:
                due_dt = datetime.datetime.now() + datetime.timedelta(days=1)
        else:
            due_dt = datetime.datetime.now() + datetime.timedelta(days=1)

        reminder = Reminder(
            user_id=payload.sender_id,
            conversation_id=payload.conversation_id,
            source_message_id=msg.id,
            title=extracted.get("title", "Action Item"),
            description=f"Auto-extracted from message: \"{payload.content}\"",
            due_date=due_dt,
            priority=extracted.get("priority", "medium"),
            status="pending",
            auto_extracted=True,
            reminder_type=extracted.get("action_type", "task")
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        auto_reminder_obj = {
            "id": reminder.id,
            "title": reminder.title,
            "due_date": reminder.due_date.isoformat(),
            "priority": reminder.priority,
            "status": reminder.status,
            "auto_extracted": True
        }

    sender = db.query(User).filter(User.id == payload.sender_id).first()
    msg_dict = {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "channel_id": msg.channel_id,
        "sender_id": msg.sender_id,
        "sender_name": sender.full_name if sender else "Unknown",
        "sender_avatar": sender.avatar if sender else "",
        "content": msg.content,
        "message_type": msg.message_type,
        "file_url": msg.file_url,
        "file_name": msg.file_name,
        "file_type": msg.file_type,
        "file_size": msg.file_size,
        "reactions": {},
        "has_action_item": msg.has_action_item,
        "action_item": extracted if has_action else None,
        "auto_scheduled_reminder": auto_reminder_obj,
        "created_at": msg.created_at.isoformat()
    }

    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "new_message",
        "message": msg_dict
    })

    # Check for @AI trigger
    if "@ai" in payload.content.lower():
        ai_response = WorkspaceAIAssistant.process_query(payload.content)
        ai_msg = Message(
            conversation_id=payload.conversation_id,
            channel_id=payload.channel_id,
            sender_id=5,  # Nova AI
            content=ai_response["reply"],
            message_type="system"
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)

        ai_sender = db.query(User).filter(User.id == 5).first()
        ai_msg_dict = {
            "id": ai_msg.id,
            "conversation_id": ai_msg.conversation_id,
            "channel_id": ai_msg.channel_id,
            "sender_id": 5,
            "sender_name": ai_sender.full_name if ai_sender else "Nova AI",
            "sender_avatar": ai_sender.avatar if ai_sender else "",
            "content": ai_msg.content,
            "message_type": "system",
            "file_url": "",
            "file_name": "",
            "reactions": {},
            "has_action_item": False,
            "action_item": None,
            "created_at": ai_msg.created_at.isoformat()
        }
        await manager.broadcast({
            "type": "new_message",
            "message": ai_msg_dict
        })

    return msg_dict

@app.post("/api/messages/{message_id}/reactions")
async def toggle_message_reaction(message_id: int, payload: EmojiReactionRequest, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    reactions = json.loads(getattr(msg, 'reactions_json', '{}') or '{}')
    emoji = payload.emoji
    user_id = payload.user_id

    if emoji not in reactions:
        reactions[emoji] = [user_id]
    else:
        if user_id in reactions[emoji]:
            reactions[emoji].remove(user_id)
            if not reactions[emoji]:
                del reactions[emoji]
        else:
            reactions[emoji].append(user_id)

    msg.reactions_json = json.dumps(reactions)
    db.commit()

    # Broadcast reaction event
    await manager.broadcast({
        "type": "message_reaction",
        "message_id": message_id,
        "conversation_id": msg.conversation_id,
        "reactions": reactions
    })

    return {"message_id": message_id, "reactions": reactions}

# -------------------------------------------------------------
# NLP Engine Direct Test & Analysis Endpoint
# -------------------------------------------------------------
@app.post("/api/ai/analyze-text", response_model=TextAnalysisResponse)
def analyze_text(payload: TextAnalysisRequest, db: Session = Depends(get_db)):
    extracted = IntelligentReminderExtractor.analyze_message(payload.text, payload.reference_time)
    has_action = extracted.get("detected", False)
    
    reminder_id = None
    if has_action and payload.auto_schedule and payload.user_id:
        due_dt = None
        if extracted.get("due_datetime"):
            try:
                due_dt = datetime.datetime.fromisoformat(extracted["due_datetime"])
            except Exception:
                due_dt = datetime.datetime.now() + datetime.timedelta(days=1)
        else:
            due_dt = datetime.datetime.now() + datetime.timedelta(days=1)

        rem = Reminder(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            title=extracted.get("title", "Action Item"),
            description=f"Auto-extracted: {payload.text}",
            due_date=due_dt,
            priority=extracted.get("priority", "medium"),
            status="pending",
            auto_extracted=True,
            reminder_type=extracted.get("action_type", "task")
        )
        db.add(rem)
        db.commit()
        db.refresh(rem)
        reminder_id = rem.id

    return {
        "has_action": has_action,
        "action_item": extracted if has_action else None,
        "auto_scheduled": bool(reminder_id),
        "reminder_id": reminder_id,
        "summary": f"Detected {extracted.get('action_type', 'task')} due on {extracted.get('due_datetime', 'upcoming')}" if has_action else "No temporal commitments found.",
        "sentiment": "neutral"
    }

# -------------------------------------------------------------
# Reminders Endpoints
# -------------------------------------------------------------
@app.get("/api/reminders", response_model=List[ReminderResponse])
def get_reminders(user_id: Optional[int] = 1, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Reminder).filter(Reminder.user_id == user_id)
    if status:
        query = query.filter(Reminder.status == status)
    return query.order_by(Reminder.due_date).all()

@app.post("/api/reminders", response_model=ReminderResponse)
async def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    rem = Reminder(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        source_message_id=payload.source_message_id,
        title=payload.title,
        description=payload.description or "",
        due_date=payload.due_date,
        priority=payload.priority or "medium",
        status="pending",
        auto_extracted=payload.auto_extracted or False,
        reminder_type=payload.reminder_type or "task"
    )
    db.add(rem)
    db.commit()
    db.refresh(rem)

    await manager.broadcast({
        "type": "reminder_created",
        "reminder": {
            "id": rem.id,
            "title": rem.title,
            "due_date": rem.due_date.isoformat(),
            "priority": rem.priority,
            "status": rem.status,
            "auto_extracted": rem.auto_extracted
        }
    })

    return rem

@app.put("/api/reminders/{reminder_id}")
def update_reminder(reminder_id: int, payload: ReminderUpdate, db: Session = Depends(get_db)):
    rem = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not rem:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if payload.title is not None:
        rem.title = payload.title
    if payload.status is not None:
        rem.status = payload.status
    if payload.priority is not None:
        rem.priority = payload.priority
    if payload.due_date is not None:
        rem.due_date = payload.due_date

    db.commit()
    db.refresh(rem)
    return rem

@app.delete("/api/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    rem = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not rem:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(rem)
    db.commit()
    return {"success": True, "message": "Reminder deleted"}

# -------------------------------------------------------------
# Meetings & Calendar Endpoints
# -------------------------------------------------------------
@app.get("/api/meetings")
def get_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.start_time).all()
    results = []
    for m in meetings:
        host = db.query(User).filter(User.id == m.host_id).first()
        results.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "host_id": m.host_id,
            "host_name": host.full_name if host else "Unknown",
            "title": m.title,
            "description": m.description,
            "start_time": m.start_time.isoformat(),
            "end_time": m.end_time.isoformat(),
            "meeting_code": m.meeting_code,
            "meeting_type": m.meeting_type,
            "status": m.status,
            "rsvps": json.loads(m.rsvps_json or "{}"),
            "created_at": m.created_at.isoformat()
        })
    return results

@app.post("/api/meetings")
async def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    code = f"procom-{uuid.uuid4().hex[:6]}"
    mtg = Meeting(
        conversation_id=payload.conversation_id,
        host_id=payload.host_id,
        title=payload.title,
        description=payload.description or "",
        start_time=payload.start_time,
        end_time=payload.end_time,
        meeting_code=code,
        meeting_type=payload.meeting_type or "video",
        status="scheduled",
        rsvps_json=json.dumps({str(payload.host_id): "going"})
    )
    db.add(mtg)
    db.commit()
    db.refresh(mtg)

    rem = Reminder(
        user_id=payload.host_id,
        conversation_id=payload.conversation_id,
        title=f"ProCom Meeting: {mtg.title}",
        description=f"Join link: {code} | {mtg.description}",
        due_date=mtg.start_time,
        priority="high",
        status="pending",
        auto_extracted=False,
        reminder_type="meeting"
    )
    db.add(rem)
    db.commit()

    await manager.broadcast({
        "type": "new_meeting",
        "meeting": {
            "id": mtg.id,
            "title": mtg.title,
            "meeting_code": mtg.meeting_code,
            "start_time": mtg.start_time.isoformat(),
            "end_time": mtg.end_time.isoformat(),
            "meeting_type": mtg.meeting_type
        }
    })

    return {
        "id": mtg.id,
        "title": mtg.title,
        "meeting_code": mtg.meeting_code,
        "start_time": mtg.start_time.isoformat(),
        "end_time": mtg.end_time.isoformat(),
        "meeting_type": mtg.meeting_type
    }

@app.post("/api/meetings/{meeting_id}/rsvp")
def rsvp_meeting(meeting_id: int, payload: MeetingRSVP, db: Session = Depends(get_db)):
    mtg = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not mtg:
        raise HTTPException(status_code=404, detail="Meeting not found")

    rsvps = json.loads(mtg.rsvps_json or "{}")
    rsvps[str(payload.user_id)] = payload.status
    mtg.rsvps_json = json.dumps(rsvps)
    db.commit()
    return {"meeting_id": mtg.id, "rsvps": rsvps}

# -------------------------------------------------------------
# Calling & Call Logs Endpoints
# -------------------------------------------------------------
@app.post("/api/calls/log")
def log_call(payload: dict, db: Session = Depends(get_db)):
    log = CallLog(
        caller_id=payload.get("caller_id", 1),
        receiver_id=payload.get("receiver_id"),
        conversation_id=payload.get("conversation_id"),
        call_type=payload.get("call_type", "video"),
        status=payload.get("status", "completed"),
        duration_seconds=payload.get("duration_seconds", 0),
        notes=payload.get("notes", "")
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id, "status": "logged"}

@app.get("/api/calls/history")
def get_call_history(db: Session = Depends(get_db)):
    logs = db.query(CallLog).order_by(desc(CallLog.created_at)).limit(20).all()
    res = []
    for l in logs:
        caller = db.query(User).filter(User.id == l.caller_id).first()
        receiver = db.query(User).filter(User.id == l.receiver_id).first() if l.receiver_id else None
        res.append({
            "id": l.id,
            "caller_name": caller.full_name if caller else "Unknown",
            "receiver_name": receiver.full_name if receiver else "Group / Community Call",
            "call_type": l.call_type,
            "status": l.status,
            "duration_seconds": l.duration_seconds,
            "notes": l.notes,
            "created_at": l.created_at.isoformat()
        })
    return res

# -------------------------------------------------------------
# Frontend Static Files & SPA Route
# -------------------------------------------------------------
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"status": "ProCom Backend API Running", "docs": "/docs"})
