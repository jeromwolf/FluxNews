import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import createMiddleware from 'next-intl/middleware'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import type { Database } from '@/types/database'

const locales = ['ko', 'en']

// Create the internationalization middleware
const intlMiddleware = createMiddleware({
  locales,
  defaultLocale: 'ko',
  localePrefix: 'as-needed'
})

export async function middleware(req: NextRequest) {
  // Handle internationalization first
  const pathname = req.nextUrl.pathname
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )

  // Apply intl middleware for non-API routes
  if (!pathname.startsWith('/api')) {
    const intlResponse = intlMiddleware(req)
    if (intlResponse) {
      return intlResponse
    }
  }

  // Then handle authentication
  const res = NextResponse.next()
  const supabase = createMiddlewareClient<Database>({ req, res })

  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Extract the locale from the pathname
  const locale = pathnameHasLocale ? pathname.split('/')[1] : 'ko'

  // Protected routes (now with locale prefix)
  const protectedRoutes = ['/dashboard', '/settings', '/watchlist']
  const authRoutes = ['/login', '/signup']

  const isProtectedRoute = protectedRoutes.some(route => {
    const localizedRoute = `/${locale}${route}`
    return pathname.startsWith(localizedRoute) || pathname.startsWith(route)
  })

  const isAuthRoute = authRoutes.some(route => {
    const localizedRoute = `/${locale}${route}`
    return pathname.startsWith(localizedRoute) || pathname.startsWith(route)
  })

  // Redirect to login if accessing protected route without auth
  if (isProtectedRoute && !user) {
    return NextResponse.redirect(new URL(`/${locale}/login`, req.url))
  }

  // Redirect to dashboard if accessing auth routes while logged in
  if (isAuthRoute && user) {
    return NextResponse.redirect(new URL(`/${locale}/dashboard`, req.url))
  }

  return res
}

export const config = {
  matcher: [
    // Match all pathnames except for
    // - ... files in public folder
    // - _next internals
    // - /api routes
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}