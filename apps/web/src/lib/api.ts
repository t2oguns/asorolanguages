export const API = process.env.NEXT_PUBLIC_API_URL!; // https://api.example.com

export function getCsrf(): string {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? "";
}

export class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API error ${status}`);
  }
}

// Client-side calls (mutations): cookie + CSRF header
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const res = await fetch(`${API}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(method !== "GET" && { "X-CSRFToken": getCsrf() }),
      ...init.headers,
    },
  });

  if (res.status === 401 || res.status === 403) {
    window.location.href = "/login";
    throw new ApiError(res.status, null);
  }
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}