/**
 * Real-time WebSocket Client for DTM-ChatSpace
 * Handles chat broadcasts, presence, typing indicators, and WebRTC signaling
 */
class RealtimeClient {
  constructor() {
    this.socket = null;
    this.userId = 1;
    this.listeners = new Map();
    this.reconnectTimer = null;
    this.pingInterval = null;
  }

  connect(userId = 1) {
    this.userId = userId;
    if (this.socket) {
      try { this.socket.close(); } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${userId}`;

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log(`[WS] Connected as User #${this.userId}`);
      this.emit('connection_status', { connected: true });
      this.startPing();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pong') return;
        this.emit(data.type, data);
        this.emit('*', data);
      } catch (err) {
        console.error('[WS] Parse error:', err);
      }
    };

    this.socket.onclose = () => {
      console.warn('[WS] Disconnected, scheduling reconnect...');
      this.emit('connection_status', { connected: false });
      this.stopPing();
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => this.connect(this.userId), 3000);
    };

    this.socket.onerror = (err) => {
      console.error('[WS] Error:', err);
    };
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const filtered = this.listeners.get(event).filter(cb => cb !== callback);
    this.listeners.set(event, filtered);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(cb => cb(data));
    }
  }

  startPing() {
    this.stopPing();
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, 25000);
  }

  stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  sendSignal(type, targetUserId, conversationId, callType, data = {}) {
    this.send({
      type,
      target_user_id: targetUserId,
      conversation_id: conversationId,
      call_type: callType,
      data
    });
  }
}

window.realtime = new RealtimeClient();
