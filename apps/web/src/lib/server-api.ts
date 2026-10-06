import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function serverFetch<T>(path: string): Promise<T> {
  const cookie = (await cookies()).toString();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    headers: { cookie },
    cache: "no-store",   // responses are per-user, never cache them
  });
  if (res.status === 401 || res.status === 403) redirect("/login");
  if (!res.ok) throw new Error(`API ${res.status} on ${path}`);
  return res.json();
}