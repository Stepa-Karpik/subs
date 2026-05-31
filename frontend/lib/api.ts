const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8360/api/v1';
const AUTH_LOGIN_URL = process.env.NEXT_PUBLIC_AUTH_LOGIN_URL || 'https://auth.nerior.ru/login';

export function authRedirect() {
  if (typeof window === 'undefined') return;
  const returnTo = encodeURIComponent(window.location.href);
  window.location.href = `${AUTH_LOGIN_URL}?return_to=${returnTo}`;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {})
    }
  });
  if (response.status === 401) {
    authRedirect();
    throw new Error('Unauthorized');
  }
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload?.error?.message || `Request failed: ${response.status}`);
  }
  return payload.data as T;
}
