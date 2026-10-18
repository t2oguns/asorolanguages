vi.mock("next/headers", () => ({ cookies: async () => ({ toString: () => "sessionid=abc" }) }));
vi.mock("next/navigation", () => ({ redirect: vi.fn(() => { throw new Error("NEXT_REDIRECT"); }) }));

import { http, HttpResponse } from "msw";
import { redirect } from "next/navigation";
import { server } from "../../test/server";
import { serverFetch } from "@/lib/server-api";

it("forwards the browser cookie to Django", async () => {
  let cookie: string | null = null;
  server.use(http.get("http://api.test/api/me/", ({ request }) => {
    cookie = request.headers.get("cookie"); return HttpResponse.json({ id: 1 });
  }));
  await serverFetch("/api/me/");
  expect(cookie).toBe("sessionid=abc");
});

it("redirects to /login when unauthenticated", async () => {
  server.use(http.get("http://api.test/api/me/", () => new HttpResponse(null, { status: 403 })));
  await expect(serverFetch("/api/me/")).rejects.toThrow("NEXT_REDIRECT");
  expect(redirect).toHaveBeenCalledWith("/login");
});