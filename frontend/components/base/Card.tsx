/**
 * Card — container for grouped content.
 *
 * Variants:
 *   default    — white surface, no border
 *   bordered   — white + hairline slate border (most common)
 *   elevated   — white + soft shadow (use for dialogs / spotlight content)
 *   muted      — slate-50 surface for de-emphasised groupings
 */

import React from 'react';

export interface CardProps {
  title?: string | React.ReactNode | null;
  subtitle?: string | React.ReactNode | null;
  icon?: React.ReactNode;
  children: React.ReactNode;
  actions?: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated' | 'muted';
  className?: string;
  /** Compact padding when true (p-4 instead of p-6). */
  dense?: boolean;
}

// v2.7 — HUD chrome. All variants render as JARVIS-style tactical panels:
// chamfered corners, hairline amber edge, subtle inner shadow for depth.
// `default` is bare (no panel chrome) for containers that stack inside
// another hud-panel. The body background is slate-950 in the dark-only
// theme, so text is inherited from :root --foreground.
const variantClasses: Record<NonNullable<CardProps['variant']>, string> = {
  default:  '',
  bordered: 'hud-panel',
  elevated: 'hud-panel hud-brackets',
  muted:    'hud-panel hud-panel-dense',
};

export function Card({
  title,
  subtitle,
  icon,
  children,
  actions,
  variant = 'default',
  className = '',
  dense = false,
}: CardProps) {
  const hasHeader = title || actions || icon;
  return (
    <article
      className={`
        ${dense ? 'p-4' : 'p-6'}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {hasHeader && (
        <div className="flex items-start justify-between mb-4 gap-3">
          <div className="flex items-start gap-3 min-w-0">
            {icon && (
              <div className="flex-shrink-0 w-9 h-9 bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/40 flex items-center justify-center mt-0.5">
                {icon}
              </div>
            )}
            <div className="min-w-0">
              {title && (
                <h3 className="text-sm font-semibold text-slate-100 leading-snug truncate uppercase tracking-wider">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-[11px] text-slate-500 mt-0.5 truncate hud-label">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {actions && (
            <div className="flex items-center gap-2 flex-shrink-0">
              {actions}
            </div>
          )}
        </div>
      )}
      <div className="text-slate-700 text-sm">{children}</div>
    </article>
  );
}
