import { server } from "../../../../test/server";
import { delay, http, HttpResponse } from "msw";
import { render, screen, waitFor } from "@testing-library/react";
import LogoutButton from "./LogoutButton";
import userEvent from "@testing-library/user-event";


const replace = vi.hoisted(() => vi.fn());
const refresh = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => (
    {useRouter: ()=>({ replace, refresh })}
))

const URL = "http://api.test/_allauth/browser/v1/auth/session";

beforeEach(() => { document.cookie = "csrftoken=tok"; replace.mockClear(); refresh.mockClear(); });


it("calls delete redirects to login", async ()=>{
    // Mocks calling the delete route with the csrf token
    // After calling you're not authenticated anymore
    server.use(http.delete(URL, ({ request })=>{
        return HttpResponse.json({status:401, meta: {is_authenticated:false}}, {status:401})
    }));

    render(<LogoutButton/>);

    // Clicks any button with log out in it
    await userEvent.click(screen.getByRole("button", {name: /log out/i}));

    //Should go to login after being clicked
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
})

it("calls delete with CSRF token on", async ()=>{
    // Set the document csrftoken
    document.cookie = "csrftoken=tok";
    let csrf: string | null = null;

    server.use(http.delete(URL, ({ request })=>{
        csrf = request.headers.get("x-csrftoken");
        return HttpResponse.json({status:401, meta: {is_authenticated:false}}, {status:401})
    }));

    render(<LogoutButton/>);

    // Clicks any button with log out in it
    await userEvent.click(screen.getByRole("button", {name: /log out/i}));

    // csrf should be set for any post/delete route
    expect(csrf).toBe("tok");
})

it("goes to /login after a successful logout", async () => {
  server.use(http.delete(URL, () =>
    HttpResponse.json({ meta: { is_authenticated: false } }, { status: 401 })));
  render(<LogoutButton />);
  await userEvent.click(screen.getByRole("button", { name: /log out/i }));
  await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
  expect(refresh).toHaveBeenCalled();     // drop cached server-component data
});

it("stays put and shows an error when logout fails", async () => {
  server.use(http.delete(URL, () => new HttpResponse(null, { status: 403 })));
  render(<LogoutButton />);
  await userEvent.click(screen.getByRole("button", { name: /log out/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/logout failed/i);
  expect(replace).not.toHaveBeenCalled();   // never claim success on failure
});

it("disables the button while logging out", async () => {
  server.use(http.delete(URL, async () => {
    await delay(50);
    return HttpResponse.json({ meta: { is_authenticated: false } }, { status: 401 });
  }));
  render(<LogoutButton />);
  await userEvent.click(screen.getByRole("button", { name: /log out/i }));
  expect(screen.getByRole("button")).toBeDisabled();
});