/**
 * ProCom Platform Controller
 * Manages themes, auth/user_id, organization search, custom photo & file uploads, and reactions
 */
window.appState = {
  currentUser: null,
  users: [],
  conversations: [],
  activeConversation: null,
  activeChannel: null,
  currentTab: 'chats',
  activeFilter: 'all',
  theme: 'dark',
  stagedFile: null,
  dbStatus: null
};

// All known theme class names
const THEME_CLASSES = ['light-theme', 'theme-midnight', 'theme-forest', 'theme-sunset', 'theme-rose', 'theme-ocean', 'theme-custom'];

document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initSplashScreen();
  await initApp();
});

// ==================== TOAST NOTIFICATIONS ====================
function showToast(title, message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: '✅', info: '💬', warn: '⚠️', error: '❌' };
  const toast = document.createElement('div');
  toast.className = 'toast-item';
  toast.innerHTML = `
    <div class="toast-icon ${type}">${icons[type] || '💬'}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==================== SPLASH SCREEN & AUTH ====================
function initSplashScreen() {
  const splash = document.getElementById('splash-screen');
  if (!splash) return;

  // Always show the splash login screen first
  splash.style.display = 'flex';
  splash.classList.remove('hidden');

  const loginBtn = document.getElementById('splash-login-btn');
  const loginInput = document.getElementById('splash-login-input');

  // Pre-fill previously used ID if available
  const savedUserId = localStorage.getItem('procom_active_user_id');
  if (savedUserId && loginInput) {
    loginInput.value = savedUserId;
  }

  if (loginBtn && loginInput) {
    const doSplashLogin = async () => {
      const val = loginInput.value.trim();
      if (!val) return;
      try {
        const user = await window.API.login(val);
        await completeUserLogin(user);
      } catch (err) {
        showToast('Login Failed', err.message, 'error');
      }
    };
    loginBtn.onclick = doSplashLogin;
    loginInput.onkeydown = (e) => { if (e.key === 'Enter') doSplashLogin(); };
  }


  // Splash quick connect buttons
  document.querySelectorAll('.splash-quick-btn').forEach(btn => {
    btn.onclick = async () => {
      const uid = parseInt(btn.getAttribute('data-uid'));
      try {
        const user = await window.API.login(uid);
        await completeUserLogin(user);
      } catch (err) {
        showToast('Connection Error', err.message, 'error');
      }
    };
  });

  // Splash register form
  const regForm = document.getElementById('splash-register-form');
  if (regForm) {
    regForm.onsubmit = async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('splash-reg-fullname').value.trim();
      const username = document.getElementById('splash-reg-username').value.trim().toLowerCase();
      const email = document.getElementById('splash-reg-email').value.trim();
      try {
        const user = await window.API.register({
          full_name: fullName,
          username,
          email,
          department: 'Engineering',
          organization: 'ProCom'
        });
        await completeUserLogin(user);
        showToast('Account Created!', `Welcome to ProCom, ${user.full_name}! Your ID is #${user.id}`, 'success');
      } catch (err) {
        showToast('Registration Failed', err.message, 'error');
      }
    };
  }
}

async function completeUserLogin(user) {
  window.appState.currentUser = user;
  localStorage.setItem('procom_active_user_id', user.id);
  updateUserUI();

  // Hide splash screen
  const splash = document.getElementById('splash-screen');
  if (splash) {
    splash.classList.add('hidden');
    setTimeout(() => splash.style.display = 'none', 600);
  }

  // Connect realtime & load user content
  window.realtime.connect(user.id);
  await loadConversations();
  if (window.appState.conversations.length > 0) {
    selectConversation(window.appState.conversations[0]);
  }
  showToast('Welcome to ProCom!', `Connected as ${user.full_name} (#${user.id})`, 'success');
}

function showLoginSplash() {
  const splash = document.getElementById('splash-screen');
  if (splash) {
    splash.style.display = 'flex';
    splash.classList.remove('hidden');
  }
}

function logoutUser() {
  localStorage.removeItem('procom_active_user_id');
  window.appState.currentUser = null;
  if (window.realtime && window.realtime.ws) {
    try { window.realtime.ws.close(); } catch(e){}
  }
  showLoginSplash();
  showToast('Logged Out', 'Returned to ProCom login screen', 'info');
}


// ==================== THEME ENGINE ====================
function initTheme() {
  const savedTheme = localStorage.getItem('procom_theme') || 'dark';
  window.appState.theme = savedTheme;
  applyTheme(savedTheme);

  // Restore custom colors if saved
  if (savedTheme === 'custom') {
    const customColors = JSON.parse(localStorage.getItem('procom_custom_colors') || '{}');
    if (customColors.primary) applyCustomColors(customColors);
  }
}

function applyTheme(theme) {
  // Remove all theme classes
  THEME_CLASSES.forEach(cls => document.body.classList.remove(cls));

  // Apply appropriate class
  if (theme === 'light') {
    document.body.classList.add('light-theme');
  } else if (theme !== 'dark' && theme !== 'custom') {
    document.body.classList.add(`theme-${theme}`);
  } else if (theme === 'custom') {
    document.body.classList.add('theme-custom');
  }

  // Update header toggle button icon
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) {
    const themeIcons = {
      dark: '☀️', light: '🌙', midnight: '🌊', forest: '🌿',
      sunset: '🌅', rose: '🌹', ocean: '🐳', custom: '🎨'
    };
    btn.innerHTML = themeIcons[theme] || '☀️';
    btn.title = `Current: ${theme.charAt(0).toUpperCase() + theme.slice(1)} — Click to cycle`;
  }

  // Update settings theme grid active state
  document.querySelectorAll('.theme-card').forEach(card => {
    card.classList.toggle('active', card.getAttribute('data-theme') === theme);
  });

  window.appState.theme = theme;
  localStorage.setItem('procom_theme', theme);
}

