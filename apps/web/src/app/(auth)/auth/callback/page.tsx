import { getUser } from "@/lib/session";
import { redirect } from "next/navigation";

export default async function Callback() {
    //Call the user identity view to check if user is logged in
  redirect((await getUser()) ? "/dashboard/learn" : "/login?error=failed");
}