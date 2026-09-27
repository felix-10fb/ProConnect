/**
 * AI Reminders & Auto-Scheduler Manager
 */
class RemindersManager {
  constructor() {
    this.reminders = [];
    this.countdownInterval = null;
  }

  async init() {
    await this.loadReminders();
    this.renderReminders();
    this.bindEvents();
    this.startCountdownLoop();

    // Realtime listeners
    window.realtime.on('reminder_created', () => {
      this.loadReminders().then(() => this.renderReminders());
      window.soundEngine.playNotification();
    });

    window.realtime.on('new_message', (data) => {
      if (data.message && data.message.auto_scheduled_reminder) {
        this.loadReminders().then(() => this.renderReminders());
        window.soundEngine.playNotification();
      }
    });
  }

  async loadReminders() {
    try {
      const uid = window.appState.currentUser ? window.appState.currentUser.id : 1;
      this.reminders = await window.API.getReminders(uid);
      this.updateBadgeCount();
    } catch (err) {
      console.error('Failed to load reminders:', err);
      this.reminders = [];
    }
  }

  updateBadgeCount() {
    const badge = document.getElementById('rail-reminders-badge');
    const pendingCount = this.reminders.filter(r => r.status === 'pending').length;
    if (badge) {
      if (pendingCount > 0) {
        badge.style.display = 'flex';
        badge.textContent = pendingCount;
      } else {
        badge.style.display = 'none';
      }
    }
  }

  bindEvents() {
    // Interactive AI Scanner Playground
    const scanBtn = document.getElementById('btn-scanner-analyze');
    const scanInput = document.getElementById('scanner-input-text');
    const autoScheduleCheckbox = document.getElementById('scanner-auto-schedule');

    if (scanBtn && scanInput) {
      scanBtn.onclick = async () => {
        const text = scanInput.value.trim();
        if (!text) return;
        const auto = autoScheduleCheckbox ? autoScheduleCheckbox.checked : true;
        await this.runPlaygroundAnalysis(text, auto);
      };
    }

    // Filter pills
    const filterPills = document.querySelectorAll('.reminder-filter-btn');
    filterPills.forEach(pill => {
      pill.onclick = () => {
        filterPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.renderReminders(pill.getAttribute('data-filter'));
      };
    });
  }

