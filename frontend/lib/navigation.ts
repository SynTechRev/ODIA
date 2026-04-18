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
 * Given a route path like `/upload`, return the absolute `file://` URL
 * to the corresponding `index.html` relative to the current document.
 *
 *   current document:   file:///C:/.../frontend/index.html
 *   input:              '/upload'
 *   output:             'file:///C:/.../frontend/upload/index.html'
 *
 * The root path (`/`) resolves to the current directory's `index.html`.
 *
 * Uses the `URL` constructor so all path-segment normalisation (`..`,
 * `./`, query strings, hashes) is handled correctly on every platform.
 */
export function routeToFileURL(path: string): string {
  if (typeof window === 'undefined') return path;

  // Split off query/hash so we can preserve them across the rewrite.
  const [pathname, ...rest] = path.split(/([?#])/);
  const tail = rest.join('');

  // Strip leading slash — we want the route to be *relative* to the
  // app root (the directory containing the top-level index.html), not
  // relative to the filesystem root.
  const rel = pathname.replace(/^\/+/, '');

  // Home route
  if (rel === '' || rel === '/') {
    // Use the directory of the current file as the base.
    const base = window.location.href.replace(/[^/]*$/, '');
    return base + 'index.html' + tail;
  }

  // Any other route: /upload  →  ./upload/index.html
  const base = window.location.href.replace(/[^/]*$/, '');
  // Build the target using the URL constructor for correctness.
  const target = new URL(rel.replace(/\/$/, '') + '/index.html', base);
  return target.href + tail;
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
