//Package mocks for later imports
import { expect, it, vi } from "vitest";

vi.mock("@/lib/session", () => ({ 
  getUser: vi.fn() 
}));

vi.mock("next/navigation", () => ({ 
  redirect: vi.fn() 
}));

import { redirect } from "next/navigation";
import Callback from "./page";
import { getUser } from "@/lib/session";


it("goes to the dashboard when logged in", async () => {
  //Configures getUser() to mock a promise that resolves to {id:1}
  vi.mocked(getUser).mockResolvedValue({ id: 1 });

  await Callback();

  expect(redirect).toHaveBeenCalledWith("/dashboard/learn");
});

it("goes back to login with an error when not logged in", async () => {
  vi.mocked(getUser).mockResolvedValue(null);

  await Callback();
  
  expect(redirect).toHaveBeenCalledWith("/login?error=failed");
});