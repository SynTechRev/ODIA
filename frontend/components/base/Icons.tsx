/**
 * Inline SVG icon set.
 *
 * Self-contained so nothing in the UI depends on emoji fonts (which
 * render inconsistently on Windows under file://) or a remote icon CDN.
 *
 * Icons are 24×24 line icons drawn on a 0–24 viewBox with strokeWidth=2.
 * All use currentColor so they inherit the parent text colour.  Sizing
 * is controlled by the `size` prop (in pixels) — defaults to 20 for
 * sidebar use.  The `className` prop is merged for Tailwind overrides.
 *
 * To add a new icon:  export a function that returns <IconBase>...</IconBase>
 * and drop the SVG path fragments inside.
 */

import React from 'react';

export interface IconProps {
  size?: number;
  className?: string;
  strokeWidth?: number;
  'aria-hidden'?: boolean;
  'aria-label'?: string;
}

const IconBase: React.FC<IconProps & { children: React.ReactNode }> = ({
  size = 20,
  className = '',
  strokeWidth = 2,
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
    aria-hidden={ariaLabel ? undefined : ariaHidden}
    aria-label={ariaLabel}
    role={ariaLabel ? 'img' : undefined}
  >
    {children}
  </svg>
);

// ---------------------------------------------------------------------------
// Navigation icons
// ---------------------------------------------------------------------------

export const DashboardIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <rect x="3" y="3" width="7" height="9" rx="1" />
    <rect x="14" y="3" width="7" height="5" rx="1" />
    <rect x="14" y="12" width="7" height="9" rx="1" />
    <rect x="3" y="16" width="7" height="5" rx="1" />
  </IconBase>
);

export const UploadIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </IconBase>
);

export const ResultsIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <line x1="10" y1="9" x2="8" y2="9" />
  </IconBase>
);

export const IngestIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M12 3v12" />
    <path d="m7 10 5 5 5-5" />
    <rect x="3" y="17" width="18" height="4" rx="1" />
  </IconBase>
);

export const AnalysisIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
    <line x1="11" y1="8" x2="11" y2="14" />
    <line x1="8" y1="11" x2="14" y2="11" />
  </IconBase>
);

export const DocumentsIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
  </IconBase>
);

export const AnomaliesIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <circle cx="12" cy="17" r="0.5" fill="currentColor" />
  </IconBase>
);

export const SynthesisIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polygon points="12 2 2 7 12 12 22 7 12 2" />
    <polyline points="2 17 12 22 22 17" />
    <polyline points="2 12 12 17 22 12" />
  </IconBase>
);

export const OrchestratorIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <circle cx="5" cy="6" r="2" />
    <circle cx="19" cy="6" r="2" />
    <circle cx="5" cy="18" r="2" />
    <circle cx="19" cy="18" r="2" />
    <path d="M7 6h10" />
    <path d="M7 18h10" />
    <path d="M5 8v8" />
    <path d="M19 8v8" />
  </IconBase>
);

export const SettingsIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
    <circle cx="12" cy="12" r="3" />
  </IconBase>
);

// ---------------------------------------------------------------------------
// Status / action icons
// ---------------------------------------------------------------------------

export const CheckIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polyline points="20 6 9 17 4 12" />
  </IconBase>
);

export const CheckCircleIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </IconBase>
);

export const XIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </IconBase>
);

export const AlertCircleIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </IconBase>
);

export const RefreshIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polyline points="23 4 23 10 17 10" />
    <polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </IconBase>
);

export const CopyIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </IconBase>
);

export const ExternalLinkIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </IconBase>
);

export const ShieldIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </IconBase>
);

export const ChevronDownIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polyline points="6 9 12 15 18 9" />
  </IconBase>
);

export const ChevronLeftIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polyline points="15 18 9 12 15 6" />
  </IconBase>
);

export const ChevronRightIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <polyline points="9 18 15 12 9 6" />
  </IconBase>
);

export const MapPinIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
    <circle cx="12" cy="10" r="3" />
  </IconBase>
);

// ---------------------------------------------------------------------------
// O.D.I.A. logo mark — stylised "eye + shield" motif
// ---------------------------------------------------------------------------

export const OdiaMarkIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <circle cx="12" cy="11" r="2.5" fill="currentColor" />
  </IconBase>
);
