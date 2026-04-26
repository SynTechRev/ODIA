/**
 * Tests for OraculusMarkIcon (v2.7.9 Track A1).
 *
 * Verifies that:
 *   - The new mark renders the four expected geometry groups (primary
 *     swirl, mid wisp, outer wisp, splatter dots).
 *   - The deprecated aliases (OctopusMarkIcon, StrategyMarkIcon,
 *     OdiaMarkIcon) re-exported from Icons.tsx all render the same
 *     SVG geometry — so existing call sites keep compiling and now
 *     paint the new mark.
 *   - The icon respects the standard IconProps (size, className,
 *     style, aria-label).
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { OraculusMarkIcon } from '../icons/OraculusMarkIcon';
import {
  OctopusMarkIcon,
  StrategyMarkIcon,
  OdiaMarkIcon,
} from '../Icons';

describe('OraculusMarkIcon', () => {
  it('renders the four expected geometry groups', () => {
    const { container } = render(<OraculusMarkIcon aria-label="O.D.I.A. mark" />);
    // Three stroked paths (primary swirl, mid wisp, outer wisp) plus
    // four filled circles (splatter dots).
    expect(container.querySelectorAll('path')).toHaveLength(3);
    expect(container.querySelectorAll('circle')).toHaveLength(4);
  });

  it('renders an svg with the standard 24x24 viewBox', () => {
    const { container } = render(<OraculusMarkIcon aria-label="mark" />);
    const svg = container.querySelector('svg');
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute('viewBox')).toBe('0 0 24 24');
  });

  it('forwards the size prop to the svg width and height', () => {
    const { container } = render(
      <OraculusMarkIcon size={32} aria-label="mark" />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('32');
    expect(svg?.getAttribute('height')).toBe('32');
  });

  it('forwards inline style for gem-palette tokens', () => {
    const { container } = render(
      <OraculusMarkIcon
        aria-label="mark"
        style={{ color: 'var(--gold-300)' }}
      />,
    );
    const svg = container.querySelector('svg') as SVGElement;
    expect(svg.style.color).toBe('var(--gold-300)');
  });

  it('exposes an accessible name when aria-label is supplied', () => {
    render(<OraculusMarkIcon aria-label="O.D.I.A. mark" />);
    expect(screen.getByLabelText('O.D.I.A. mark')).toBeInTheDocument();
  });
});

describe('OraculusMarkIcon — deprecated aliases', () => {
  it.each([
    ['OctopusMarkIcon', OctopusMarkIcon],
    ['StrategyMarkIcon', StrategyMarkIcon],
    ['OdiaMarkIcon', OdiaMarkIcon],
  ])('%s renders the same geometry as OraculusMarkIcon', (_name, Alias) => {
    const { container } = render(<Alias aria-label="alias" />);
    expect(container.querySelectorAll('path')).toHaveLength(3);
    expect(container.querySelectorAll('circle')).toHaveLength(4);
  });
});
