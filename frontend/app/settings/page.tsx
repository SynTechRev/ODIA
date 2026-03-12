/**
 * Settings Page - UI preferences and configuration
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { useUISettingsStore } from '@/lib/stores/ui-settings';

export default function SettingsPage() {
  const theme = useUISettingsStore((state) => state.theme);
  const setTheme = useUISettingsStore((state) => state.setTheme);
  const compactMode = useUISettingsStore((state) => state.compact_mode);
  const setCompactMode = useUISettingsStore((state) => state.setCompactMode);
  const showConfidenceScores = useUISettingsStore((state) => state.show_confidence_scores);
  const setShowConfidenceScores = useUISettingsStore((state) => state.setShowConfidenceScores);
  const highlightHighSeverity = useUISettingsStore((state) => state.highlight_high_severity);
  const setHighlightHighSeverity = useUISettingsStore((state) => state.setHighlightHighSeverity);
  const defaultView = useUISettingsStore((state) => state.default_view);
  const setDefaultView = useUISettingsStore((state) => state.setDefaultView);

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-6">
        {/* Appearance Settings */}
        <Card title="Appearance" variant="bordered">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Theme
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                Choose your preferred color theme
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="compact-mode"
                checked={compactMode}
                onChange={(e) => setCompactMode(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="compact-mode" className="ml-2 block text-sm text-gray-900">
                Compact Mode
              </label>
            </div>
            <p className="ml-6 text-sm text-gray-500">
              Reduce spacing and padding for a denser layout
            </p>
          </div>
        </Card>

        {/* Analysis Settings */}
        <Card title="Analysis Display" variant="bordered">
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="show-confidence"
                checked={showConfidenceScores}
                onChange={(e) => setShowConfidenceScores(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="show-confidence" className="ml-2 block text-sm text-gray-900">
                Show Confidence Scores
              </label>
            </div>
            <p className="ml-6 text-sm text-gray-500">
              Display confidence percentages for findings and anomalies
            </p>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="highlight-severity"
                checked={highlightHighSeverity}
                onChange={(e) => setHighlightHighSeverity(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="highlight-severity" className="ml-2 block text-sm text-gray-900">
                Highlight High Severity
              </label>
            </div>
            <p className="ml-6 text-sm text-gray-500">
              Use prominent colors for high and critical severity findings
            </p>
          </div>
        </Card>

        {/* View Preferences */}
        <Card title="Default View" variant="bordered">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default List View
              </label>
              <select
                value={defaultView}
                onChange={(e) => setDefaultView(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="list">List</option>
                <option value="grid">Grid</option>
                <option value="table">Table</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                Choose how documents and analyses are displayed by default
              </p>
            </div>
          </div>
        </Card>

        {/* System Information */}
        <Card title="System Information" variant="bordered">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Frontend Version:</span>
              <span className="font-mono text-gray-900">0.1.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Backend API:</span>
              <span className="font-mono text-gray-900">
                {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Framework:</span>
              <span className="font-mono text-gray-900">Next.js 16</span>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
