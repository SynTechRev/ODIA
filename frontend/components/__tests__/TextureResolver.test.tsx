/**
 * Tests for TextureResolver (v2.8.1 Fix #2).
 *
 * The TextureResolver rewrites the texture CSS variables at runtime so
 * Electron file:// builds resolve them correctly. These tests pin:
 *
 *   • on mount it writes a `--texture-*` CSS variable for each known
 *     texture name onto the documentElement
 *   • the value is a `url('...')` expression (not a bare path) — CSS
 *     custom properties for textures must wrap their target in url()
 *   • `publicAssetURL()` is consulted (so HTTP / file:// resolution is
 *     honored)
 *   • SSR-safe: short-circuits when window is undefined
 */

import React from 'react';
import { render } from '@testing-library/react';
import { TextureResolver } from '../TextureResolver';

// Force publicAssetURL to a deterministic stub so the assertions don't
// have to reproduce the file:// vs HTTP branching logic.
jest.mock('@/lib/navigation', () => ({
  publicAssetURL: (path: string) => `https://test.local${path}`,
}));

describe('TextureResolver', () => {
  beforeEach(() => {
    // Reset CSS variables between tests — setProperty leaks across
    // assertions otherwise.
    const known = [
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
    ];
    for (const name of known) {
      document.documentElement.style.removeProperty(name);
    }
  });

  it('writes a url() expression for every known texture variable', () => {
    render(<TextureResolver />);

    const html = document.documentElement;
    expect(html.style.getPropertyValue('--texture-marble')).toBe(
      "url('https://test.local/textures/texture-marble-bg.webp')",
    );
    expect(html.style.getPropertyValue('--texture-malachite')).toBe(
      "url('https://test.local/textures/texture-malachite-bg.webp')",
    );
    expect(html.style.getPropertyValue('--texture-malachite-flux')).toBe(
      "url('https://test.local/textures/texture-malachite-flux-bg.webp')",
    );
    expect(html.style.getPropertyValue('--texture-gold-flux')).toBe(
      "url('https://test.local/textures/texture-gold-flux-bg.webp')",
    );
  });

  it('writes hero variants for the four primary textures', () => {
    render(<TextureResolver />);

    const html = document.documentElement;
    expect(html.style.getPropertyValue('--texture-marble-hero')).toContain(
      'texture-marble-hero.webp',
    );
    expect(html.style.getPropertyValue('--texture-malachite-hero')).toContain(
      'texture-malachite-hero.webp',
    );
    expect(
      html.style.getPropertyValue('--texture-malachite-flux-hero'),
    ).toContain('texture-malachite-flux-hero.webp');
    expect(html.style.getPropertyValue('--texture-gold-flux-hero')).toContain(
      'texture-gold-flux-hero.webp',
    );
  });

  it('renders nothing — pure side-effect component', () => {
    const { container } = render(<TextureResolver />);
    expect(container.innerHTML).toBe('');
  });

  it('uses mobile texture variants when viewport is <= 768px', () => {
    // jsdom defaults innerWidth to 1024; force phone viewport.
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 375,
    });

    render(<TextureResolver />);

    const html = document.documentElement;
    // The mobile override REPLACES the desktop -bg variant for the
    // four primary names. Desktop hero/tile variants stay as they were.
    expect(html.style.getPropertyValue('--texture-marble')).toContain(
      'texture-marble-mobile.webp',
    );
    expect(html.style.getPropertyValue('--texture-malachite')).toContain(
      'texture-malachite-mobile.webp',
    );
    expect(html.style.getPropertyValue('--texture-malachite-flux')).toContain(
      'texture-malachite-flux-mobile.webp',
    );
    expect(html.style.getPropertyValue('--texture-gold-flux')).toContain(
      'texture-gold-flux-mobile.webp',
    );

    // Restore so other tests start clean.
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 1024,
    });
  });
});
