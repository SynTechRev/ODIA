/**
 * Tests for HeroMetricTile (v2.9.2 canonical hero metric tile).
 *
 * Pin behaviour for:
 *   • all 10 tones resolve to a CSS variable on the value color
 *   • active state injects the 3-layer shadow ring
 *   • onClick renders as <button type="button"> with aria-pressed
 *   • absent onClick renders as <div>
 *   • sublabel renders only when supplied
 *   • icon slot renders inside the label row
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { HeroMetricTile, type HeroMetricTone } from '../hero/HeroMetricTile';

const ALL_TONES: HeroMetricTone[] = [
  'critical', 'high', 'medium', 'low', 'info',
  'gold', 'emerald', 'signal', 'flow', 'neutral',
];

const TONE_VAR: Record<HeroMetricTone, string> = {
  critical: 'var(--severity-critical)',
  high: 'var(--severity-high)',
  medium: 'var(--severity-medium)',
  low: 'var(--severity-low)',
  info: 'var(--severity-info)',
  gold: 'var(--gold-300)',
  emerald: 'var(--emerald-400)',
  signal: 'var(--signal-400)',
  flow: 'var(--flow-400)',
  neutral: 'var(--smoke-200)',
};

describe('HeroMetricTile', () => {
  it('renders label and value', () => {
    render(<HeroMetricTile label="Critical" value={42} />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it.each(ALL_TONES)('resolves tone "%s" to its CSS var on the value', (tone) => {
    const { container } = render(
      <HeroMetricTile label={tone} value={1} tone={tone} />,
    );
    const valueEl = container.querySelector('.hud-metric') as HTMLElement;
    expect(valueEl).not.toBeNull();
    expect(valueEl.style.color).toBe(TONE_VAR[tone]);
  });

  it('renders as <div> when onClick is absent', () => {
    const { container } = render(<HeroMetricTile label="Idle" value={0} />);
    // No <button> in the DOM — root is a div.
    expect(container.querySelector('button')).toBeNull();
    expect(container.firstElementChild?.tagName).toBe('DIV');
  });

  it('renders as <button type="button"> when onClick is provided', () => {
    const onClick = jest.fn();
    render(<HeroMetricTile label="Filter" value={5} onClick={onClick} />);
    const btn = screen.getByRole('button');
    expect(btn).toHaveAttribute('type', 'button');
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('reflects active state via aria-pressed and the 3-layer shadow', () => {
    render(
      <HeroMetricTile
        label="Critical"
        value={9}
        tone="critical"
        active
        onClick={() => {}}
      />,
    );
    const btn = screen.getByRole('button');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
    // Active shadow contains the 3-layer ring; spot-check the spread.
    expect(btn.style.boxShadow).toContain('1.5px');
    expect(btn.style.boxShadow).toContain('inset');
    expect(btn.style.boxShadow).toContain('32px');
  });

  it('omits the active shadow when inactive', () => {
    render(<HeroMetricTile label="Quiet" value={0} onClick={() => {}} />);
    const btn = screen.getByRole('button');
    expect(btn.style.boxShadow).toBe('');
  });

  it('renders sublabel only when supplied', () => {
    const { rerender } = render(<HeroMetricTile label="A" value={1} />);
    expect(screen.queryByText('9.5%')).toBeNull();
    rerender(<HeroMetricTile label="A" value={1} sublabel="9.5%" />);
    expect(screen.getByText('9.5%')).toBeInTheDocument();
  });

  it('renders icon in the label row when supplied', () => {
    render(
      <HeroMetricTile
        label="Flow"
        value={4}
        icon={<span data-testid="tile-icon">★</span>}
      />,
    );
    expect(screen.getByTestId('tile-icon')).toBeInTheDocument();
  });

  it('defaults tone to gold when omitted', () => {
    const { container } = render(<HeroMetricTile label="X" value={0} />);
    const valueEl = container.querySelector('.hud-metric') as HTMLElement;
    expect(valueEl.style.color).toBe('var(--gold-300)');
  });
});
