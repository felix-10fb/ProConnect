from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    avatar: Optional[str] = ""
    status: Optional[str] = "online"
    status_text: Optional[str] = "Available for calls and tasks"
    department: Optional[str] = "Engineering"
    organization: Optional[str] = "ProCom"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_bot: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    user_id: Optional[int] = None
    username_or_email: Optional[str] = None
    organization: Optional[str] = "ProCom"

class RegisterRequest(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    department: Optional[str] = "Engineering"
    organization: Optional[str] = "ProCom"
    avatar: Optional[str] = ""

# Channel Schemas
class ChannelBase(BaseModel):
    name: str
    topic: Optional[str] = ""
    channel_type: Optional[str] = "text"
    position: Optional[int] = 0

class ChannelCreate(ChannelBase):
    conversation_id: int

class ChannelResponse(ChannelBase):
    id: int
    conversation_id: int

    class Config:
        from_attributes = True

# Conversation Schemas
class ConversationBase(BaseModel):
    title: str
    type: str  # direct, group, community, broadcast
    description: Optional[str] = ""
    avatar: Optional[str] = ""
    icon: Optional[str] = "chat"

class ConversationCreate(ConversationBase):
    member_ids: Optional[List[int]] = []
    initial_channels: Optional[List[str]] = []

class ConversationResponse(ConversationBase):
    id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    member_count: Optional[int] = 0
    channels: Optional[List[ChannelResponse]] = []
    unread_count: Optional[int] = 0
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None

    class Config:
        from_attributes = True

# Message Schemas
class MessageCreate(BaseModel):
    conversation_id: int
    channel_id: Optional[int] = None
    content: str
    sender_id: int
    message_type: Optional[str] = "text"
    file_url: Optional[str] = ""
    file_name: Optional[str] = ""
    file_type: Optional[str] = ""
    file_size: Optional[int] = 0
    auto_schedule_reminder: Optional[bool] = False

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    channel_id: Optional[int] = None
    sender_id: int
    sender_name: Optional[str] = ""
    sender_avatar: Optional[str] = ""
    content: str
    message_type: str
    file_url: Optional[str] = ""
    file_name: Optional[str] = ""
    file_type: Optional[str] = ""
    file_size: Optional[int] = 0
    reactions_json: Optional[str] = "{}"
    has_action_item: bool
    action_item_json: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True

class EmojiReactionRequest(BaseModel):
    user_id: int
    emoji: str

# Reminder Schemas
class ReminderBase(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: datetime
    priority: Optional[str] = "medium"
    reminder_type: Optional[str] = "task"

class ReminderCreate(ReminderBase):
    user_id: int
    conversation_id: Optional[int] = None
    source_message_id: Optional[int] = None
    auto_extracted: Optional[bool] = False

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None  # pending, completed, dismissed
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    conversation_id: Optional[int] = None
    source_message_id: Optional[int] = None
    status: str
    auto_extracted: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Meeting Schemas
class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    meeting_type: Optional[str] = "video"

class MeetingCreate(MeetingBase):
    conversation_id: Optional[int] = None
    host_id: int

class MeetingRSVP(BaseModel):
    user_id: int
    status: str  # going, maybe, declined

class MeetingResponse(MeetingBase):
    id: int
    conversation_id: Optional[int] = None
    host_id: int
    host_name: Optional[str] = ""
    meeting_code: str
    status: str
    rsvps_json: Optional[str] = "{}"
    created_at: datetime

    class Config:
        from_attributes = True

# AI Text Analysis Schemas
class TextAnalysisRequest(BaseModel):
    text: str
    reference_time: Optional[datetime] = None
    auto_schedule: Optional[bool] = False
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None

class ActionItemExtracted(BaseModel):
    detected: bool
    title: str
    description: str
    due_datetime: Optional[str] = None
    priority: str
    confidence: float
    action_type: str
    suggested_action: str

class TextAnalysisResponse(BaseModel):
    has_action: bool
    action_item: Optional[ActionItemExtracted] = None
    auto_scheduled: bool = False
    reminder_id: Optional[int] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = "neutral"

# Call Log Schemas
class CallInitiateRequest(BaseModel):
    caller_id: int
    receiver_id: Optional[int] = None
    conversation_id: Optional[int] = None
    call_type: str = "video"  # audio, video

class CallLogResponse(BaseModel):
    id: int
    caller_id: int
    receiver_id: Optional[int] = None
    conversation_id: Optional[int] = None
    call_type: str
    status: str
    duration_seconds: int
    notes: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True
