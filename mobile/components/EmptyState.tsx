/**
 * EmptyState Component.
 *
 * Displayed when there are no documents or results to show.
 */

import React from 'react';
import { View, Text, StyleSheet, useColorScheme } from 'react-native';

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: string;
}

export function EmptyState({
  title,
  message,
  icon = '📄',
}: EmptyStateProps): React.ReactElement {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <View style={styles.container}>
      <Text style={styles.icon}>{icon}</Text>
      <Text
        style={[styles.title, { color: isDark ? '#f3f4f6' : '#1f2937' }]}
      >
        {title}
      </Text>
      <Text
        style={[styles.message, { color: isDark ? '#9ca3af' : '#6b7280' }]}
      >
        {message}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  icon: {
    fontSize: 48,
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
    textAlign: 'center',
  },
  message: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
});
