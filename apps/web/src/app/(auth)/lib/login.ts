import { API, api, getCsrf } from "@/lib/api";


//This function uses a post form 
export async function login(provider: string) {
  await api("/_allauth/browser/v1/config"); // ensures the csrftoken cookie exists
  const form = document.createElement("form");
  form.method = "POST";
  form.action = `${API}/_allauth/browser/v1/auth/provider/redirect`;
  const fields = {
    provider,
    process: "login",
    callback_url: `${location.origin}/auth/callback`,
    csrfmiddlewaretoken: getCsrf(),
  };
  for (const [k, v] of Object.entries(fields)) {
    const i = document.createElement("input");
    i.type = "hidden"; i.name = k; i.value = v;
    form.appendChild(i);
  }
  document.body.appendChild(form);
  form.submit();
}