import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import type { paths } from "@/lib/api-schema";
import { type ApiResponse } from "./api-types";

export async function serverFetch<
  P extends keyof paths,
>(
  path: P,
): Promise<ApiResponse<P, "get">> {
  const cookie = (await cookies()).toString();

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}${path}`,
    {
      headers: { cookie },
      cache: "no-store",
    },
  );

  if (res.status === 401 || res.status === 403) {
    redirect("/login");
  }

  if (!res.ok) {
    throw new Error(`API ${res.status} on ${path}`);
  }

  return res.json() as Promise<ApiResponse<P, "get">>;
}