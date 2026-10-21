import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../../../test/server";
import { LoginCard } from "./LoginCard";

it("posts a form to Django's redirect endpoint with the right fields", async () => {
  server.use(http.get("http://api.test/_allauth/browser/v1/config", () => HttpResponse.json({})));
  document.cookie = "csrftoken=tok123";
  const submit = vi.spyOn(HTMLFormElement.prototype, "submit").mockImplementation(() => {});

  render(<LoginCard />);
  await userEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

  const form = document.querySelector("form")!;
  expect(form.action).toBe("http://api.test/_allauth/browser/v1/auth/provider/redirect");
  expect(form.method).toBe("post");
  
  // Gets the field for each named element
  const field = (n: string) => (form.elements.namedItem(n) as HTMLInputElement).value;
  expect(field("provider")).toBe("google");
  expect(field("process")).toBe("login");
  expect(field("callback_url")).toBe(`${location.origin}/auth/callback`);
  expect(field("csrfmiddlewaretoken")).toBe("tok123");
  expect(submit).toHaveBeenCalled();
});

