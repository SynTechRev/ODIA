/**
 * IconBase — shared SVG wrapper for the inline icon family.
 *
 * Extracted from Icons.tsx in v2.7.9 so per-icon component files
 * (OraculusMarkIcon.tsx, future icons in this directory) can compose
 * against IconBase without importing the entire icon barrel.
 *
 * 24×24 viewBox, currentColor stroke, no fill. Stroke width and
 * accessibility props flow through IconProps. The `style` prop is
 * forwarded to the <svg> element so per-call gem-palette CSS variables
 * (e.g. `style={{ color: 'var(--gold-300)' }}`) work.
 */

import React from 'react';
import type { IconProps } from './IconProps';

export const IconBase: React.FC<IconProps & { children: React.ReactNode }> = ({
  size = 20,
  className = '',
  strokeWidth = 2,
  style,
  'aria-hidden': ariaHidden = true,
  'aria-label': ariaLabel,
  children,
}) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={style}
    aria-hidden={ariaLabel ? undefined : ariaHidden}
    aria-label={ariaLabel}
    role={ariaLabel ? 'img' : undefined}
  >
    {children}
  </svg>
);
