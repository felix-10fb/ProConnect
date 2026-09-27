/**
 * API Service for ProCom Platform Communication
 */
const API = {
  baseUrl: window.location.origin,

  async request(endpoint, options = {}) {
    try {
      const isFormData = options.body instanceof FormData;
      const headers = isFormData ? (options.headers || {}) : {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      };

      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        headers,
        ...options
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth & Organization Directory
  login(userIdOrQuery) {
    const isNum = !isNaN(userIdOrQuery) && userIdOrQuery !== '';
    const body = isNum ? { user_id: parseInt(userIdOrQuery) } : { username_or_email: userIdOrQuery };
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },
  register(data) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  searchOrganization(query) {
    return this.request(`/api/search?q=${encodeURIComponent(query)}`);
  },

  // File & Photo Upload
  uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/api/upload', {
      method: 'POST',
      body: formData
    });
  },
  uploadAvatar(userId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/api/users/${userId}/avatar`, {
      method: 'POST',
      body: formData
    });
  },

  // Reactions
  toggleReaction(messageId, userId, emoji) {
    return this.request(`/api/messages/${messageId}/reactions`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, emoji })
    });
  },

  // Database Status
  getDatabaseStatus() {
    return this.request('/api/database/status');
  },
  configureDatabase(databaseUrl) {
    return this.request('/api/database/configure', {
      method: 'POST',
      body: JSON.stringify({ database_url: databaseUrl })
    });
  },

  // Users
  getUsers() {
    return this.request('/api/users');
  },
  getUser(userId) {
    return this.request(`/api/users/${userId}`);
  },

  // Conversations & Channels
  getConversations() {
    return this.request('/api/conversations');
  },
  createConversation(data) {
    return this.request('/api/conversations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  addChannel(convId, data) {
    return this.request(`/api/conversations/${convId}/channels`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // Messages
  getMessages(convId, channelId = null) {
    let url = `/api/conversations/${convId}/messages`;
    if (channelId) url += `?channel_id=${channelId}`;
    return this.request(url);
  },
  sendMessage(data) {
    return this.request('/api/messages', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // AI NLP Analysis
  analyzeText(text, autoSchedule = false, userId = 1, convId = null) {
    return this.request('/api/ai/analyze-text', {
      method: 'POST',
      body: JSON.stringify({
        text,
        auto_schedule: autoSchedule,
        user_id: userId,
        conversation_id: convId
      })
    });
  },

  // Reminders
  getReminders(userId = 1, status = null) {
    let url = `/api/reminders?user_id=${userId}`;
    if (status) url += `&status=${status}`;
    return this.request(url);
  },
  createReminder(data) {
    return this.request('/api/reminders', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  updateReminder(id, data) {
    return this.request(`/api/reminders/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  deleteReminder(id) {
    return this.request(`/api/reminders/${id}`, {
      method: 'DELETE'
    });
  },

  // Meetings
  getMeetings() {
    return this.request('/api/meetings');
  },
  createMeeting(data) {
    return this.request('/api/meetings', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  rsvpMeeting(meetingId, userId, status) {
    return this.request(`/api/meetings/${meetingId}/rsvp`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, status })
    });
  },

  // Calls
  logCall(data) {
    return this.request('/api/calls/log', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  getCallHistory() {
    return this.request('/api/calls/history');
  }
};

window.API = API;