function cycleTheme() {
  const order = ['dark', 'light', 'midnight', 'forest', 'sunset', 'rose', 'ocean'];
  const currentIdx = order.indexOf(window.appState.theme);
  const nextIdx = (currentIdx + 1) % order.length;
  applyTheme(order[nextIdx]);
  showToast('Theme Changed', `Switched to ${order[nextIdx].charAt(0).toUpperCase() + order[nextIdx].slice(1)}`, 'info');
}

function applyCustomColors(colors) {
  document.body.style.setProperty('--primary', colors.primary);
  document.body.style.setProperty('--bg-base', colors.bg);
  document.body.style.setProperty('--bg-surface', colors.surface);
  document.body.style.setProperty('--accent-cyan', colors.accent);
  // Derived values
  document.body.style.setProperty('--primary-glow', colors.primary + '66');
  document.body.style.setProperty('--primary-hover', colors.primary);
}

async function initApp() {
  console.log('[ProCom] Initializing platform...');

  // 1. Fetch DB Status
  await refreshDatabaseStatus();

  // 2. Fetch Users
  try {
    const users = await window.API.getUsers();
    window.appState.users = users;

    // User connects explicitly through splash screen first
    showLoginSplash();
  } catch (err) {
    console.error('Failed to load users:', err);
    showLoginSplash();
  }

  // 3. Initialize Engines
  window.callingEngine.init();
  await window.calendarManager.init();
  await window.remindersManager.init();

  // 4. Bind Global UI Events
  bindGlobalEvents();
}


async function refreshDatabaseStatus() {
  try {
    const status = await window.API.getDatabaseStatus();
    window.appState.dbStatus = status;

    const btn = document.getElementById('db-badge-btn');
    const textEl = document.getElementById('db-status-text');

    if (btn && textEl) {
      if (status.is_neon) {
        textEl.textContent = 'Neon Cloud PostgreSQL';
        btn.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        btn.style.color = '#10b981';
      } else {
        textEl.textContent = 'Local SQLite Mode';
      }
    }
  } catch (e) {
    console.warn('DB status error:', e);
  }
}

function updateUserUI() {
  const u = window.appState.currentUser;
  if (!u) return;

  const avatar = document.getElementById('current-user-avatar');
  const nameEl = document.getElementById('current-user-name');
  const idBadge = document.getElementById('current-user-id-badge');

  if (avatar) avatar.src = u.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80';
  if (nameEl) nameEl.textContent = u.full_name;
  if (idBadge) idBadge.textContent = `#${u.id}`;

  localStorage.setItem('procom_active_user_id', u.id);
}

async function loadConversations() {
  try {
    const uid = window.appState.currentUser ? window.appState.currentUser.id : null;
    const convs = await window.API.getConversations(uid);
    window.appState.conversations = convs;
    renderConversationList();
  } catch (err) {
    console.error('Failed to load conversations:', err);
  }
}


function renderConversationList() {
  const listEl = document.getElementById('conversation-list-container');
  if (!listEl) return;

  listEl.innerHTML = '';
  const filter = window.appState.activeFilter;

  let filtered = window.appState.conversations;
  if (filter !== 'all') {
    filtered = window.appState.conversations.filter(c => c.type === filter);
  }

  filtered.forEach(c => {
    const item = document.createElement('div');
    const isActive = window.appState.activeConversation && window.appState.activeConversation.id === c.id;
    item.className = `conversation-item ${isActive ? 'active' : ''}`;

    let avatarHtml = '';
    if (c.avatar) {
      avatarHtml = `<img src="${c.avatar}" class="conv-avatar" alt="${c.title}">`;
    } else {
      const iconLetter = c.title.charAt(0).toUpperCase();
      const bgGrad = c.type === 'community' 
        ? 'linear-gradient(135deg, #06b6d4, #3b82f6)' 
        : c.type === 'group' 
        ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' 
        : 'linear-gradient(135deg, #f59e0b, #ef4444)';
      avatarHtml = `<div class="conv-icon-avatar" style="background:${bgGrad}">${iconLetter}</div>`;
    }

    const snippet = c.last_message || c.description || 'No recent messages';

    item.innerHTML = `
      <div class="conv-avatar-wrapper">
        ${avatarHtml}
        ${c.type === 'direct' ? '<div class="avatar-badge-online"></div>' : ''}
      </div>
      <div class="conv-details">
        <div class="conv-header-row">
          <span class="conv-title">${c.title}</span>
          <span class="conv-type-tag ${c.type}">${c.type}</span>
        </div>
        <div class="conv-subtitle-row">
          <span class="conv-snippet">${snippet}</span>
        </div>
      </div>
    `;

    item.onclick = () => selectConversation(c);
    listEl.appendChild(item);
  });
}

async function selectConversation(conv) {
  window.appState.activeConversation = conv;
  window.appState.activeChannel = null;

  renderConversationList();
  renderChatHeader(conv);
  renderCommunityChannelsBar(conv);
  await loadAndRenderMessages(conv.id);
}

function renderChatHeader(conv) {
  const targetAvatar = document.getElementById('chat-target-avatar');
  const targetName = document.getElementById('chat-target-name');
  const targetStatus = document.getElementById('chat-target-status');

  if (targetName) targetName.textContent = conv.title;
  if (targetAvatar) {
    if (conv.avatar) {
      targetAvatar.src = conv.avatar;
      targetAvatar.style.display = 'block';
    } else {
      targetAvatar.src = 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=150&auto=format&fit=crop&q=80';
    }
  }
  if (targetStatus) {
    if (conv.type === 'community') {
      targetStatus.textContent = `🌐 ProCom Community • ${conv.member_count || 5} Members`;
    } else if (conv.type === 'group') {
      targetStatus.textContent = `👥 ProCom Team Group • ${conv.member_count || 4} Active`;
    } else if (conv.type === 'broadcast') {
      targetStatus.textContent = `📢 ProCom Official Broadcast Channel`;
    } else {
      targetStatus.textContent = `🟢 Online • Direct Message`;
    }
  }
}

