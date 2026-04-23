/**
 * Electron-aware navigation helper.
 *
 * Why this exists
 * ---------------
 * Under `next build` with `output: "export"` and `trailingSlash: true`,
 * every route is emitted as its own `index.html` (`/upload/index.html`,
 * `/results/index.html`, …).  When the app is loaded via `http://` the
 * Next App Router handles client-side transitions by fetching a static
 * payload chunk over the network.  Under Electron's `file://` protocol
 * that payload fetch 404s silently — the URL bar updates, the content
 * does not, and every sidebar click appears to do nothing.
 *
 * The fix is to detect `file://` (or the `window.odiaDesktop` bridge)
 * and perform a *hard* navigation to the correct relative HTML file.
 * Every page then boots fresh, which is fine for this app — page-level
 * state (analyses, uploaded files) is rehydrated from the backend on
 * mount anyway.
 *
 * Browser / Docker users get the normal SPA behaviour because the
 * helper falls through to `router.push()` for them.
 *
 * Usage
 * -----
 *     const nav = useAppNavigate();
 *     nav('/upload');
 *
 * For <Link>-style inline markup use the <AppLink> component below.
 */

'use client';

import React, { useCallback } from 'react';
import Link, { type LinkProps } from 'next/link';
import { useRouter } from 'next/navigation';

// ---------------------------------------------------------------------------
// Environment detection
// ---------------------------------------------------------------------------

/**
 * True when the page is loaded from the local filesystem (Electron
 * packaged mode) or the desktop bridge advertises itself.
 */
export function isFileProtocol(): boolean {
  if (typeof window === 'undefined') return false;
  if (window.location.protocol === 'file:') return true;
  if (window.odiaDesktop?.isDesktop) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Route → file-URL resolution
// ---------------------------------------------------------------------------

/**
 * Resolve the frontend root URL regardless of which page is currently loaded.
 *
 * Problem: when the user navigates from /upload to /analysis, `window.location`
 * points to `.../frontend/upload/index.html`.  A naïve `href.replace(/[^/]*$/, '')`
 * gives `.../frontend/upload/` as the base, so the next URL resolves to
 * `.../frontend/upload/analysis/index.html` (wrong).
 *
 * Fix: strip any known first-level route segment so we always return the
 * `.../frontend/` root regardless of where we currently are.
 */
function getAppRootURL(): string {
  if (typeof window === 'undefined') return '/';

  const url = new URL(window.location.href);
  let pathname = url.pathname.replace(/[^/]*$/, ''); // strip filename

  // Strip one first-level route segment if present
  const routePattern = /\/(upload|ingest|analysis|documents|results|anomalies|synthesis|orchestrator|automation|settings)\/$/;
  const m = pathname.match(routePattern);
  if (m) {
    pathname = pathname.slice(0, -(m[1].length + 1));
  }

  return `${url.protocol}//${url.host}${pathname}`;
}

/**
 * Given a route path like `/upload`, return the absolute `file://` URL
 * to the corresponding `index.html` always relative to the app root —
 * not to the currently loaded page.
 *
 *   from any page:   /upload  →  file:///C:/.../frontend/upload/index.html
 *   from any page:   /        →  file:///C:/.../frontend/index.html
 */
export function routeToFileURL(path: string): string {
  if (typeof window === 'undefined') return path;

  const [pathname, ...rest] = path.split(/([?#])/);
  const tail = rest.join('');
  const rel = pathname.replace(/^\/+/, '');
  const root = getAppRootURL();

  if (!rel || rel === '/') {
    return root + 'index.html' + tail;
  }

  return root + rel.replace(/\/$/, '') + '/index.html' + tail;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export type NavigateFn = (path: string, opts?: { replace?: boolean }) => void;

/**
 * Returns a navigate function that does the right thing for the current
 * environment.  In Electron it calls `window.location.assign()` so the
 * browser hard-loads the target page.  In a browser it uses Next's
 * client-side router.
 */
export function useAppNavigate(): NavigateFn {
  const router = useRouter();

  return useCallback(
    (path: string, opts) => {
      if (isFileProtocol() && typeof window !== 'undefined') {
        const url = routeToFileURL(path);
        if (opts?.replace) {
          window.location.replace(url);
        } else {
          window.location.assign(url);
        }
        return;
      }
      if (opts?.replace) {
        router.replace(path);
      } else {
        router.push(path);
      }
    },
    [router],
  );
}

// ---------------------------------------------------------------------------
// <AppLink> — drop-in replacement for <Link> that also works under file://
// ---------------------------------------------------------------------------

type AppLinkProps = Omit<LinkProps, 'href'> & {
  href: string;
  children: React.ReactNode;
  className?: string;
  'aria-current'?: React.AriaAttributes['aria-current'];
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
};

export function AppLink({
  href,
  children,
  onClick,
  className,
  ...rest
}: AppLinkProps) {
  const nav = useAppNavigate();

  const handleClick: React.MouseEventHandler<HTMLAnchorElement> = (e) => {
    if (onClick) onClick(e);
    if (e.defaultPrevented) return;

    // Let the user modifier-click / middle-click to open in a new tab.
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) {
      return;
    }

    if (isFileProtocol()) {
      e.preventDefault();
      nav(href);
    }
    // For browser / Docker, fall through to Next's <Link> default behaviour.
  };

  return (
    <Link href={href} onClick={handleClick} className={className} {...rest}>
      {children}
    </Link>
  );
}