  async runPlaygroundAnalysis(text, autoSchedule) {
    const resBox = document.getElementById('scanner-result-box');
    if (!resBox) return;

    resBox.innerHTML = `<div style="color:#a5b4fc; font-style:italic;">🤖 Nova AI is analyzing temporal markers and intent...</div>`;

    try {
      const currentUserId = window.appState.currentUser ? window.appState.currentUser.id : 1;
      const res = await window.API.analyzeText(text, autoSchedule, currentUserId);

      if (res.has_action && res.action_item) {
        const item = res.action_item;
        const dueFormatted = item.due_datetime ? new Date(item.due_datetime).toLocaleString() : 'Upcoming';
        const priorityClass = `priority-${item.priority}`;

        resBox.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#fff;">🎯 Detected: ${item.title}</strong>
            <span class="priority-badge ${priorityClass}">${item.priority}</span>
          </div>
          <div style="color:#67e8f9; font-size:0.78rem;">⏰ Due: ${dueFormatted} • Confidence: ${Math.round(item.confidence * 100)}%</div>
          <div style="color:#94a3b8; font-size:0.75rem;">Action Type: <strong>${item.action_type.toUpperCase()}</strong></div>
          <div style="margin-top:6px; color:#6ee7b7; font-weight:700;">
            ${res.auto_scheduled ? '✅ Automatically scheduled into your Reminders & Calendar!' : '💡 Ready to schedule.'}
          </div>
        `;

        if (res.auto_scheduled) {
          window.soundEngine.playNotification();
          await this.loadReminders();
          this.renderReminders();
        }
      } else {
        resBox.innerHTML = `<div style="color:#94a3b8;">No actionable commitments or deadlines detected in this text. Try: <em>"Send progress report tomorrow at 5pm"</em></div>`;
      }
    } catch (err) {
      resBox.innerHTML = `<div style="color:#fda4af;">Analysis error: ${err.message}</div>`;
    }
  }

  renderReminders(filter = 'all') {
    const stream = document.getElementById('reminders-stream-container');
    if (!stream) return;

    let filtered = this.reminders;
    if (filter === 'pending') filtered = this.reminders.filter(r => r.status === 'pending');
    else if (filter === 'completed') filtered = this.reminders.filter(r => r.status === 'completed');
    else if (filter === 'high') filtered = this.reminders.filter(r => r.priority === 'high' && r.status === 'pending');

    if (!filtered.length) {
      stream.innerHTML = `
        <div style="text-align:center; padding:40px 20px; color:#64748b; font-size:0.9rem;">
          No reminders found in this view.<br>
          <span style="font-size:0.8rem; color:#94a3b8;">Send messages containing deadlines or use the AI text scanner to generate them automatically!</span>
        </div>
      `;
      return;
    }

    stream.innerHTML = '';
    const now = new Date();

    filtered.forEach(r => {
      const card = document.createElement('div');
      card.className = `reminder-card ${r.status === 'completed' ? 'completed' : ''}`;

      const dueDate = new Date(r.due_date);
      const isOverdue = dueDate < now && r.status === 'pending';
      const timeRemaining = this.formatTimeRemaining(dueDate, now);

      card.innerHTML = `
        <div class="reminder-left">
          <button class="reminder-check-btn" title="${r.status === 'completed' ? 'Mark Pending' : 'Mark Completed'}">
            ${r.status === 'completed' ? '✓' : ''}
          </button>
          <div class="reminder-info">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="reminder-title">${r.title}</span>
              ${r.auto_extracted ? '<span class="reminder-auto-tag">⚡ AI Auto</span>' : ''}
              <span class="priority-badge priority-${r.priority}">${r.priority}</span>
            </div>
            <div class="reminder-due-badge">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              <span style="${isOverdue ? 'color:#fda4af; font-weight:700;' : ''}">${dueDate.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} • ${timeRemaining}</span>
            </div>
            ${r.description ? `<p style="font-size:0.75rem; color:#64748b;">${r.description}</p>` : ''}
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <button class="icon-btn-round btn-del-reminder" title="Delete Reminder">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      `;

      // Toggle status
      const checkBtn = card.querySelector('.reminder-check-btn');
      checkBtn.onclick = async () => {
        const newStatus = r.status === 'completed' ? 'pending' : 'completed';
        await window.API.updateReminder(r.id, { status: newStatus });
        await this.loadReminders();
        this.renderReminders(filter);
      };

      // Delete
      const delBtn = card.querySelector('.btn-del-reminder');
      delBtn.onclick = async (e) => {
        e.stopPropagation();
        await window.API.deleteReminder(r.id);
        await this.loadReminders();
        this.renderReminders(filter);
      };

      stream.appendChild(card);
    });
  }

  formatTimeRemaining(dueDate, now) {
    const diffMs = dueDate - now;
    if (diffMs < 0) {
      const pastMins = Math.floor(-diffMs / 60000);
      if (pastMins < 60) return `Overdue by ${pastMins}m`;
      const pastHours = Math.floor(pastMins / 60);
      return `Overdue by ${pastHours}h`;
    }
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `Due in ${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `Due in ${hours}h ${mins % 60}m`;
    const days = Math.floor(hours / 24);
    return `Due in ${days}d ${hours % 24}h`;
  }

  startCountdownLoop() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    this.countdownInterval = setInterval(() => {
      // Re-render reminders to update dynamic countdown text if tab is visible
      const remindersView = document.getElementById('reminders-view');
      if (remindersView && remindersView.classList.contains('active')) {
        this.renderReminders();
      }
    }, 60000);
  }
}

window.remindersManager = new RemindersManager();
