import datetime
from sqlalchemy.orm import Session
from backend.models import User, Conversation, ConversationMember, CommunityChannel, Message, Reminder, Meeting
import json

def seed_database(db: Session):
    # Check if database is already seeded
    if db.query(User).first():
        return

    print("[SEED] Seeding initial users, communities, groups, broadcasts, reminders, and meetings...")

    now = datetime.datetime.now()

    # 1. Users
    users_data = [
        User(
            id=1,
            username="alex_morgan",
            full_name="Alex Morgan",
            email="alex@dtmspace.io",
            avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            status="online",
            status_text="Lead Architect • ProCom",
            department="Architecture & Core",
            organization="ProCom",
            is_bot=False
        ),
        User(
            id=2,
            username="sarah_chen",
            full_name="Sarah Chen",
            email="sarah.chen@procom.io",
            avatar="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
            status="online",
            status_text="Senior Full-Stack Engineer",
            department="Frontend & Realtime",
            organization="ProCom",
            is_bot=False
        ),
        User(
            id=3,
            username="marcus_vance",
            full_name="Marcus Vance",
            email="marcus@procom.io",
            avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
            status="away",
            status_text="Product Manager",
            department="Product & Design",
            organization="ProCom",
            is_bot=False
        ),
        User(
            id=4,
            username="elena_rostova",
            full_name="Elena Rostova",
            email="elena@procom.io",
            avatar="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            status="busy",
            status_text="AI Research Scientist",
            department="AI Research & NLP",
            organization="ProCom",
            is_bot=False
        ),
        User(
            id=5,
            username="nova_ai",
            full_name="Nova AI Intelligence",
            email="nova@procom.io",
            avatar="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80",
            status="online",
            status_text="Automated Workspace Assistant & NLP Engine",
            department="Autonomous AI",
            organization="ProCom",
            is_bot=True
        )
    ]

    for u in users_data:
        db.add(u)
    db.commit()

    # 2. Conversations:
    # 2a. Direct chat: Alex & Sarah
    dm_sarah = Conversation(
        id=1,
        title="Sarah Chen",
        type="direct",
        description="Direct messaging with Sarah Chen",
        avatar="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
        icon="user",
        created_by_id=1
    )
    db.add(dm_sarah)

    # 2b. Group: Core Engineering Team
    grp_eng = Conversation(
        id=2,
        title="Core Engineering Team",
        type="group",
        description="Daily standups, architectural discussions, and release planning",
        avatar="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=150&auto=format&fit=crop&q=80",
        icon="users",
        created_by_id=1
    )
    db.add(grp_eng)

    # 2c. Community: DTM Global Tech Space
    comm_dtm = Conversation(
        id=3,
        title="DTM Global Ecosystem",
        type="community",
        description="Decentralized Tech Ecosystem: Engineering, AI Research, and Community Events",
        avatar="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=150&auto=format&fit=crop&q=80",
        icon="globe",
        created_by_id=1
    )
    db.add(comm_dtm)

    # 2d. Broadcast: Official Releases & Alerts
    bcast_official = Conversation(
        id=4,
        title="DTM Space Broadcasts",
        type="broadcast",
        description="Official platform announcements, scheduled maintenance, and feature drops",
        avatar="https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=150&auto=format&fit=crop&q=80",
        icon="radio",
        created_by_id=1
    )
    db.add(bcast_official)

    db.commit()

    # 3. Community Channels for DTM Global Ecosystem
    channels_data = [
        CommunityChannel(id=1, conversation_id=3, name="announcements", topic="Official ecosystem news and milestones", channel_type="announcements", position=1),
        CommunityChannel(id=2, conversation_id=3, name="general-chat", topic="Lobby discussion and team watercooler", channel_type="text", position=2),
        CommunityChannel(id=3, conversation_id=3, name="neon-postgresql", topic="Database migrations, pooling and queries", channel_type="text", position=3),
        CommunityChannel(id=4, conversation_id=3, name="ai-agents-collab", topic="NLP reminders and autonomous assistant dev", channel_type="text", position=4),
        CommunityChannel(id=5, conversation_id=3, name="stage-audio-video", topic="Live community voice and video stage", channel_type="voice", position=5),
    ]
    for ch in channels_data:
        db.add(ch)
    db.commit()

    # 4. Conversation Members
    memberships = [
        # DM Sarah
        ConversationMember(conversation_id=1, user_id=1, role="owner"),
        ConversationMember(conversation_id=1, user_id=2, role="member"),

        # Group Core Engineering
        ConversationMember(conversation_id=2, user_id=1, role="owner"),
        ConversationMember(conversation_id=2, user_id=2, role="admin"),
        ConversationMember(conversation_id=2, user_id=3, role="member"),
        ConversationMember(conversation_id=2, user_id=4, role="member"),
        ConversationMember(conversation_id=2, user_id=5, role="member"),

        # Community
        ConversationMember(conversation_id=3, user_id=1, role="owner"),
        ConversationMember(conversation_id=3, user_id=2, role="admin"),
        ConversationMember(conversation_id=3, user_id=3, role="member"),
        ConversationMember(conversation_id=3, user_id=4, role="member"),
        ConversationMember(conversation_id=3, user_id=5, role="member"),

        # Broadcast
        ConversationMember(conversation_id=4, user_id=1, role="owner"),
        ConversationMember(conversation_id=4, user_id=2, role="member"),
        ConversationMember(conversation_id=4, user_id=3, role="member"),
        ConversationMember(conversation_id=4, user_id=4, role="member"),
    ]
    for m in memberships:
        db.add(m)
    db.commit()

    # 5. Seed Messages demonstrating AI text detection
    action_item_1 = {
        "detected": True,
        "title": "Submit Neon PostgreSQL migration schema",
        "description": "Extracted from message: \"Don't forget to submit the Neon PostgreSQL schema migration tomorrow at 5pm\"",
        "due_datetime": (now + datetime.timedelta(days=1)).replace(hour=17, minute=0, second=0).isoformat(),
        "priority": "high",
        "confidence": 0.95,
        "action_type": "deadline",
        "suggested_action": "Schedule Reminder"
    }

    action_item_2 = {
        "detected": True,
        "title": "Sync with DevOps team",
        "description": "Extracted from message: \"Let's meet with DevOps team this Friday at 3:00 PM to test WebRTC signaling\"",
        "due_datetime": (now + datetime.timedelta(days=2)).replace(hour=15, minute=0, second=0).isoformat(),
        "priority": "medium",
        "confidence": 0.92,
        "action_type": "meeting",
        "suggested_action": "Schedule Meeting"
    }

    messages_data = [
        # DM with Sarah
        Message(
            id=1,
            conversation_id=1,
            sender_id=2,
            content="Hey Alex! The WebRTC video streaming latency is looking super crisp under 60ms.",
            created_at=now - datetime.timedelta(minutes=45)
        ),
        Message(
            id=2,
            conversation_id=1,
            sender_id=1,
            content="Awesome! Let's ensure the audio ringtones and screen sharing tests pass smoothly.",
            created_at=now - datetime.timedelta(minutes=30)
        ),
        Message(
            id=3,
            conversation_id=1,
            sender_id=2,
            content="Don't forget to submit the Neon PostgreSQL schema migration tomorrow at 5pm so we can merge.",
            has_action_item=True,
            action_item_json=json.dumps(action_item_1),
            created_at=now - datetime.timedelta(minutes=15)
        ),

        # Group Core Engineering
        Message(
            id=4,
            conversation_id=2,
            sender_id=3,
            content="Good morning everyone! Reminder: Sprint 14 review is coming up.",
            created_at=now - datetime.timedelta(hours=2)
        ),
        Message(
            id=5,
            conversation_id=2,
            sender_id=4,
            content="Let's meet with DevOps team this Friday at 3:00 PM to test WebRTC signaling server under load.",
            has_action_item=True,
            action_item_json=json.dumps(action_item_2),
            created_at=now - datetime.timedelta(hours=1)
        ),
        Message(
            id=6,
            conversation_id=2,
            sender_id=5,
            content="🤖 **Nova AI**: I noticed a proposed meeting for this Friday at 3:00 PM. A calendar event suggestion has been prepared for the team!",
            message_type="system",
            created_at=now - datetime.timedelta(minutes=58)
        ),

        # Community General Chat
        Message(
            id=7,
            conversation_id=3,
            channel_id=2,
            sender_id=1,
            content="Welcome everyone to DTM Global Ecosystem! Feel free to explore our dedicated channels.",
            created_at=now - datetime.timedelta(days=1)
        ),

        # Broadcast Channel
        Message(
            id=8,
            conversation_id=4,
            sender_id=1,
            content="📢 **System Release v2.4 Live**:\n• Integrated Neon Cloud PostgreSQL\n• Intelligent AI Auto-Scheduler for text commitments\n• HD Video/Audio WebRTC peer calling with screen share\n• Unified Channels, Communities and Broadcast Hub",
            message_type="broadcast",
            created_at=now - datetime.timedelta(hours=5)
        )
    ]
    for msg in messages_data:
        db.add(msg)
    db.commit()

    # 6. Seed Reminders (already auto-extracted and active)
    reminders_data = [
        Reminder(
            id=1,
            user_id=1,
            conversation_id=1,
            source_message_id=3,
            title="Submit Neon PostgreSQL schema migration",
            description="Auto-extracted from Sarah Chen's message in Direct Chat",
            due_date=(now + datetime.timedelta(days=1)).replace(hour=17, minute=0, second=0),
            priority="high",
            status="pending",
            auto_extracted=True,
            reminder_type="deadline"
        ),
        Reminder(
            id=2,
            user_id=1,
            conversation_id=2,
            source_message_id=5,
            title="DevOps WebRTC Signaling Stress Test",
            description="Auto-extracted from Elena Rostova's message in Core Engineering",
            due_date=(now + datetime.timedelta(days=2)).replace(hour=15, minute=0, second=0),
            priority="medium",
            status="pending",
            auto_extracted=True,
            reminder_type="meeting"
        ),
        Reminder(
            id=3,
            user_id=1,
            title="Prepare Product Keynote Slides",
            description="Complete the deck for investors and developer community",
            due_date=(now + datetime.timedelta(days=3)).replace(hour=11, minute=0, second=0),
            priority="low",
            status="pending",
            auto_extracted=False,
            reminder_type="task"
        )
    ]
    for r in reminders_data:
        db.add(r)
    db.commit()

    # 7. Seed Meetings
    meetings_data = [
        Meeting(
            id=1,
            conversation_id=2,
            host_id=1,
            title="Sprint 14 Architecture & Neon DB Sync",
            description="Review PostgreSQL query plans, pooling configurations, and real-time WebRTC scaling.",
            start_time=(now + datetime.timedelta(days=1)).replace(hour=14, minute=0, second=0),
            end_time=(now + datetime.timedelta(days=1)).replace(hour=15, minute=0, second=0),
            meeting_code="dtm-sync-arch",
            meeting_type="video",
            status="scheduled",
            rsvps_json=json.dumps({"1": "going", "2": "going", "3": "maybe", "4": "going"})
        ),
        Meeting(
            id=2,
            conversation_id=3,
            host_id=1,
            title="AI Communication Hub Global Demo",
            description="Live interactive demo of AI text reading, auto-reminders, and calling interface.",
            start_time=(now + datetime.timedelta(days=2)).replace(hour=16, minute=30, second=0),
            end_time=(now + datetime.timedelta(days=2)).replace(hour=17, minute=30, second=0),
            meeting_code="dtm-ai-demo",
            meeting_type="video",
            status="scheduled",
            rsvps_json=json.dumps({"1": "going", "2": "going", "4": "going"})
        )
    ]
    for mt in meetings_data:
        db.add(mt)
    db.commit()

    print("[SEED] Database successfully populated with initial data.")

    # In PostgreSQL, sync sequence counters with max id
    if "postgres" in str(db.bind.url):
        from sqlalchemy import text
        tables = ['users', 'conversations', 'conversation_members', 'community_channels', 'messages', 'reminders', 'meetings', 'call_logs']
        for tbl in tables:
            try:
                db.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1));"))
            except Exception as e:
                pass
        db.commit()
        print("[SEED] PostgreSQL sequences successfully synchronized.")
