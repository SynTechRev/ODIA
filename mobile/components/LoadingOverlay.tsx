/**
 * LoadingOverlay Component.
 *
 * Full-screen loading overlay with activity indicator and message.
 */

import React from 'react';
import {
  View,
  Text,
  ActivityIndicator,
  StyleSheet,
  useColorScheme,
} from 'react-native';

interface LoadingOverlayProps {
  message?: string;
  visible: boolean;
}

export function LoadingOverlay({
  message = 'Analyzing...',
  visible,
}: LoadingOverlayProps): React.ReactElement | null {
  if (!visible) return null;

  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <View style={styles.overlay}>
      <View
        style={[
          styles.content,
          { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
        ]}
      >
        <ActivityIndicator
          size="large"
          color={isDark ? '#60a5fa' : '#3b82f6'}
        />
        <Text
          style={[styles.message, { color: isDark ? '#f3f4f6' : '#1f2937' }]}
        >
          {message}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  content: {
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  message: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '500',
  },
});
