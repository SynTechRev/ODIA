/**
 * TextureResolver — sets CSS texture variables to the correct absolute
 * URLs for the current runtime environment.
 *
 * The bug this fixes
 * ------------------
 * `globals.css` defines texture variables as `url('/textures/foo.webp')`.
 * Under HTTP (web, PWA, dev server) those resolve correctly against the
 * origin. Under Electron's `file://` protocol they resolve against the
 * filesystem ROOT, which doesn't exist — and the textures silently
 * 404. The hero panels show their dimming-overlay gradient with no
 * marble underneath.
 *
 * This is the same bug class that hit the IntroFrame iframe in v2.7.10.
 * `publicAssetURL()` fixed it for JS-resolved URLs; this component fixes
 * it for CSS `url()` references by re-writing the variables at runtime.
 *
 * How it works
 * ------------
 * On mount, computes the correct absolute URL for each texture variant
 * via publicAssetURL() and writes it into document.documentElement.style
 * as a CSS variable. The :root values from globals.css are overridden
 * because element-level styles win over selector-level styles.
 *
 * Render-blocking
 * ---------------
 * The first paint after layout.tsx mounts already reads the original
 * leading-slash URLs. That paint will fail to load textures under
 * file://. A useLayoutEffect ensures the override is applied before the
 * BROWSER paints (vs useEffect which runs after). End result: zero
 * visible flicker.
 *
 * SSR safety
 * ----------
 * The hook short-circuits when `typeof window === 'undefined'`. Server
 * renders use the original :root values, which is correct because the
 * server does HTTP-style URL resolution.
 */

'use client';

import { useLayoutEffect } from 'react';
import { publicAssetURL } from '@/lib/navigation';

const TEXTURES = [
  '--texture-marble',
  '--texture-malachite',
  '--texture-malachite-flux',
  '--texture-gold-flux',
  '--texture-marble-hero',
  '--texture-malachite-hero',
  '--texture-malachite-flux-hero',
  '--texture-gold-flux-hero',
  '--texture-marble-tile',
  '--texture-malachite-tile',
  '--texture-gold-flux-tile',
] as const;

const NAME_TO_FILE: Record<string, string> = {
  '--texture-marble':              '/textures/texture-marble-bg.webp',
  '--texture-malachite':           '/textures/texture-malachite-bg.webp',
  '--texture-malachite-flux':      '/textures/texture-malachite-flux-bg.webp',
  '--texture-gold-flux':           '/textures/texture-gold-flux-bg.webp',
  '--texture-marble-hero':         '/textures/texture-marble-hero.webp',
  '--texture-malachite-hero':      '/textures/texture-malachite-hero.webp',
  '--texture-malachite-flux-hero': '/textures/texture-malachite-flux-hero.webp',
  '--texture-gold-flux-hero':      '/textures/texture-gold-flux-hero.webp',
  '--texture-marble-tile':         '/textures/texture-marble-tile.webp',
  '--texture-malachite-tile':      '/textures/texture-malachite-tile.webp',
  '--texture-gold-flux-tile':      '/textures/texture-gold-flux-tile.webp',
};

export function TextureResolver() {
  useLayoutEffect(() => {
    if (typeof window === 'undefined') return;

    const root = document.documentElement;
    for (const name of TEXTURES) {
      const path = NAME_TO_FILE[name];
      if (!path) continue;
      const resolved = publicAssetURL(path);
      // The CSS variable values are url() expressions, not bare paths.
      // Wrap the resolved string back into the url() form CSS expects.
      root.style.setProperty(name, `url('${resolved}')`);
    }

    // Mobile variants — only override if we're at a phone breakpoint;
    // desktop browsers don't load these so we don't waste resolution
    // bandwidth.
    if (window.innerWidth <= 768) {
      const mobilePaths: Record<string, string> = {
        '--texture-marble':         '/textures/texture-marble-mobile.webp',
        '--texture-malachite':      '/textures/texture-malachite-mobile.webp',
        '--texture-malachite-flux': '/textures/texture-malachite-flux-mobile.webp',
        '--texture-gold-flux':      '/textures/texture-gold-flux-mobile.webp',
      };
      for (const [name, path] of Object.entries(mobilePaths)) {
        root.style.setProperty(name, `url('${publicAssetURL(path)}')`);
      }
    }
  }, []);

  return null;
}
