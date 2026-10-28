import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import type { paths } from "@/lib/api/api-schema";
import { type PathParams, type ApiResponse } from "./api-types";
import { buildPath } from "./api";

export async function serverFetch <P extends keyof paths> (
  path: P,
  params?: PathParams<P & string>,
): Promise<ApiResponse<P, "get">> {
  const cookie = (await cookies()).toString();

  const url = params
    ? buildPath(path, params)
    : path as string;

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}${url}`,
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