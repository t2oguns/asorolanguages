import { http, HttpResponse } from "msw";
import { server } from "../../test/server";
import { logout, LogoutError } from "@/app/(auth)/lib/logout";

const URL = "http://api.test/_allauth/browser/v1/auth/session";

// Logged out state for all mocked end points
const loggedOut = () =>(HttpResponse.json(
    { status: 401,  meta: { is_authenticated: false } }, 
    { status: 401 }
));

beforeEach(() => { document.cookie = "csrftoken=tok123"; });

it("treats allauth's 401 with is_authenticated=false as success", async () => {
  server.use(http.delete(URL, loggedOut));
  await expect(logout()).resolves.toBeUndefined();
});

it("sends the CSRF header", async () => {
  let csrf: string | null = null;
  server.use(http.delete(URL, ({ request }) => {
    csrf = request.headers.get("x-csrftoken");
    return loggedOut();
  }));
  await logout();
  expect(csrf).toBe("tok123");
});

it("fails on 403 (CSRF rejected: the session is still alive)", async () => {
  server.use(http.delete(URL, () => new HttpResponse(null, { status: 403 })));
  await expect(logout()).rejects.toBeInstanceOf(LogoutError);
});

it("fails on a server error", async () => {
  server.use(http.delete(URL, () => new HttpResponse(null, { status: 500 })));
  await expect(logout()).rejects.toBeInstanceOf(LogoutError);
});

it("fails on a network error", async () => {
  server.use(http.delete(URL, () => HttpResponse.error()));
  await expect(logout()).rejects.toBeInstanceOf(LogoutError);
});

it("fetches the CSRF cookie first if it is missing", async () => {
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  let bootstrapped = false;
  server.use(
    http.get("http://api.test/_allauth/browser/v1/config", () => {
      bootstrapped = true;
      document.cookie = "csrftoken=fresh";   // simulate Django's Set-Cookie
      return HttpResponse.json({});
    }),
    http.delete(URL, loggedOut),
  );
  await logout();
  expect(bootstrapped).toBe(true);
});