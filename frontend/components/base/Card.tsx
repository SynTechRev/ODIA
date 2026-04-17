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

const variantClasses: Record<NonNullable<CardProps['variant']>, string> = {
  default:  'bg-white',
  bordered: 'bg-white border border-slate-200',
  elevated: 'bg-white shadow-lg shadow-slate-900/5 ring-1 ring-slate-900/5',
  muted:    'bg-slate-50 border border-slate-200',
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
        rounded-xl ${dense ? 'p-4' : 'p-6'}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {hasHeader && (
        <div className="flex items-start justify-between mb-4 gap-3">
          <div className="flex items-start gap-3 min-w-0">
            {icon && (
              <div className="flex-shrink-0 w-9 h-9 rounded-md bg-slate-100 text-slate-600 flex items-center justify-center mt-0.5">
                {icon}
              </div>
            )}
            <div className="min-w-0">
              {title && (
                <h3 className="text-base font-semibold text-slate-900 leading-snug truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-slate-500 mt-0.5 truncate">
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
