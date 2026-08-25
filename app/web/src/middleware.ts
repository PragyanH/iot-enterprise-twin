import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/api/")) {
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
    const url = new URL(pathname, backendUrl);

    if (request.nextUrl.search) {
      url.search = request.nextUrl.search;
    }

    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
