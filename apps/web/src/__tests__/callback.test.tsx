//Package mocks for later imports
import { expect, it, vi } from "vitest";

vi.mock("@/lib/actions/session", () => ({ 
  getUser: vi.fn() 
}));

vi.mock("next/navigation", () => ({ 
  redirect: vi.fn() 
}));

import { redirect } from "next/navigation";
import Callback from "../app/(auth)/auth/callback/page";
import { getUser } from "@/lib/actions/session";


it("goes to the dashboard when logged in", async () => {
  //Configures getUser() to mock a promise that resolves to {id:1}
  vi.mocked(getUser).mockResolvedValue(
    { id: 1, email: "test@example.com", is_superuser: false, profile: "" }
  );

  await Callback();

  expect(redirect).toHaveBeenCalledWith("/dashboard/learn");
});

it("goes back to login with an error when not logged in", async () => {
  vi.mocked(getUser).mockResolvedValue(
    null as unknown as Awaited<ReturnType<typeof getUser>>
  );

  await Callback();
  
  expect(redirect).toHaveBeenCalledWith("/login?error=failed");
});