import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    avatar = Column(String(255), default="")
    status = Column(String(30), default="online")  # online, away, busy, offline
    status_text = Column(String(120), default="Available for calls and tasks")
    department = Column(String(100), default="Engineering")
    organization = Column(String(100), default="ProCom")
    is_bot = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="sender")
    memberships = relationship("ConversationMember", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    hosted_meetings = relationship("Meeting", back_populates="host")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    type = Column(String(30), default="direct")  # direct, group, community, broadcast
    description = Column(Text, default="")
    avatar = Column(String(255), default="")
    icon = Column(String(50), default="chat")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    channels = relationship("CommunityChannel", back_populates="community", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMember(Base):
    __tablename__ = "conversation_members"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(30), default="member")  # owner, admin, member
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User", back_populates="memberships")

class CommunityChannel(Base):
    __tablename__ = "community_channels"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    name = Column(String(60), nullable=False)
    topic = Column(String(200), default="")
    channel_type = Column(String(30), default="text")  # text, voice, announcements
    position = Column(Integer, default=0)

    community = relationship("Conversation", back_populates="channels")
    messages = relationship("Message", back_populates="channel")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("community_channels.id"), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(30), default="text")  # text, call_log, reminder_alert, system, broadcast, file, image
    file_url = Column(String(500), default="")
    file_name = Column(String(255), default="")
    file_type = Column(String(50), default="")
    file_size = Column(Integer, default=0)
    reactions_json = Column(Text, default="{}")  # {"👍": [1, 2], "🚀": [3]}
    has_action_item = Column(Boolean, default=False)
    action_item_json = Column(Text, default="")  # Stored JSON with extracted reminder/action details
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    channel = relationship("CommunityChannel", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    reminders = relationship("Reminder", back_populates="source_message")

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    source_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    due_date = Column(DateTime, nullable=False)
    priority = Column(String(20), default="medium")  # high, medium, low
    status = Column(String(20), default="pending")   # pending, completed, dismissed
    auto_extracted = Column(Boolean, default=False)
    reminder_type = Column(String(30), default="task")  # task, meeting, deadline, follow_up
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reminders")
    source_message = relationship("Message", back_populates="reminders")

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(180), nullable=False)
    description = Column(Text, default="")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    meeting_code = Column(String(50), unique=True, index=True, nullable=False)
    meeting_type = Column(String(20), default="video")  # video, audio
    status = Column(String(20), default="scheduled")    # scheduled, ongoing, completed, cancelled
    rsvps_json = Column(Text, default="{}")             # JSON mapping user_id -> status ('going', 'maybe', 'declined')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    host = relationship("User", back_populates="hosted_meetings")
    conversation = relationship("Conversation", back_populates="meetings")

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    call_type = Column(String(20), default="video")     # audio, video
    status = Column(String(20), default="completed")    # completed, missed, declined
    duration_seconds = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