function renderCommunityChannelsBar(conv) {
  const bar = document.getElementById('community-channels-strip');
  if (!bar) return;

  if (conv.type !== 'community' || !conv.channels || conv.channels.length === 0) {
    bar.style.display = 'none';
    return;
  }

  bar.style.display = 'flex';
  bar.innerHTML = '';

  conv.channels.forEach(ch => {
    const pill = document.createElement('div');
    const isActive = window.appState.activeChannel && window.appState.activeChannel.id === ch.id;
    pill.className = `channel-pill ${isActive ? 'active' : ''}`;
    const icon = ch.channel_type === 'announcements' ? '📢' : ch.channel_type === 'voice' ? '🔊' : '#';
    pill.innerHTML = `<span>${icon}</span> <span>${ch.name}</span>`;

    pill.onclick = async () => {
      window.appState.activeChannel = ch;
      renderCommunityChannelsBar(conv);
      await loadAndRenderMessages(conv.id, ch.id);
    };

    bar.appendChild(pill);
  });

  if (!window.appState.activeChannel && conv.channels.length > 0) {
    window.appState.activeChannel = conv.channels[0];
    renderCommunityChannelsBar(conv);
  }
}

async function loadAndRenderMessages(convId, channelId = null) {
  const stream = document.getElementById('messages-stream');
  if (!stream) return;

  try {
    const uid = window.appState.currentUser ? window.appState.currentUser.id : null;
    const msgs = await window.API.getMessages(convId, channelId, uid);
    stream.innerHTML = '';

    msgs.forEach(m => appendMessageToStream(m));
    stream.scrollTop = stream.scrollHeight;
  } catch (err) {
    console.error('Failed to load messages:', err);
    stream.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted); font-size:0.9rem;">🔒 <strong>Private Space</strong><br>You are not a member of this private conversation.</div>';
  }
}


function appendMessageToStream(m) {
  const stream = document.getElementById('messages-stream');
  if (!stream) return;

  const currentUserId = window.appState.currentUser ? window.appState.currentUser.id : 1;
  const isOutgoing = m.sender_id === currentUserId;

  const row = document.createElement('div');
  let typeClass = '';
  if (m.message_type === 'broadcast') typeClass = 'broadcast-msg';
  else if (m.message_type === 'system') typeClass = 'system-msg';

  row.className = `message-row ${isOutgoing ? 'outgoing' : ''} ${typeClass}`;
  row.setAttribute('data-msg-id', m.id);

  const timeFormatted = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const avatarUrl = m.sender_avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80';

  // Attachment Rendering
  let attachmentHtml = '';
  if (m.file_url) {
    if (m.message_type === 'image' || m.file_type === 'image' || /\.(png|jpe?g|webp|gif|svg)$/i.test(m.file_url)) {
      attachmentHtml = `
        <a href="${m.file_url}" target="_blank">
          <img src="${m.file_url}" class="msg-image-attachment" alt="${m.file_name || 'Image'}">
        </a>
      `;
    } else {
      const sizeKb = m.file_size ? `${Math.round(m.file_size / 1024)} KB` : '';
      attachmentHtml = `
        <a href="${m.file_url}" class="msg-file-attachment" download="${m.file_name || 'attachment'}">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          <div style="display:flex; flex-direction:column;">
            <strong style="font-size:0.85rem;">${m.file_name || 'Download File'}</strong>
            <span style="font-size:0.7rem; color:var(--text-muted);">${sizeKb}</span>
          </div>
        </a>
      `;
    }
  }

  // Reactions HTML
  const reactions = m.reactions || {};
  let reactionsHtml = '<div class="msg-reactions-row" id="reactions-' + m.id + '">';
  Object.keys(reactions).forEach(emoji => {
    const count = reactions[emoji].length;
    const hasReacted = reactions[emoji].includes(currentUserId);
    reactionsHtml += `
      <button class="reaction-pill ${hasReacted ? 'reacted' : ''}" data-emoji="${emoji}" data-msg-id="${m.id}">
        <span>${emoji}</span>
        <span style="font-weight:700;">${count}</span>
      </button>
    `;
  });
  reactionsHtml += '</div>';

  // AI Action Item Card if detected
  let actionCardHtml = '';
  if (m.has_action_item && m.action_item_json) {
    try {
      const item = JSON.parse(m.action_item_json);
      const dueStr = item.due_datetime ? new Date(item.due_datetime).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Upcoming';
      actionCardHtml = `
        <div class="ai-action-card">
          <div class="ai-card-header">
            <div class="ai-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"></path><rect x="4" y="8" width="16" height="12" rx="2"></rect><circle cx="9" cy="13" r="1"></circle><circle cx="15" cy="13" r="1"></circle></svg>
              <span>AI Action Detected</span>
            </div>
            <span class="priority-badge priority-${item.priority}">${item.priority}</span>
          </div>
          <div class="ai-task-title">${item.title}</div>
          <div class="ai-due-row">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>Due: ${dueStr}</span>
          </div>
          <div class="ai-action-footer">
            <span style="font-size:0.7rem; color:var(--text-muted);">Confidence: ${Math.round(item.confidence * 100)}%</span>
            <button class="btn-ai-schedule" data-title="${item.title}" data-due="${item.due_datetime}" data-prio="${item.priority}">
              ⚡ Schedule Reminder
            </button>
          </div>
        </div>
      `;
    } catch (e) {}
  }

  let formattedContent = m.content
    ? m.content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
    : '';

  row.innerHTML = `
    <!-- Floating Emoji Reaction Bar -->
    <div class="msg-action-bar">
      <button class="btn-emoji-quick" data-emoji="👍" data-msg-id="${m.id}" title="Thumbs Up">👍</button>
      <button class="btn-emoji-quick" data-emoji="❤️" data-msg-id="${m.id}" title="Heart">❤️</button>
      <button class="btn-emoji-quick" data-emoji="🚀" data-msg-id="${m.id}" title="Rocket">🚀</button>
      <button class="btn-emoji-quick" data-emoji="🎉" data-msg-id="${m.id}" title="Party">🎉</button>
      <button class="btn-emoji-quick" data-emoji="🔥" data-msg-id="${m.id}" title="Fire">🔥</button>
    </div>

    <img src="${avatarUrl}" class="msg-sender-avatar" alt="${m.sender_name}">
    <div class="msg-bubble-wrapper">
      <div class="msg-meta-row">
        <span class="msg-sender-name">${m.sender_name}</span>
        <span>•</span>
        <span>${timeFormatted}</span>
      </div>
      <div class="msg-bubble">
        ${formattedContent ? `<div>${formattedContent}</div>` : ''}
        ${attachmentHtml}
        ${actionCardHtml}
      </div>
      ${reactionsHtml}
    </div>
  `;

  // Bind 1-click schedule button
  const scheduleBtn = row.querySelector('.btn-ai-schedule');
  if (scheduleBtn) {
    scheduleBtn.onclick = async () => {
      const title = scheduleBtn.getAttribute('data-title');
      const due = scheduleBtn.getAttribute('data-due');
      const prio = scheduleBtn.getAttribute('data-prio');

      await window.API.createReminder({
        user_id: currentUserId,
        conversation_id: m.conversation_id,
        source_message_id: m.id,
        title: title,
        due_date: due,
        priority: prio,
        auto_extracted: true
      });

      scheduleBtn.classList.add('scheduled');
      scheduleBtn.textContent = '✓ Scheduled!';
      window.soundEngine.playNotification();
    };
  }

  // Bind reaction clicks
  row.querySelectorAll('.btn-emoji-quick, .reaction-pill').forEach(btn => {
    btn.onclick = async () => {
      const emoji = btn.getAttribute('data-emoji');
      const msgId = parseInt(btn.getAttribute('data-msg-id'));
      await window.API.toggleReaction(msgId, currentUserId, emoji);
    };
  });

  stream.appendChild(row);
  stream.scrollTop = stream.scrollHeight;
}

