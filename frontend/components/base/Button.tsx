/**
 * Button — base reusable button with variants.
 *
 * v2.7.7 Y2 — `accent` is now the gemstone primary CTA: emerald gradient
 * body with gold inner highlight ring + crystallized facet clip-path.
 * `outline` and `ghost` carry gold-edge dual-stroke on hover so secondary
 * actions still read as part of the gem palette.
 *
 * Variants:
 *   primary    — blue (default; kept for existing snapshot tests)
 *   accent     — gem CTA: emerald + gold dual-edge (top-level CTAs)
 *   secondary  — smoke fill, gold-outline
 *   danger     — rose (destructive)
 *   outline    — transparent + gold-edge hairline
 *   ghost      — transparent, emerald-glow on hover
 *
 * v2.9.0 B2 — Touch-target policy
 * -------------------------------
 * Interactive buttons MUST be at least 44px tall on mobile (iOS HIG;
 * Material Design wants 48dp). The size scale enforces this:
 *
 *   xs → min-h-[32px]   decorative use only (status pills, chips,
 *                        non-tappable role="button")
 *   sm → min-h-[40px]   desktop-only secondary actions; do NOT use on
 *                        surfaces that render below the md: breakpoint
 *   md → min-h-[44px]   mobile-safe default. Use this everywhere unless
 *                        you have a specific reason not to.
 *   lg → min-h-[52px]   primary CTA on mobile hero panels (pull-quote
 *                        hero, splash, evidence-cover overlay)
 *
 * Non-Button interactive elements (raw <button>, <a> with onClick, etc.)
 * should also hit min-h-[44px] when they appear on mobile-rendered
 * surfaces. The mobile bottom-tab bar in DashboardLayout, the upload
 * Remove buttons (B1), and the install prompt (B5) each manage their
 * own touch target via the matching min-h class.
 */

import React from 'react';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'primary'
    | 'accent'
    | 'secondary'
    | 'danger'
    | 'outline'
    | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  children: React.ReactNode;
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 focus:ring-blue-500 shadow-sm',
  // v2.7.7 — gem CTA: emerald body + gold inner ring + neon-emerald glow.
  // Composed as plain Tailwind utilities pointing at the gemstone tokens
  // so the bg/inset shadows compose with caller-supplied className overrides.
  accent: [
    'text-[#03240e] font-semibold tracking-[0.02em]',
    'bg-[linear-gradient(135deg,var(--neon-emerald)_0%,var(--emerald-500)_60%,var(--emerald-700)_100%)]',
    'shadow-[inset_0_1px_0_rgba(245,220,154,0.55),inset_0_0_0_1px_rgba(216,177,60,0.40),0_0_24px_-6px_var(--neon-emerald)]',
    'hover:shadow-[inset_0_1px_0_rgba(245,220,154,0.75),inset_0_0_0_1px_rgba(245,220,154,0.55),0_0_36px_-4px_var(--neon-emerald)]',
    'focus:ring-2 focus:ring-[var(--gold-300)] focus:ring-offset-0',
  ].join(' '),
  secondary: [
    'text-[var(--smoke-100)] bg-[rgba(14,14,20,0.85)]',
    'border border-[var(--gem-edge-gold)]',
    'shadow-[inset_0_1px_0_rgba(245,220,154,0.10)]',
    'hover:text-[var(--neon-emerald)] hover:border-[var(--gem-edge-gold-bright)]',
    'hover:shadow-[inset_0_1px_0_rgba(245,220,154,0.20),0_0_18px_-6px_var(--neon-emerald)]',
    'focus:ring-2 focus:ring-[var(--gold-300)] focus:ring-offset-0',
  ].join(' '),
  danger:
    'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 focus:ring-rose-500 shadow-sm',
  outline: [
    'bg-transparent text-[var(--smoke-100)]',
    'border border-[var(--gem-edge-gold)]',
    'hover:text-[var(--neon-emerald)] hover:border-[var(--gem-edge-gold-bright)]',
    'hover:shadow-[0_0_18px_-6px_var(--neon-emerald)]',
    'focus:ring-2 focus:ring-[var(--gold-300)] focus:ring-offset-0',
  ].join(' '),
  ghost: [
    'bg-transparent text-[var(--smoke-200)]',
    'hover:text-[var(--neon-emerald)] hover:bg-[rgba(31,232,143,0.08)]',
    'focus:ring-2 focus:ring-[var(--emerald-400)] focus:ring-offset-0',
  ].join(' '),
};

const sizeClasses: Record<NonNullable<ButtonProps['size']>, string> = {
  // v2.9.0 B2 — explicit min-heights enforce mobile touch-target rules
  // (iOS HIG: 44pt; Material Design: 48dp). xs is decorative-only.
  xs: 'min-h-[32px] px-2.5 py-1 text-xs gap-1',
  sm: 'min-h-[40px] px-3 py-1.5 text-sm gap-1.5',
  md: 'min-h-[44px] px-4 py-2 text-sm gap-2',
  lg: 'min-h-[52px] px-6 py-3 text-base gap-2.5',
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  icon,
  iconPosition = 'left',
  children,
  className = '',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      className={`
        inline-flex items-center justify-center
        font-medium rounded-md
        focus:outline-none focus:ring-2 focus:ring-offset-2
        transition-colors duration-150
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      disabled={isDisabled}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        icon && iconPosition === 'left' && <span className="flex-shrink-0">{icon}</span>
      )}
      {children}
      {!loading && icon && iconPosition === 'right' && (
        <span className="flex-shrink-0">{icon}</span>
      )}
    </button>
  );
}
