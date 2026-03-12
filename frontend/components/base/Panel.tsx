/**
 * Panel Component - Generic panel container
 */

import React from 'react';

export interface PanelProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingClasses = {
  none: 'p-0',
  sm: 'p-2',
  md: 'p-4',
  lg: 'p-6',
};

export function Panel({ children, className = '', padding = 'md' }: PanelProps) {
  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200
        ${paddingClasses[padding]}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
