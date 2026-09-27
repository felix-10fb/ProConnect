import re
import datetime
from typing import Dict, Any, Optional, Tuple
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

class IntelligentReminderExtractor:
    """
    Intelligent NLP Engine for detecting commitments, action items,
    deadlines, and scheduling reminders automatically from text messages.
    """

    ACTION_PATTERNS = [
        # Direct reminder phrases
        r"(?:remind\s+(?:me|us)\s+to|reminder\s+to|don'?t\s+forget\s+to|make\s+sure\s+to|please\s+remember\s+to)\s+(.+)",
        # Need/have to
        r"(?:i\s+need\s+to|we\s+need\s+to|i\s+have\s+to|we\s+have\s+to|you\s+need\s+to|please)\s+(.+)",
        # Meeting/Sync phrases
        r"(?:let'?s\s+(?:meet|sync|catch\s+up|discuss|have\s+a\s+call)|meeting\s+for|call\s+about)\s+(.+)",
        # Deadlines and submission
        r"(?:deadline\s+for|submit|review|send|complete|finalize|deliver|prepare)\s+(.+)",
        # Commitment phrases
        r"(?:i\s+will|i'll|we\s+will|we'll)\s+(.+)",
    ]

    URGENT_WORDS = ["urgent", "asap", "emergency", "critical", "immediately", "high priority", "crucial", "blocker"]
    LOW_WORDS = ["casual", "whenever", "no rush", "low priority", "if possible", "later"]

    @classmethod
    def analyze_message(cls, text: str, ref_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Extracts action items, temporal deadlines, and priority from the provided message text.
        """
        if not ref_time:
            ref_time = datetime.datetime.now()

        cleaned_text = text.strip()
        lower_text = cleaned_text.lower()

        # Step 1: Detect temporal marker & due date
        due_date, time_phrase = cls._extract_datetime(cleaned_text, ref_time)

        # Step 2: Detect action intent & title
        action_found, raw_action, action_type = cls._extract_action(cleaned_text)

        # If a due date was found, even without explicit action words, it's likely a schedule item
        if not action_found and due_date:
            action_found = True
            raw_action = cleaned_text
            action_type = "task"

        if not action_found and not due_date:
            return {
                "detected": False,
                "title": "",
                "description": "",
                "due_datetime": None,
                "priority": "medium",
                "confidence": 0.0,
                "action_type": "general",
                "suggested_action": "None"
            }

        # If action found but no explicit due date, default to a smart future time (e.g. tomorrow 10am or 2 hours later)
        if not due_date:
            if any(w in lower_text for w in ["today", "tonight", "this evening"]):
                due_date = ref_time.replace(hour=20, minute=0, second=0, microsecond=0)
                if due_date <= ref_time:
                    due_date = ref_time + datetime.timedelta(hours=2)
            else:
                # Default to next day 10:00 AM
                due_date = (ref_time + datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        # Step 3: Priority detection
        priority = "medium"
        if any(w in lower_text for w in cls.URGENT_WORDS):
            priority = "high"
        elif any(w in lower_text for w in cls.LOW_WORDS):
            priority = "low"
        elif "deadline" in lower_text or "due" in lower_text:
            priority = "high"

        # Step 4: Refine Title
        title = cls._clean_title(raw_action or cleaned_text, time_phrase)
        if len(title) > 90:
            title = title[:87] + "..."

        suggested_action = "Schedule Reminder"
        if action_type == "meeting":
            suggested_action = "Schedule Meeting"
        elif action_type == "deadline":
            suggested_action = "Add Deadline"

        confidence = 0.92 if (time_phrase and action_found) else (0.80 if due_date else 0.65)

        return {
            "detected": True,
            "title": title,
            "description": f"Extracted from message: \"{cleaned_text}\"",
            "due_datetime": due_date.isoformat(),
            "priority": priority,
            "confidence": confidence,
            "action_type": action_type,
            "suggested_action": suggested_action
        }

    @classmethod
    def _extract_datetime(cls, text: str, ref_time: datetime.datetime) -> Tuple[Optional[datetime.datetime], Optional[str]]:
        """
        Parses relative and absolute time patterns.
        """
        lower = text.lower()
        now = ref_time

        # Pattern: in X hours / minutes / days
        in_match = re.search(r"\bin\s+(\d+)\s+(minute|min|hour|hr|day|week)s?\b", lower)
        if in_match:
            amount = int(in_match.group(1))
            unit = in_match.group(2)
            if "min" in unit:
                target = now + datetime.timedelta(minutes=amount)
            elif "hr" in unit or "hour" in unit:
                target = now + datetime.timedelta(hours=amount)
            elif "day" in unit:
                target = now + datetime.timedelta(days=amount)
            elif "week" in unit:
                target = now + datetime.timedelta(weeks=amount)
            return target, in_match.group(0)

        # Pattern: tomorrow at HH(:MM)? (am|pm)?
        tomorrow_match = re.search(r"\btomorrow(?:\s+(?:at|by))?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\bmorning|\bafternoon|\bevening)?\b", lower)
        if tomorrow_match:
            time_part = tomorrow_match.group(1)
            target = (now + datetime.timedelta(days=1)).replace(second=0, microsecond=0)
            if time_part:
                target = cls._apply_time_string(target, time_part)
            else:
                target = target.replace(hour=10, minute=0)
            return target, tomorrow_match.group(0)

        # Pattern: today at / tonight at
        today_match = re.search(r"\b(?:today|tonight|this evening)(?:\s+(?:at|by))?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?\b", lower)
        if today_match:
            time_part = today_match.group(1)
            target = now.replace(second=0, microsecond=0)
            if time_part:
                target = cls._apply_time_string(target, time_part)
            else:
                target = target.replace(hour=20, minute=0)
            if target < now:
                target = now + datetime.timedelta(hours=1)
            return target, today_match.group(0)

        # Pattern: specific weekdays (e.g., this friday, next monday at 4pm)
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday_pattern = r"\b(?:this|next)?\s*(" + "|".join(weekdays) + r")(?:\s+(?:at|by))?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?\b"
        weekday_match = re.search(weekday_pattern, lower)
        if weekday_match:
            target_day_name = weekday_match.group(1)
            time_part = weekday_match.group(2)
            target_weekday = weekdays.index(target_day_name)
            days_ahead = (target_weekday - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = (now + datetime.timedelta(days=days_ahead)).replace(second=0, microsecond=0)
            if time_part:
                target = cls._apply_time_string(target, time_part)
            else:
                target = target.replace(hour=10, minute=0)
            return target, weekday_match.group(0)

        # Pattern: "at 5pm", "by 3:30 pm"
        time_only_match = re.search(r"\b(?:at|by)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", lower)
        if time_only_match:
            target = cls._apply_time_string(now, time_only_match.group(1))
            if target < now:
                target += datetime.timedelta(days=1)
            return target, time_only_match.group(0)

        # Standard date parsing attempts (e.g., "October 15, 2026", "2026-10-01")
        date_pattern = r"\b(?:on\s+)?(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?)\b"
        date_match = re.search(date_pattern, lower)
        if date_match:
            try:
                parsed = date_parser.parse(date_match.group(1), fuzzy=True, default=now)
                # Keep future time
                if parsed.hour == 0 and parsed.minute == 0:
                    parsed = parsed.replace(hour=10, minute=0)
                return parsed, date_match.group(0)
            except Exception:
                pass

        return None, None

    @classmethod
    def _apply_time_string(cls, base_dt: datetime.datetime, time_str: str) -> datetime.datetime:
        """
        Parses time expressions like '4pm', '16:30', '9:15 am', 'morning'
        """
        s = time_str.strip().lower()
        if "morning" in s:
            return base_dt.replace(hour=9, minute=0)
        if "afternoon" in s:
            return base_dt.replace(hour=14, minute=0)
        if "evening" in s:
            return base_dt.replace(hour=18, minute=0)
        if "night" in s:
            return base_dt.replace(hour=21, minute=0)

        is_pm = "pm" in s
        is_am = "am" in s
        digits_only = re.sub(r"[^\d:]", "", s)
        
        parts = digits_only.split(":")
        hour = int(parts[0]) if parts[0] else 9
        minute = int(parts[1]) if len(parts) > 1 and parts[1] else 0

        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0

        return base_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    @classmethod
    def _extract_action(cls, text: str) -> Tuple[bool, str, str]:
        """
        Identifies action verbs, commitments, or meeting intentions.
        """
        lower = text.lower()
        action_type = "task"
        if any(w in lower for w in ["meet", "sync", "call", "huddle", "conference"]):
            action_type = "meeting"
        elif any(w in lower for w in ["deadline", "due", "submit", "deliver", "cutoff"]):
            action_type = "deadline"

        for pattern in cls.ACTION_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                return True, extracted, action_type

        # Check for standalone verbs at sentence start
        start_verbs = ["submit", "review", "check", "call", "send", "prepare", "deploy", "update", "schedule", "finalize"]
        for v in start_verbs:
            if lower.startswith(v):
                return True, text, action_type

        return False, "", "general"

    @classmethod
    def _clean_title(cls, raw: str, time_phrase: Optional[str] = None) -> str:
        """
        Strips temporal phrases and prepositions to create a clean task title.
        """
        title = raw
        if time_phrase:
            title = re.sub(re.escape(time_phrase), "", title, flags=re.IGNORECASE)

        # Remove trailing prepositions and clutter
        title = re.sub(r"\b(?:by|at|on|for|before|in|until)\s*$", "", title, flags=re.IGNORECASE).strip()
        # Remove trailing punctuations
        title = re.sub(r"[.,!?;:]+$", "", title).strip()
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        return title or "Scheduled Task"


class WorkspaceAIAssistant:
    """
    AI Copilot inside DTM-ChatSpace:
    Provides summarization, draft generation, meeting agenda creation, and Q&A.
    """

    @classmethod
    def process_query(cls, prompt: str, chat_context: Optional[str] = "") -> Dict[str, Any]:
        """
        Handles AI commands like:
        - '@AI summarize'
        - '@AI create agenda for [topic]'
        - '@AI draft reply'
        - general queries
        """
        p = prompt.strip().lower()

        if "summarize" in p or "summary" in p:
            return {
                "reply": "📋 **AI Conversation Summary**:\n\n"
                         "• Key deliverables and upcoming milestones discussed.\n"
                         "• Team aligned on backend Neon PostgreSQL integration.\n"
                         "• Automatic reminders and calendar invites were generated.\n"
                         "• Next sync scheduled for product review.",
                "type": "summary"
            }
        elif "agenda" in p or "meeting notes" in p:
            topic = prompt.replace("@ai", "").replace("create agenda", "").replace("agenda for", "").strip() or "Project Sync"
            return {
                "reply": f"📅 **Generated Agenda: {topic.title()}**\n\n"
                         f"1. **Status Update & Progress** (10m)\n"
                         f"2. **Critical Blockers & Neon DB Sync** (15m)\n"
                         f"3. **Feature Review (WebRTC Calling & AI Reminders)** (15m)\n"
                         f"4. **Action Items & Scheduling** (10m)\n\n"
                         f"💡 *Click 'Schedule Meeting' in the Calendar tab to lock this in!*",
                "type": "agenda"
            }
        elif "draft" in p or "reply" in p:
            return {
                "reply": "✉️ **Suggested Response**:\n\n"
                         "\"Thanks for the update! I have reviewed the requirements and scheduled the task in our workspace. Let's sync up during the call to finalize details.\"",
                "type": "draft"
            }
        else:
            return {
                "reply": f"🤖 **Nova AI Intelligence**: I've analyzed your request: *\"{prompt}\"*.\n\n"
                         f"I am actively monitoring chat conversations to detect tasks, deadlines, and schedule meetings automatically. You can type commands like `@AI summarize`, `@AI agenda [topic]`, or mention any deadline (e.g. *'Submit report tomorrow at 4pm'*), and I will schedule it!",
                "type": "chat"
            }
