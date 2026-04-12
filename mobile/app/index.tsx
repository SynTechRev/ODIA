/**
 * Home Screen.
 *
 * Displays a list of analyzed documents and provides actions
 * to add new documents for analysis.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  useColorScheme,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { EmptyState } from '../components/EmptyState';
import { StoredDocument } from '../lib/analysis/types';

export default function HomeScreen(): React.ReactElement {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Refresh document list from storage
    try {
      const { listDocuments } = await import('../lib/storage');
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // Storage not available
    }
    setRefreshing(false);
  }, []);

  const renderDocument = ({ item }: { item: StoredDocument }) => (
    <TouchableOpacity
      style={[
        styles.documentCard,
        { backgroundColor: isDark ? '#1f2937' : '#ffffff' },
      ]}
      onPress={() =>
        router.push({ pathname: '/results', params: { documentId: item.id } })
      }
      accessibilityRole="button"
      accessibilityLabel={`Document: ${item.title}`}
    >
      <Text
        style={[styles.documentTitle, { color: isDark ? '#f3f4f6' : '#1f2937' }]}
      >
        {item.title}
      </Text>
      <Text
        style={[styles.documentDate, { color: isDark ? '#9ca3af' : '#6b7280' }]}
      >
        {new Date(item.createdAt).toLocaleDateString()}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: isDark ? '#111827' : '#f9fafb' }]}>
      {documents.length === 0 ? (
        <EmptyState
          title="No Documents"
          message="Tap the + button to add a document for analysis. All processing happens on-device."
          icon="📋"
        />
      ) : (
        <FlatList
          data={documents}
          renderItem={renderDocument}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/analyze')}
        accessibilityRole="button"
        accessibilityLabel="Add new document"
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  list: {
    padding: 16,
  },
  documentCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  documentTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  documentDate: {
    fontSize: 13,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 32,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  fabText: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '300',
    lineHeight: 30,
  },
});
