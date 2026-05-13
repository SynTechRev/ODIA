/**
 * Tests for OraculusMarkIcon (v3.0 O.D.I.A. monogram crosshair).
 *
 * The v3.0 mark replaces the v2.7.9 gold-swirl design with a geometric
 * O+D+I+A overlay: a gold outer circle (shared by O and D), a left
 * tangent stem (D), an inscribed equilateral triangle (A), a centre
 * vertical stem with double top crossbar (I), and four tinted facets
 * inside the triangle.  The geometry shape changed completely, so
 * these assertions count the new primitives:
 *
 *   - 5 polygons   = 4 facet fills + 1 triangle outline
 *   - 2 circles    = 1 outer O/D ring + 1 centre catch-light
 *   - 4 lines      = D stem, I stem, primary crossbar, echo crossbar
 *
 * The accessibility, sizing, and style-forwarding contracts are
 * unchanged from v2.7.9 and continue to be exercised below.
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
  it('renders the v3.0 monogram primitives', () => {
    const { container } = render(<OraculusMarkIcon aria-label="O.D.I.A. mark" />);
    expect(container.querySelectorAll('polygon')).toHaveLength(5);
    expect(container.querySelectorAll('circle')).toHaveLength(2);
    expect(container.querySelectorAll('line')).toHaveLength(4);
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
    expect(container.querySelectorAll('polygon')).toHaveLength(5);
    expect(container.querySelectorAll('circle')).toHaveLength(2);
    expect(container.querySelectorAll('line')).toHaveLength(4);
  });
});
