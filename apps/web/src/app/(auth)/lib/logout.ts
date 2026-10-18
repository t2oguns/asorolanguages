import { api, ApiError } from "@/lib/api";
import { useRouter } from "next/navigation";
import { API, getCsrf } from "@/lib/api";


export class LogoutError extends Error {}


export async function logout(): Promise<void> {
  try {
    if (!getCsrf()) {
      // Django only sets the cookie once something asks for it
      await fetch(`${API}/_allauth/browser/v1/config`, { credentials: "include" });
    }
    const res = await fetch(`${API}/_allauth/browser/v1/auth/session`, {
      method: "DELETE",
      credentials: "include",
      headers: { "X-CSRFToken": getCsrf() },
    });
    console.log(getCsrf())

    const body = await res.json().catch(() => null);
    // allauth answers 401 + is_authenticated:false once the session is gone
    if (res.status === 401 && body?.meta?.is_authenticated === false) return;
    if (res.ok) return;
    throw new LogoutError(`Logout failed (${res.status})`);
  } catch (e) {
    throw e instanceof LogoutError ? e : new LogoutError("Network error");
  }
}