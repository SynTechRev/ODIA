/**
 * Card Component - Container component for content grouping
 */

import React from 'react';

export interface CardProps {
  title?: string | null;
  children: React.ReactNode;
  actions?: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
  className?: string;
}

const variantClasses = {
  default: 'bg-white',
  bordered: 'bg-white border border-gray-200',
  elevated: 'bg-white shadow-lg',
};

export function Card({
  title,
  children,
  actions,
  variant = 'default',
  className = '',
}: CardProps) {
  return (
    <article
      className={`
        rounded-lg p-6
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="text-gray-700">{children}</div>
    </article>
  );
}
