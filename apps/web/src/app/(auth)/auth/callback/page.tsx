import { serverFetch } from "@/lib/server-api";
import { redirect } from "next/navigation";

export default async function Callback() {
    //Call the user identity view to check if user is logged in
  redirect((await serverFetch("/api/me/")) ? "/learn" : "/login?error=failed");
}