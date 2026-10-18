import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const sessionid = request.cookies.get("sessionid");

  // Protect private pages.
  if (!sessionid) {
    const loginUrl = new URL("/login", request.url);

    loginUrl.searchParams.set("next", pathname);

    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/settings/:path*",
    "/profile/:path*",
  ],
};