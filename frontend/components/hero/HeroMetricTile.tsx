/**
 * HeroMetricTile — the canonical metric tile for hero-region readouts.
 *
 * v2.9.2 unification of three previously-divergent implementations:
 *   - Dashboard's SeverityTile (frontend/app/page.tsx) — gem-panel
 *     wrapper, severity-tone glow.
 *   - Anomalies' inline severity-filter buttons (frontend/app/anomalies/
 *     page.tsx) — hud-panel-inset wrapper, click-to-filter.
 *   - Orchestrator's OrchestratorMetric (frontend/app/orchestrator/
 *     page.tsx) — minimal hud-panel-inset, neutral.
 *
 * One component, ten tones, optional active state, optional onClick.
 * Used inside hero sections to render integrated metric grids that
 * respond to clicks (filter toggles) or display live state.
 *
 * Visual rhythm: colored dot + label row, large tone-colored value,
 * optional sublabel. Active state adds a 3-layer shadow ring + halo.
 * If onClick is provided, renders as a button with role/type set so the
 * tile is keyboard-accessible and safe inside form contexts.
 */

'use client';

import React from 'react';

export type HeroMetricTone =
  | 'critical' | 'high' | 'medium' | 'low' | 'info'
  | 'gold' | 'emerald' | 'signal' | 'flow' | 'neutral';

export interface HeroMetricTileProps {
  /** Small caps label above the value */
  label: string;
  /** The metric — number, formatted string, or React node */
  value: React.ReactNode;
  /** Optional sublabel — second line below value (e.g., "9.5%") */
  sublabel?: string;
  /** Tonal color — drives the dot, value color, active glow */
  tone?: HeroMetricTone;
  /** Active state — adds outer ring + inset edge + halo glow */
  active?: boolean;
  /** Click handler — if present, tile renders as button */
  onClick?: () => void;
  /** Optional icon glyph (lucide icon, custom SVG, or emoji) */
  icon?: React.ReactNode;
  /** Optional override classname for unusual layouts */
  className?: string;
}

const TONE_TO_VAR: Record<HeroMetricTone, string> = {
  critical: 'var(--severity-critical)',
  high:     'var(--severity-high)',
  medium:   'var(--severity-medium)',
  low:      'var(--severity-low)',
  info:     'var(--severity-info)',
  gold:     'var(--gold-300)',
  emerald:  'var(--emerald-400)',
  signal:   'var(--signal-400)',
  flow:     'var(--flow-400)',
  neutral:  'var(--smoke-200)',
};

export function HeroMetricTile({
  label,
  value,
  sublabel,
  tone = 'gold',
  active = false,
  onClick,
  icon,
  className = '',
}: HeroMetricTileProps) {
  const colorVar = TONE_TO_VAR[tone];

  // 3-layer shadow when active: outer halo + inset edge + offstrong.
  // Matches the Anomalies severity-filter visual at v2.9.1.
  const activeShadow =
    `0 0 0 1.5px ${colorVar}, ` +
    `inset 0 0 0 1px ${colorVar}, ` +
    `0 0 32px -8px ${colorVar}`;

  const baseClass = `hud-panel hud-panel-inset p-4 text-left transition-all ${
    onClick ? 'cursor-pointer hover:brightness-110' : ''
  } ${className}`.trim();

  const inner = (
    <>
      <div className="flex items-center gap-2 mb-2">
        <span
          aria-hidden
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{
            background: colorVar,
            boxShadow: `0 0 8px ${colorVar}`,
          }}
        />
        <span className="hud-metric-label">{label}</span>
        {icon && (
          <span
            className="ml-auto"
            style={{ color: colorVar }}
            aria-hidden
          >
            {icon}
          </span>
        )}
      </div>
      <div
        className="hud-metric tabular-nums"
        style={{ color: colorVar }}
      >
        {value}
      </div>
      {sublabel && (
        <div
          className="mt-1 text-xs tabular-nums"
          style={{ color: 'var(--smoke-400)' }}
        >
          {sublabel}
        </div>
      )}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={active}
        className={baseClass}
        style={{
          boxShadow: active ? activeShadow : undefined,
        }}
      >
        {inner}
      </button>
    );
  }

  return (
    <div
      className={baseClass}
      style={{
        boxShadow: active ? activeShadow : undefined,
      }}
    >
      {inner}
    </div>
  );
}
