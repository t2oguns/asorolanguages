import { http, HttpResponse } from "msw";
import { server } from "../../test/server";
import { api, ApiError } from "@/lib/api/api";


// This sets the csrf token that django would usually send
beforeEach(() => { document.cookie = "csrftoken=tok123"; });

it("sends the CSRF header on mutations only", async () => {
  const seen: Record<string, string | null> = {};
  
  // Give server api points to call from
  server.use(
    http.get("http://api.test/api/x/", ({ request }) => {
      seen.get = request.headers.get("x-csrftoken"); return HttpResponse.json({});
    }),
    http.post("http://api.test/api/x/", ({ request }) => {
      seen.post = request.headers.get("x-csrftoken"); return HttpResponse.json({});
    }),
  );
  
  // Call defined api points as get and then post
  await api("/api/x/");
  await api("/api/x/", { method: "POST", body: "{}" });

  // The csrftoken is only sent on post requests
  expect(seen.get).toBeNull();
  expect(seen.post).toBe("tok123");
});

it("redirects to /login on 403", async () => {
  vi.stubGlobal("location", { href: "" });
  server.use(http.get("http://api.test/api/x/", () => new HttpResponse(null, { status: 403 })));
  await expect(api("/api/x/")).rejects.toBeInstanceOf(ApiError);
  expect(window.location.href).toBe("/login");
});

it("throws ApiError with the body on 400", async () => {
  server.use(http.post("http://api.test/api/x/", () => HttpResponse.json({ name: ["required"] }, { status: 400 })));
  await expect(api("/api/x/", { method: "POST", body: "{}" }))
    .rejects.toMatchObject({ status: 400, body: { name: ["required"] } });
});