function bindGlobalEvents() {
  // Theme Toggle Button (cycles through all presets)
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) themeBtn.onclick = cycleTheme;

  // Search Input in Header
  const orgSearchInput = document.getElementById('org-search-input');
  const searchOverlay = document.getElementById('search-results-overlay');
  if (orgSearchInput && searchOverlay) {
    let debounceTimer = null;
    orgSearchInput.oninput = (e) => {
      clearTimeout(debounceTimer);
      const val = e.target.value.trim();
      if (!val) {
        searchOverlay.classList.remove('active');
        return;
      }
      debounceTimer = setTimeout(() => runOrganizationSearch(val), 250);
    };

    searchOverlay.onclick = (e) => {
      if (e.target === searchOverlay) searchOverlay.classList.remove('active');
    };
  }

  // User Profile Badge -> opens Login Splash Screen to Switch Account / Log Out
  const userProfileBadge = document.getElementById('user-profile-badge');
  if (userProfileBadge) {
    userProfileBadge.onclick = () => showLoginSplash();
  }

  // Login Form Submission
  const loginForm = document.getElementById('form-user-login');
  if (loginForm) {
    loginForm.onsubmit = async (e) => {
      e.preventDefault();
      const inputVal = document.getElementById('login-input-id-or-name').value.trim();
      if (!inputVal) return;

      try {
        const user = await window.API.login(inputVal);
        await completeUserLogin(user);
        if (loginModal) loginModal.classList.remove('active');
        loginForm.reset();
      } catch (err) {
        showToast('Login Failed', err.message, 'error');
      }
    };
  }

  // Register Form Submission
  const registerForm = document.getElementById('form-user-register');
  if (registerForm) {
    registerForm.onsubmit = async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('reg-fullname').value.trim();
      const username = document.getElementById('reg-username').value.trim().toLowerCase();
      const email = document.getElementById('reg-email').value.trim();
      const dept = document.getElementById('reg-dept').value;

      try {
        const user = await window.API.register({
          full_name: fullName,
          username,
          email,
          department: dept,
          organization: "ProCom"
        });
        await completeUserLogin(user);
        if (loginModal) loginModal.classList.remove('active');
        registerForm.reset();
      } catch (err) {
        showToast('Registration Failed', err.message, 'error');
      }
    };
  }

  // Demo User Quick Connect Pills
  document.querySelectorAll('.btn-demo-user').forEach(btn => {
    btn.onclick = async () => {
      const uid = parseInt(btn.getAttribute('data-uid'));
      try {
        const user = await window.API.login(uid);
        await completeUserLogin(user);
        if (loginModal) loginModal.classList.remove('active');
      } catch (err) {
        showToast('Connection Error', err.message, 'error');
      }
    };
  });


  // Custom Avatar Photo Upload
  const avatarFileInput = document.getElementById('input-avatar-photo');
  if (avatarFileInput) {
    avatarFileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file || !window.appState.currentUser) return;
      try {
        const res = await window.API.uploadAvatar(window.appState.currentUser.id, file);
        window.appState.currentUser.avatar = res.avatar;
        updateUserUI();
        alert('Profile photo updated successfully!');
      } catch (err) {
        alert('Avatar upload error: ' + err.message);
      }
    };
  }

  // File Upload Buttons in Chat Composer
  const btnUploadPhoto = document.getElementById('btn-upload-photo');
  const btnUploadFile = document.getElementById('btn-upload-file');
  const chatFileInput = document.getElementById('chat-file-input');
  const stagedPreview = document.getElementById('staged-file-preview');
  const stagedFileName = document.getElementById('staged-file-name');
  const btnRemoveStaged = document.getElementById('btn-remove-staged-file');

  if (btnUploadPhoto && chatFileInput) {
    btnUploadPhoto.onclick = () => {
      chatFileInput.accept = 'image/*';
      chatFileInput.click();
    };
  }
  if (btnUploadFile && chatFileInput) {
    btnUploadFile.onclick = () => {
      chatFileInput.accept = '*/*';
      chatFileInput.click();
    };
  }

  if (chatFileInput) {
    chatFileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const uploadRes = await window.API.uploadFile(file);
        window.appState.stagedFile = uploadRes;

        if (stagedPreview && stagedFileName) {
          stagedFileName.textContent = `${uploadRes.original_name} (${Math.round(uploadRes.file_size / 1024)} KB)`;
          stagedPreview.classList.add('active');
        }
      } catch (err) {
        alert('File upload failed: ' + err.message);
      }
    };
  }

  if (btnRemoveStaged) {
    btnRemoveStaged.onclick = () => {
      window.appState.stagedFile = null;
      if (stagedPreview) stagedPreview.classList.remove('active');
      if (chatFileInput) chatFileInput.value = '';
    };
  }

  // Send Message Logic
  const sendBtn = document.getElementById('btn-send-message');
  const chatInput = document.getElementById('chat-input-text');
  const autoScheduleToggle = document.getElementById('composer-auto-schedule-toggle');

  const doSendMessage = async () => {
    const text = chatInput ? chatInput.value.trim() : '';
    const staged = window.appState.stagedFile;

    if (!text && !staged) return;
    if (!window.appState.activeConversation) return;

    if (chatInput) chatInput.value = '';
    const autoSchedule = autoScheduleToggle ? autoScheduleToggle.checked : true;

    const payload = {
      conversation_id: window.appState.activeConversation.id,
      channel_id: window.appState.activeChannel ? window.appState.activeChannel.id : null,
      sender_id: window.appState.currentUser ? window.appState.currentUser.id : 1,
      content: text || (staged ? staged.original_name : ''),
      file_url: staged ? staged.url : '',
      file_name: staged ? staged.original_name : '',
      file_type: staged ? staged.file_type : '',
      file_size: staged ? staged.file_size : 0,
      auto_schedule_reminder: autoSchedule
    };

    // Reset staged file
    window.appState.stagedFile = null;
    if (stagedPreview) stagedPreview.classList.remove('active');
    if (chatFileInput) chatFileInput.value = '';

    try {
      await window.API.sendMessage(payload);
      window.soundEngine.playNotification();
    } catch (err) {
      alert('Error sending message: ' + err.message);
    }
  };

  if (sendBtn) sendBtn.onclick = doSendMessage;
  if (chatInput) {
    chatInput.onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        doSendMessage();
      }
    };
  }

  // Quick Prompt Chips
  document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.onclick = () => {
      const prompt = btn.getAttribute('data-prompt');
      if (chatInput) {
        chatInput.value = prompt;
        chatInput.focus();
      }
    };
  });

  // Rail Navigation
  document.querySelectorAll('.rail-btn[data-tab]').forEach(btn => {
    btn.onclick = () => switchTab(btn.getAttribute('data-tab'));
  });

  // Secondary Sidebar Filters
  document.querySelectorAll('.filter-tab').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      window.appState.activeFilter = btn.getAttribute('data-filter');
      renderConversationList();
    };
  });

  // Header Call Buttons
  const btnVideoCall = document.getElementById('btn-header-video-call');
  const btnAudioCall = document.getElementById('btn-header-audio-call');
  if (btnVideoCall) {
    btnVideoCall.onclick = () => {
      const conv = window.appState.activeConversation;
      if (!conv) {
        showToast('No Active Chat', 'Select a conversation or member first', 'warn');
        return;
      }
      const myId = window.appState.currentUser ? window.appState.currentUser.id : 1;
      let targetId = conv.partner_id;
      if (!targetId) {
        targetId = myId === 1 ? 2 : 1;
      }
      window.callingEngine.startCall(targetId, conv.id, conv.title, conv.avatar, 'video');
    };
  }
  if (btnAudioCall) {
    btnAudioCall.onclick = () => {
      const conv = window.appState.activeConversation;
      if (!conv) {
        showToast('No Active Chat', 'Select a conversation or member first', 'warn');
        return;
      }
      const myId = window.appState.currentUser ? window.appState.currentUser.id : 1;
      let targetId = conv.partner_id;
      if (!targetId) {
        targetId = myId === 1 ? 2 : 1;
      }
      window.callingEngine.startCall(targetId, conv.id, conv.title, conv.avatar, 'audio');
    };
  }


  // Call HUD Controls
  const btnMute = document.getElementById('btn-call-mute');
  const btnVideo = document.getElementById('btn-call-video');
  const btnScreen = document.getElementById('btn-call-screenshare');
  const btnNotes = document.getElementById('btn-call-notes');
  const btnHangup = document.getElementById('btn-call-hangup');

  if (btnMute) btnMute.onclick = () => window.callingEngine.toggleMute();
  if (btnVideo) btnVideo.onclick = () => window.callingEngine.toggleVideo();
  if (btnScreen) btnScreen.onclick = () => window.callingEngine.toggleScreenShare();
  if (btnNotes) btnNotes.onclick = () => window.callingEngine.toggleNotesDrawer();
  if (btnHangup) btnHangup.onclick = () => window.callingEngine.endCall(true);

  // Incoming Call Toast
  const btnAcceptCall = document.getElementById('btn-toast-accept-call');
  const btnDeclineCall = document.getElementById('btn-toast-decline-call');
  if (btnAcceptCall) btnAcceptCall.onclick = () => window.callingEngine.acceptIncomingCall();
  if (btnDeclineCall) btnDeclineCall.onclick = () => window.callingEngine.rejectIncomingCall();

  // Create Space Form
  const btnOpenCreateConv = document.getElementById('btn-create-conversation');
  const createConvModal = document.getElementById('create-conversation-modal');
  const formCreateConv = document.getElementById('form-create-conversation');

  if (btnOpenCreateConv && createConvModal) {
    btnOpenCreateConv.onclick = () => createConvModal.classList.add('active');
  }

  if (formCreateConv) {
    formCreateConv.onsubmit = async (e) => {
      e.preventDefault();
      const title = document.getElementById('conv-modal-title').value.trim();
      const type = document.getElementById('conv-modal-type').value;
      const desc = document.getElementById('conv-modal-desc').value.trim();
      if (!title) return;

      try {
        const res = await window.API.createConversation({ title, type, description: desc });
        createConvModal.classList.remove('active');
        formCreateConv.reset();
        await loadConversations();
        const created = window.appState.conversations.find(c => c.id === res.id);
        if (created) selectConversation(created);
      } catch (err) {
        alert('Failed to create space: ' + err.message);
      }
    };
  }

  // Database Configuration Modal
  const dbBadgeBtn = document.getElementById('db-badge-btn');
  const dbModal = document.getElementById('db-config-modal');
  const dbForm = document.getElementById('form-db-config');

  if (dbBadgeBtn && dbModal) {
    dbBadgeBtn.onclick = () => {
      const maskedEl = document.getElementById('db-modal-masked-url');
      const engineEl = document.getElementById('db-modal-engine-name');
      if (window.appState.dbStatus) {
        if (maskedEl) maskedEl.textContent = window.appState.dbStatus.masked_url || 'Using local chatspace.db';
        if (engineEl) engineEl.textContent = window.appState.dbStatus.engine_type;
      }
      dbModal.classList.add('active');
    };
  }

  if (dbForm) {
    dbForm.onsubmit = async (e) => {
      e.preventDefault();
      const urlInput = document.getElementById('db-modal-input-url').value.trim();
      if (!urlInput) return;
      try {
        const res = await window.API.configureDatabase(urlInput);
        alert(res.message);
        dbModal.classList.remove('active');
        refreshDatabaseStatus();
      } catch (err) {
        alert('Error: ' + err.message);
      }
    };
  }

  // New Meeting Form
  const meetingForm = document.getElementById('form-new-meeting');
  const meetingModal = document.getElementById('new-meeting-modal');
  if (meetingForm) {
    meetingForm.onsubmit = async (e) => {
      e.preventDefault();
      const title = document.getElementById('mtg-title').value.trim();
      const desc = document.getElementById('mtg-desc').value.trim();
      const dateVal = document.getElementById('mtg-date').value;
      const timeVal = document.getElementById('mtg-time').value;
      const type = document.getElementById('mtg-type').value;

      if (!title || !dateVal || !timeVal) {
        alert('Please fill out required fields');
        return;
      }

      const start = new Date(`${dateVal}T${timeVal}`);
      const end = new Date(start.getTime() + 60 * 60 * 1000);

      const success = await window.calendarManager.handleCreateMeeting({
        title,
        description: desc,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        meeting_type: type,
        host_id: window.appState.currentUser ? window.appState.currentUser.id : 1,
        conversation_id: window.appState.activeConversation ? window.appState.activeConversation.id : null
      });

      if (success && meetingModal) {
        meetingModal.classList.remove('active');
        meetingForm.reset();
      }
    };
  }

  // Modals backdrop close
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.onclick = (e) => {
      if (e.target === modal) modal.classList.remove('active');
    };
  });
  document.querySelectorAll('.btn-close-modal').forEach(btn => {
    btn.onclick = () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) modal.classList.remove('active');
    };
  });

  // WebSocket message receiver
  window.realtime.on('new_message', (data) => {
    const msg = data.message;
    if (!msg) return;

    if (window.appState.activeConversation && window.appState.activeConversation.id === msg.conversation_id) {
      appendMessageToStream(msg);
      window.soundEngine.playNotification();
    }

    const conv = window.appState.conversations.find(c => c.id === msg.conversation_id);
    if (conv) {
      conv.last_message = msg.content;
      renderConversationList();
    }
  });

  // WebSocket reaction updater
  window.realtime.on('message_reaction', (data) => {
    const container = document.getElementById(`reactions-${data.message_id}`);
    if (!container) return;

    const currentUserId = window.appState.currentUser ? window.appState.currentUser.id : 1;
    container.innerHTML = '';
    const reactions = data.reactions || {};
    Object.keys(reactions).forEach(emoji => {
      const count = reactions[emoji].length;
      const hasReacted = reactions[emoji].includes(currentUserId);
      const pill = document.createElement('button');
      pill.className = `reaction-pill ${hasReacted ? 'reacted' : ''}`;
      pill.setAttribute('data-emoji', emoji);
      pill.setAttribute('data-msg-id', data.message_id);
      pill.innerHTML = `<span>${emoji}</span> <span style="font-weight:700;">${count}</span>`;
      pill.onclick = async () => {
        await window.API.toggleReaction(data.message_id, currentUserId, emoji);
      };
      container.appendChild(pill);
    });
  });
}

