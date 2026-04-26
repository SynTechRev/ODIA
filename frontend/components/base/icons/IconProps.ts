/**
 * Shared IconProps interface for the inline SVG icon family.
 *
 * Extracted to its own file in v2.7.9 so per-icon component files
 * (e.g. OraculusMarkIcon.tsx) can import the type without pulling in
 * the entire Icons.tsx barrel. The original definition in Icons.tsx
 * now re-exports from here so existing call sites keep compiling.
 */

import type React from 'react';

export interface IconProps {
  size?: number;
  className?: string;
  strokeWidth?: number;
  /** v2.7.7 — inline style forwarded to the SVG (gem-palette tokens). */
  style?: React.CSSProperties;
  'aria-hidden'?: boolean;
  'aria-label'?: string;
}
