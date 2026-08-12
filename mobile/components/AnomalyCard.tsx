/**
 * AnomalyCard Component.
 *
 * Displays a single anomaly finding with severity indicator,
 * description, and expandable details.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  useColorScheme,
} from 'react-native';
import { Anomaly } from '../lib/analysis/types';

interface AnomalyCardProps {
  anomaly: Anomaly;
}

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: '#fef2f2', text: '#991b1b', border: '#fecaca' },
  high: { bg: '#fff7ed', text: '#9a3412', border: '#fed7aa' },
  medium: { bg: '#fffbeb', text: '#92400e', border: '#fde68a' },
  low: { bg: '#f0fdf4', text: '#166534', border: '#bbf7d0' },
};

const SEVERITY_COLORS_DARK: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: '#450a0a', text: '#fca5a5', border: '#7f1d1d' },
  high: { bg: '#431407', text: '#fdba74', border: '#7c2d12' },
  medium: { bg: '#451a03', text: '#fcd34d', border: '#78350f' },
  low: { bg: '#052e16', text: '#86efac', border: '#14532d' },
};

export function AnomalyCard({ anomaly }: AnomalyCardProps): React.ReactElement {
  const [expanded, setExpanded] = useState(false);
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const colors = isDark
    ? SEVERITY_COLORS_DARK[anomaly.severity] || SEVERITY_COLORS_DARK.medium
    : SEVERITY_COLORS[anomaly.severity] || SEVERITY_COLORS.medium;

  return (
    <TouchableOpacity
      onPress={() => setExpanded(!expanded)}
      activeOpacity={0.7}
      accessibilityRole="button"
      accessibilityLabel={`${anomaly.severity} severity: ${anomaly.issue}`}
      accessibilityHint="Tap to expand details"
    >
      <View style={[styles.card, { backgroundColor: colors.bg, borderColor: colors.border }]}>
        <View style={styles.header}>
          <View style={[styles.severityBadge, { backgroundColor: colors.border }]}>
            <Text style={[styles.severityText, { color: colors.text }]}>
              {anomaly.severity.toUpperCase()}
            </Text>
          </View>
          <Text style={[styles.layer, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
            {anomaly.layer}
          </Text>
        </View>
        <Text style={[styles.issue, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
          {anomaly.issue}
        </Text>
        <Text style={[styles.id, { color: isDark ? '#6b7280' : '#9ca3af' }]}>
          {anomaly.id}
        </Text>
        {expanded && (
          <View style={[styles.details, { borderTopColor: colors.border }]}>
            <Text style={[styles.detailsTitle, { color: isDark ? '#d1d5db' : '#374151' }]}>
              Details
            </Text>
            <Text style={[styles.detailsContent, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
              {JSON.stringify(anomaly.details, null, 2)}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginVertical: 6,
    marginHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8,
  },
  severityText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  layer: {
    fontSize: 12,
    fontWeight: '500',
  },
  issue: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 4,
  },
  id: {
    fontSize: 12,
    fontFamily: 'monospace',
  },
  details: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
  },
  detailsTitle: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  detailsContent: {
    fontSize: 12,
    fontFamily: 'monospace',
    lineHeight: 18,
  },
});
