/**
 * SeverityChart - Pie chart showing anomaly distribution by severity.
 *
 * Uses recharts PieChart. Falls back gracefully to a text summary if
 * there are no anomalies or all counts are zero.
 */

'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface SeverityCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface SeverityChartProps {
  bySeverity: SeverityCount;
  /** Optional total — computed from bySeverity if omitted */
  total?: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#dc2626', // red-600
  high: '#ea580c',     // orange-600
  medium: '#ca8a04',   // yellow-600
  low: '#9ca3af',      // gray-400
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

export function SeverityChart({ bySeverity, total }: SeverityChartProps) {
  const data = Object.entries(bySeverity)
    .filter(([, count]) => count > 0)
    .map(([severity, count]) => ({
      name: SEVERITY_LABELS[severity] ?? severity,
      value: count,
      severity,
    }));

  const computedTotal =
    total ?? Object.values(bySeverity).reduce((s, n) => s + n, 0);

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-gray-400">
        <div className="text-4xl mb-2">✓</div>
        <div className="text-sm">No anomalies detected</div>
      </div>
    );
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry) => (
              <Cell
                key={entry.severity}
                fill={SEVERITY_COLORS[entry.severity] ?? '#9ca3af'}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value} anomal${value === 1 ? 'y' : 'ies'}`,
              name,
            ]}
          />
          <Legend
            formatter={(value) => (
              <span className="text-sm text-gray-700">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Center label */}
      <div className="text-center -mt-2">
        <span className="text-2xl font-bold text-gray-900">{computedTotal}</span>
        <span className="ml-1 text-sm text-gray-500">total</span>
      </div>
    </div>
  );
}
