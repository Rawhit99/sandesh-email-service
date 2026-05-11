const TOKEN_KEY = 'token';
const USER_KEY = 'user';
const ORG_KEY = 'sandesh-org-id';
const LAST_ACTIVITY_KEY = 'sandesh-last-activity-at';

export const SESSION_IDLE_TIMEOUT_MS = 30 * 60 * 1000;

function hasStorage(): boolean {
  return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
}

function readLastActivity(): number | null {
  if (!hasStorage()) {
    return null;
  }
  const raw = localStorage.getItem(LAST_ACTIVITY_KEY);
  if (!raw) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

export function markSessionActivity(timestamp = Date.now()): void {
  if (!hasStorage() || !localStorage.getItem(TOKEN_KEY)) {
    return;
  }
  localStorage.setItem(LAST_ACTIVITY_KEY, String(timestamp));
}

export function clearSession(): void {
  if (!hasStorage()) {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ORG_KEY);
  localStorage.removeItem(LAST_ACTIVITY_KEY);
}

export function startSession(accessToken: string, user: unknown): void {
  if (!hasStorage()) {
    return;
  }
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.removeItem(ORG_KEY);
  markSessionActivity();
}

export function isSessionIdle(now = Date.now()): boolean {
  if (!hasStorage() || !localStorage.getItem(TOKEN_KEY)) {
    return false;
  }

  const lastActivity = readLastActivity();
  if (lastActivity === null) {
    markSessionActivity(now);
    return false;
  }

  return now - lastActivity > SESSION_IDLE_TIMEOUT_MS;
}

export function hasActiveSession(): boolean {
  if (!hasStorage() || !localStorage.getItem(TOKEN_KEY)) {
    return false;
  }
  if (isSessionIdle()) {
    clearSession();
    return false;
  }
  return true;
}

export function expireSession(): void {
  clearSession();
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.assign('/login');
  }
}

export function ensureSessionActive(): boolean {
  if (!hasStorage() || !localStorage.getItem(TOKEN_KEY)) {
    return true;
  }
  if (isSessionIdle()) {
    expireSession();
    return false;
  }
  markSessionActivity();
  return true;
}

export function setupSessionIdleTimer(onExpire: () => void): () => void {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  const activityEvents = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
  const handleActivity = () => {
    if (!hasStorage() || !localStorage.getItem(TOKEN_KEY)) {
      return;
    }
    if (isSessionIdle()) {
      onExpire();
      return;
    }
    markSessionActivity();
  };
  const checkIdle = () => {
    if (isSessionIdle()) {
      onExpire();
    }
  };

  activityEvents.forEach((eventName) => {
    window.addEventListener(eventName, handleActivity, { passive: true });
  });
  const timer = window.setInterval(checkIdle, 30 * 1000);

  return () => {
    activityEvents.forEach((eventName) => {
      window.removeEventListener(eventName, handleActivity);
    });
    window.clearInterval(timer);
  };
}
