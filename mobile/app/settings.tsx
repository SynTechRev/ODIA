/**
 * Settings Screen.
 *
 * App configuration and information.
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  useColorScheme,
} from 'react-native';

export default function SettingsScreen(): React.ReactElement {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: isDark ? '#111827' : '#f9fafb' }]}
      contentContainerStyle={styles.content}
    >
      <View
        style={[
          styles.section,
          { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
        ]}
      >
        <Text style={[styles.sectionTitle, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
          About ODIA Mobile
        </Text>
        <Text style={[styles.text, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
          ODIA (Oraculus DI Auditor) is a legal document analysis platform that
          detects anomalies in government and legislative documents.
        </Text>
        <Text style={[styles.text, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
          All analysis runs completely on-device. No data is ever sent to
          external servers.
        </Text>
      </View>

      <View
        style={[
          styles.section,
          { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
        ]}
      >
        <Text style={[styles.sectionTitle, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
          Analysis Detectors
        </Text>
        {[
          'Fiscal Trail Analyzer',
          'Constitutional Conformity',
          'Surveillance Outsourcing',
          'Procurement Timeline',
          'Governance Gap',
          'Signature Chain',
          'Administrative Integrity',
          'Scope Expansion',
          'Cross-Reference Auditor',
        ].map((detector) => (
          <Text
            key={detector}
            style={[styles.listItem, { color: isDark ? '#d1d5db' : '#374151' }]}
          >
            • {detector}
          </Text>
        ))}
      </View>

      <View
        style={[
          styles.section,
          { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
        ]}
      >
        <Text style={[styles.sectionTitle, { color: isDark ? '#f3f4f6' : '#1f2937' }]}>
          Version
        </Text>
        <Text style={[styles.text, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
          1.0.0
        </Text>
        <Text style={[styles.text, { color: isDark ? '#9ca3af' : '#6b7280' }]}>
          License: MIT
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 8,
  },
  text: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 4,
  },
  listItem: {
    fontSize: 14,
    lineHeight: 24,
  },
});
