/**
 * Calendar & Meetings Manager for DTM-ChatSpace
 */
class CalendarManager {
  constructor() {
    this.currentDate = new Date();
    this.selectedDate = new Date();
    this.meetings = [];
  }

  async init() {
    await this.loadMeetings();
    this.renderCalendar();
    this.renderUpcomingMeetings();
    this.bindEvents();
  }

  async loadMeetings() {
    try {
      this.meetings = await window.API.getMeetings();
    } catch (err) {
      console.error('Failed to load meetings:', err);
      this.meetings = [];
    }
  }

  bindEvents() {
    const prevBtn = document.getElementById('btn-cal-prev');
    const nextBtn = document.getElementById('btn-cal-next');
    const todayBtn = document.getElementById('btn-cal-today');
    const newMeetingBtn = document.getElementById('btn-new-meeting');

    if (prevBtn) {
      prevBtn.onclick = () => {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.renderCalendar();
      };
    }
    if (nextBtn) {
      nextBtn.onclick = () => {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.renderCalendar();
      };
    }
    if (todayBtn) {
      todayBtn.onclick = () => {
        this.currentDate = new Date();
        this.selectedDate = new Date();
        this.renderCalendar();
        this.renderUpcomingMeetings();
      };
    }
    if (newMeetingBtn) {
      newMeetingBtn.onclick = () => this.openNewMeetingModal();
    }
  }

  renderCalendar() {
    const titleEl = document.getElementById('cal-month-title');
    const gridEl = document.getElementById('cal-days-grid');
    if (!gridEl) return;

    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth();

    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];

    if (titleEl) titleEl.textContent = `${monthNames[month]} ${year}`;

    gridEl.innerHTML = '';

    const firstDayIndex = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevDaysInMonth = new Date(year, month, 0).getDate();

    const today = new Date();

    // Previous month padding days
    for (let i = firstDayIndex; i > 0; i--) {
      const cell = document.createElement('div');
      cell.className = 'calendar-day-cell pad-day';
      cell.style.opacity = '0.3';
      cell.textContent = prevDaysInMonth - i + 1;
      gridEl.appendChild(cell);
    }

    // Days of current month
    for (let day = 1; day <= daysInMonth; day++) {
      const cell = document.createElement('div');
      cell.className = 'calendar-day-cell';
      cell.textContent = day;

      const thisDate = new Date(year, month, day);

      if (
        thisDate.getFullYear() === today.getFullYear() &&
        thisDate.getMonth() === today.getMonth() &&
        thisDate.getDate() === today.getDate()
      ) {
        cell.classList.add('today');
      }

      if (
        thisDate.getFullYear() === this.selectedDate.getFullYear() &&
        thisDate.getMonth() === this.selectedDate.getMonth() &&
        thisDate.getDate() === this.selectedDate.getDate()
      ) {
        cell.classList.add('active');
      }

      // Check if this date has scheduled meetings
      const hasEvents = this.meetings.some(m => {
        const mDate = new Date(m.start_time);
        return mDate.getFullYear() === year && mDate.getMonth() === month && mDate.getDate() === day;
      });

      if (hasEvents) {
        cell.classList.add('has-events');
      }

      cell.onclick = () => {
        this.selectedDate = new Date(year, month, day);
        this.renderCalendar();
        this.renderUpcomingMeetings();
      };

      gridEl.appendChild(cell);
    }
  }

  renderUpcomingMeetings() {
    const listEl = document.getElementById('meetings-list-container');
    if (!listEl) return;

    if (!this.meetings.length) {
      listEl.innerHTML = `<div style="text-align:center; padding:30px 10px; color:#64748b; font-size:0.85rem;">No meetings scheduled yet. Click '+ Schedule Meeting' to create one!</div>`;
      return;
    }

    listEl.innerHTML = '';
    const currentUserId = window.appState.currentUser ? String(window.appState.currentUser.id) : '1';

    this.meetings.forEach(mtg => {
      const card = document.createElement('div');
      card.className = 'meeting-card';

      const start = new Date(mtg.start_time);
      const end = new Date(mtg.end_time);

      const timeStr = `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} • ${start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

      const rsvps = mtg.rsvps || {};
      const userRsvp = rsvps[currentUserId] || 'none';

      let goingCount = 0;
      Object.values(rsvps).forEach(v => { if (v === 'going') goingCount++; });

      card.innerHTML = `
        <div class="meeting-card-title">${mtg.title}</div>
        <div class="meeting-time-row">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          <span>${timeStr}</span>
        </div>
        <p style="font-size:0.8rem; color:#94a3b8;">${mtg.description || 'Virtual team conference'}</p>
        <div style="font-size:0.75rem; color:#6ee7b7; font-weight:600;">👥 ${goingCount} Going • Host: ${mtg.host_name}</div>
        <div class="meeting-actions-row">
          <div class="rsvp-group">
            <button class="btn-rsvp ${userRsvp === 'going' ? 'active' : ''}" data-status="going">Going</button>
            <button class="btn-rsvp ${userRsvp === 'maybe' ? 'active' : ''}" data-status="maybe">Maybe</button>
          </div>
          <button class="btn-join-meeting" data-code="${mtg.meeting_code}" data-title="${mtg.title}">
            🎥 Join Room
          </button>
        </div>
      `;

      // RSVP event
      card.querySelectorAll('.btn-rsvp').forEach(btn => {
        btn.onclick = async () => {
          const status = btn.getAttribute('data-status');
          await window.API.rsvpMeeting(mtg.id, parseInt(currentUserId), status);
          await this.loadMeetings();
          this.renderUpcomingMeetings();
        };
      });

      // Join call event
      const joinBtn = card.querySelector('.btn-join-meeting');
      if (joinBtn) {
        joinBtn.onclick = () => {
          window.callingEngine.startCall(
            mtg.host_id,
            mtg.conversation_id || 1,
            mtg.title,
            '',
            mtg.meeting_type || 'video'
          );
        };
      }

      listEl.appendChild(card);
    });
  }

  openNewMeetingModal() {
    const modal = document.getElementById('new-meeting-modal');
    if (modal) modal.classList.add('active');
  }

  async handleCreateMeeting(formData) {
    try {
      await window.API.createMeeting(formData);
      await this.loadMeetings();
      this.renderCalendar();
      this.renderUpcomingMeetings();
      // Reload reminders since meeting creates an auto-reminder
      if (window.remindersManager) {
        window.remindersManager.loadReminders();
      }
      return true;
    } catch (err) {
      alert('Error creating meeting: ' + err.message);
      return false;
    }
  }
}

window.calendarManager = new CalendarManager();
