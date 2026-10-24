/**
 * Results Screen.
 *
 * Displays analysis results for a specific document with
 * anomaly cards, scores, and summary.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  useColorScheme,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { AnomalyCard } from '../components/AnomalyCard';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { EmptyState } from '../components/EmptyState';
import { getAnalysisResult } from '../lib/storage';
import { StoredAnalysisResult } from '../lib/analysis/types';

export default function ResultsScreen(): React.ReactElement {
  const { documentId } = useLocalSearchParams<{ documentId: string }>();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const [result, setResult] = useState<StoredAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadResult() {
      if (documentId) {
        const stored = await getAnalysisResult(documentId);
        setResult(stored);
      }
      setLoading(false);
    }
    loadResult();
  }, [documentId]);

  if (loading) {
    return <LoadingOverlay visible={true} message="Loading results..." />;
  }

  if (!result) {
    return (
      <EmptyState
        title="No Results"
        message="Analysis results were not found for this document."
        icon="🔍"
      />
    );
  }

  const { findings, severity_score, lattice_score, summary, flags } =
    result.result;
  const allAnomalies = [
    ...findings.fiscal,
    ...findings.constitutional,
    ...findings.surveillance,
  ];

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: isDark ? '#111827' : '#f9fafb' }]}
      contentContainerStyle={styles.content}
    >
      {/* Summary Card */}
      <View
        style={[
          styles.summaryCard,
          { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
        ]}
      >
        <Text style={[styles.summaryText, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
          {summary}
        </Text>

        <View style={styles.scoreRow}>
          <View style={styles.scoreItem}>
            <Text style={[styles.scoreLabel, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
              Severity
            </Text>
            <Text
              style={[
                styles.scoreValue,
                {
                  color:
                    severity_score > 0.6
                      ? '#ef4444'
                      : severity_score > 0.3
                      ? '#f59e0b'
                      : '#22c55e',
                },
              ]}
            >
              {severity_score.toFixed(2)}
            </Text>
          </View>
          <View style={styles.scoreItem}>
            <Text style={[styles.scoreLabel, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
              Confidence
            </Text>
            <Text
              style={[
                styles.scoreValue,
                {
                  color:
                    lattice_score > 0.8
                      ? '#22c55e'
                      : lattice_score > 0.5
                      ? '#f59e0b'
                      : '#ef4444',
                },
              ]}
            >
              {lattice_score.toFixed(2)}
            </Text>
          </View>
          <View style={styles.scoreItem}>
            <Text style={[styles.scoreLabel, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
              Findings
            </Text>
            <Text style={[styles.scoreValue, { color: isDark ? '#60a5fa' : '#3b82f6' }]}>
              {allAnomalies.length}
            </Text>
          </View>
        </View>
      </View>

      {/* Flags */}
      {flags.length > 0 && (
        <View style={styles.flagsSection}>
          <Text style={[styles.sectionTitle, { color: isDark ? '#fca5a5' : '#dc2626' }]}>
            ⚠️ High-Priority Flags
          </Text>
          {flags.map((flag, idx) => (
            <Text
              key={idx}
              style={[styles.flagText, { color: isDark ? '#fca5a5' : '#991b1b' }]}
            >
              • {flag}
            </Text>
          ))}
        </View>
      )}

      {/* Anomalies */}
      {allAnomalies.length > 0 ? (
        <View style={styles.anomaliesSection}>
          <Text style={[styles.sectionTitle, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
            Findings ({allAnomalies.length})
          </Text>
          {allAnomalies.map((anomaly, idx) => (
            <AnomalyCard key={`${anomaly.id}-${idx}`} anomaly={anomaly} />
          ))}
        </View>
      ) : (
        <EmptyState
          title="No Anomalies"
          message="No anomalies were detected in this document."
          icon="✅"
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    paddingBottom: 32,
  },
  summaryCard: {
    margin: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  summaryText: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 16,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  scoreItem: {
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  flagsSection: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  flagText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 4,
  },
  anomaliesSection: {
    marginBottom: 16,
  },
});