async function runOrganizationSearch(query) {
  const overlay = document.getElementById('search-results-overlay');
  const resultsBox = document.getElementById('search-results-container');
  if (!overlay || !resultsBox) return;

  overlay.classList.add('active');
  resultsBox.innerHTML = `<div style="color:var(--text-muted); font-size:0.85rem; padding:10px;">Searching ProCom directory...</div>`;

  try {
    const data = await window.API.searchOrganization(query);
    resultsBox.innerHTML = '';

    // Members Section
    if (data.users && data.users.length > 0) {
      const section = document.createElement('div');
      section.innerHTML = `<div class="search-section-title">👥 ProCom Members (${data.users.length})</div>`;
      data.users.forEach(u => {
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px;">
            <img src="${u.avatar}" class="user-avatar-small" alt="${u.full_name}">
            <div>
              <div style="font-weight:700; font-size:0.9rem;">${u.full_name} <span style="color:var(--primary); font-size:0.75rem;">#${u.id}</span></div>
              <div style="font-size:0.75rem; color:var(--text-muted);">${u.department} • @${u.username}</div>
            </div>
          </div>
          <button class="btn-rsvp active" style="font-size:0.72rem;">Direct Message</button>
        `;
        item.onclick = async () => {
          overlay.classList.remove('active');
          // Switch to or create DM
          let dm = window.appState.conversations.find(c => c.type === 'direct' && c.title === u.full_name);
          if (!dm) {
            const newDm = await window.API.createConversation({
              title: u.full_name,
              type: 'direct',
              description: `Direct message with ${u.full_name}`,
              avatar: u.avatar,
              member_ids: [window.appState.currentUser.id, u.id]
            });
            await loadConversations();
            dm = window.appState.conversations.find(c => c.id === newDm.id);
          }
          if (dm) selectConversation(dm);
        };
        section.appendChild(item);
      });
      resultsBox.appendChild(section);
    }

    // Conversations / Spaces Section
    if (data.conversations && data.conversations.length > 0) {
      const section = document.createElement('div');
      section.innerHTML = `<div class="search-section-title">🌐 Spaces & Channels (${data.conversations.length})</div>`;
      data.conversations.forEach(c => {
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = `
          <div>
            <div style="font-weight:700; font-size:0.88rem;">${c.title}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${c.description || c.type}</div>
          </div>
          <span class="conv-type-tag ${c.type}">${c.type}</span>
        `;
        item.onclick = () => {
          overlay.classList.remove('active');
          const target = window.appState.conversations.find(x => x.id === c.id);
          if (target) selectConversation(target);
        };
        section.appendChild(item);
      });
      resultsBox.appendChild(section);
    }

    // Messages & Files Section
    if (data.messages && data.messages.length > 0) {
      const section = document.createElement('div');
      section.innerHTML = `<div class="search-section-title">💬 Messages & Attachments (${data.messages.length})</div>`;
      data.messages.forEach(m => {
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = `
          <div style="max-width:85%;">
            <div style="font-size:0.85rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.content}</div>
            ${m.file_name ? `<span style="font-size:0.72rem; color:var(--accent-cyan);">📎 ${m.file_name}</span>` : ''}
          </div>
          <span style="font-size:0.7rem; color:var(--text-muted);">${new Date(m.created_at).toLocaleDateString()}</span>
        `;
        item.onclick = () => {
          overlay.classList.remove('active');
          const conv = window.appState.conversations.find(x => x.id === m.conversation_id);
          if (conv) selectConversation(conv);
        };
        section.appendChild(item);
      });
      resultsBox.appendChild(section);
    }

    if (!resultsBox.children.length) {
      resultsBox.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">No results found for "${query}" in ProCom.</div>`;
    }
  } catch (err) {
    resultsBox.innerHTML = `<div style="color:var(--accent-rose); padding:10px;">Search error: ${err.message}</div>`;
  }
}

function switchTab(tab) {
  window.appState.currentTab = tab;

  document.querySelectorAll('.rail-btn[data-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
  });

  const chatView = document.getElementById('chat-view-container');
  const calendarView = document.getElementById('calendar-view');
  const remindersView = document.getElementById('reminders-view');
  const callsView = document.getElementById('calls-view');
  const settingsView = document.getElementById('settings-view');
  const secondarySidebar = document.getElementById('secondary-sidebar');

  // Hide all views first
  if (chatView) chatView.style.display = 'none';
  if (calendarView) calendarView.classList.remove('active');
  if (remindersView) remindersView.classList.remove('active');
  if (callsView) callsView.classList.remove('active');
  if (settingsView) settingsView.classList.remove('active');
  if (secondarySidebar) secondarySidebar.style.display = 'none';

  if (tab === 'chats') {
    if (chatView) chatView.style.display = 'flex';
    if (secondarySidebar) secondarySidebar.style.display = 'flex';
  } else if (tab === 'calendar') {
    if (calendarView) calendarView.classList.add('active');
    window.calendarManager.loadMeetings().then(() => {
      window.calendarManager.renderCalendar();
      window.calendarManager.renderUpcomingMeetings();
    });
  } else if (tab === 'reminders') {
    if (remindersView) remindersView.classList.add('active');
    window.remindersManager.loadReminders().then(() => {
      window.remindersManager.renderReminders();
    });
  } else if (tab === 'calls') {
    if (callsView) callsView.classList.add('active');
    renderCallsView();
  } else if (tab === 'settings') {
    if (settingsView) settingsView.classList.add('active');
    updateSettingsView();
  }
}

async function renderCallsView() {
  const membersContainer = document.getElementById('calls-members-list');
  const historyContainer = document.getElementById('calls-history-list');
  const currentUserId = window.appState.currentUser ? window.appState.currentUser.id : 1;

  if (membersContainer) {
    membersContainer.innerHTML = '';
    const otherUsers = (window.appState.users || []).filter(u => u.id !== currentUserId && !u.is_bot);
    otherUsers.forEach(u => {
      const card = document.createElement('div');
      card.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:12px 14px; background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:var(--radius-lg);';
      card.innerHTML = `
        <div style="display:flex; align-items:center; gap:12px;">
          <img src="${u.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'}" style="width:40px; height:40px; border-radius:var(--radius-md); object-fit:cover;" alt="${u.full_name}">
          <div>
            <div style="font-weight:700; font-size:0.9rem; color:var(--text-main);">${u.full_name} <span style="font-size:0.75rem; color:var(--primary); font-weight:600;">#${u.id}</span></div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${u.department || 'ProCom'} • <span style="color:#10b981;">Online</span></div>
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn-primary btn-call-user" data-uid="${u.id}" data-uname="${u.full_name}" data-uavatar="${u.avatar || ''}" data-type="video" style="padding:6px 12px; font-size:0.78rem;" title="Start HD Video Call">
            📹 Video Call
          </button>
          <button class="btn-secondary btn-call-user" data-uid="${u.id}" data-uname="${u.full_name}" data-uavatar="${u.avatar || ''}" data-type="audio" style="padding:6px 12px; font-size:0.78rem;" title="Start Voice Call">
            📞 Voice
          </button>
        </div>
      `;
      membersContainer.appendChild(card);
    });

    membersContainer.querySelectorAll('.btn-call-user').forEach(btn => {
      btn.onclick = () => {
        const uid = parseInt(btn.getAttribute('data-uid'));
        const uname = btn.getAttribute('data-uname');
        const uavatar = btn.getAttribute('data-uavatar');
        const callType = btn.getAttribute('data-type');
        window.callingEngine.startCall(uid, null, uname, uavatar, callType);
      };
    });
  }

  if (historyContainer) {
    try {
      const logs = await window.API.request('/api/calls/history');
      historyContainer.innerHTML = '';
      if (!logs || logs.length === 0) {
        historyContainer.innerHTML = '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:20px;">No calls logged yet. Start a call!</div>';
      } else {
        logs.slice(0, 8).forEach(l => {
          const item = document.createElement('div');
          item.style.cssText = 'padding:10px 12px; background:rgba(0,0,0,0.15); border:1px solid var(--border-subtle); border-radius:var(--radius-md); font-size:0.78rem; display:flex; justify-content:space-between; align-items:center;';
          const icon = l.call_type === 'video' ? '📹' : '📞';
          item.innerHTML = `
            <div>
              <div style="font-weight:700;">${icon} ${l.caller_name} ➔ ${l.receiver_name}</div>
              <div style="color:var(--text-muted); font-size:0.72rem;">${new Date(l.created_at).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' })} • Duration: ${l.duration_seconds}s</div>
            </div>
            <span style="font-size:0.7rem; padding:2px 8px; border-radius:10px; background:rgba(16,185,129,0.15); color:#10b981; font-weight:700;">${l.status}</span>
          `;
          historyContainer.appendChild(item);
        });
      }
    } catch (e) {
      historyContainer.innerHTML = '<div style="color:var(--text-muted); font-size:0.8rem;">Ready for calling</div>';
    }
  }
}


// ==================== SETTINGS VIEW LOGIC ====================
function updateSettingsView() {
  const u = window.appState.currentUser;
  if (u) {
    const avatarEl = document.getElementById('settings-profile-avatar');
    const nameEl = document.getElementById('settings-profile-name');
    const metaEl = document.getElementById('settings-profile-meta');
    if (avatarEl) avatarEl.src = u.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${u.username}`;
    if (nameEl) nameEl.textContent = u.full_name;
    if (metaEl) metaEl.textContent = `@${u.username} • #${u.id} • ${u.department || 'Engineering'}`;
  }

  // Update DB status in settings
  if (window.appState.dbStatus) {
    const engineEl = document.getElementById('settings-db-engine');
    const urlEl = document.getElementById('settings-db-url');
    if (engineEl) engineEl.textContent = window.appState.dbStatus.engine_type;
    if (urlEl) urlEl.textContent = window.appState.dbStatus.masked_url || 'Using local chatspace.db';
  }

  // Theme grid click handlers
  document.querySelectorAll('.theme-card').forEach(card => {
    card.onclick = () => {
      const theme = card.getAttribute('data-theme');
      applyTheme(theme);
      showToast('Theme Applied', `Switched to ${card.querySelector('.theme-card-name').textContent}`, 'success');
    };
  });

  // Settings avatar upload
  const settingsAvatarUpload = document.getElementById('settings-avatar-upload');
  if (settingsAvatarUpload) {
    settingsAvatarUpload.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file || !window.appState.currentUser) return;
      try {
        const res = await window.API.uploadAvatar(window.appState.currentUser.id, file);
        window.appState.currentUser.avatar = res.avatar;
        updateUserUI();
        updateSettingsView();
        showToast('Avatar Updated', 'Your profile photo has been changed', 'success');
      } catch (err) {
        showToast('Upload Error', err.message, 'error');
      }
    };
  }

  // Custom theme color picker
  const btnApplyCustom = document.getElementById('btn-apply-custom-theme');
  if (btnApplyCustom) {
    btnApplyCustom.onclick = () => {
      const colors = {
        primary: document.getElementById('custom-color-primary').value,
        bg: document.getElementById('custom-color-bg').value,
        surface: document.getElementById('custom-color-surface').value,
        accent: document.getElementById('custom-color-accent').value
      };
      applyTheme('custom');
      applyCustomColors(colors);
      localStorage.setItem('procom_custom_colors', JSON.stringify(colors));
      showToast('Custom Theme', 'Your custom color palette has been applied!', 'success');
    };
  }

  // Settings DB save
  const btnSettingsSaveDb = document.getElementById('btn-settings-save-db');
  if (btnSettingsSaveDb) {
    btnSettingsSaveDb.onclick = async () => {
      const urlInput = document.getElementById('settings-db-input').value.trim();
      if (!urlInput) return;
      try {
        const res = await window.API.configureDatabase(urlInput);
        showToast('Database Updated', res.message, 'success');
        refreshDatabaseStatus();
      } catch (err) {
        showToast('Database Error', err.message, 'error');
      }
    };
  }
}

