/**
 * Root Layout.
 *
 * Configures navigation and global providers for the app.
 */

import React from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';

export default function RootLayout(): React.ReactElement {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  return (
    <>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: isDark ? '#1a1a2e' : '#ffffff',
          },
          headerTintColor: isDark ? '#f3f4f6' : '#1f2937',
          headerTitleStyle: {
            fontWeight: '700',
          },
          contentStyle: {
            backgroundColor: isDark ? '#111827' : '#f9fafb',
          },
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            title: 'ODIA',
            headerLargeTitle: true,
          }}
        />
        <Stack.Screen
          name="analyze"
          options={{
            title: 'Analyze Document',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="results"
          options={{
            title: 'Analysis Results',
          }}
        />
        <Stack.Screen
          name="settings"
          options={{
            title: 'Settings',
          }}
        />
      </Stack>
    </>
  );
}
