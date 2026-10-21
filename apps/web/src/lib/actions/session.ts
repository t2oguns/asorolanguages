import { serverFetch } from "@/lib/api/server-api";

export const getUser = () =>{
  return serverFetch("/api/me/")
}
