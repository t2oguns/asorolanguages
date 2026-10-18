import { serverFetch } from "@/lib/server-api";

export const getUser = () =>{
  return serverFetch("/api/me/")
}
