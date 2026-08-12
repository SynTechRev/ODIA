/**
 * Analyze Screen.
 *
 * Allows users to input document text (via paste or camera capture)
 * and run on-device analysis.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  useColorScheme,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { runFullAnalysis } from '../lib/analysis/pipeline';
import { saveDocument, saveAnalysisResult } from '../lib/storage';

export default function AnalyzeScreen(): React.ReactElement {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const [title, setTitle] = useState('');
  const [documentText, setDocumentText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = useCallback(async () => {
    if (!documentText.trim()) {
      Alert.alert('Empty Document', 'Please enter or paste document text to analyze.');
      return;
    }

    setAnalyzing(true);

    try {
      const docTitle = title.trim() || 'Untitled Document';
      const metadata: Record<string, unknown> = { title: docTitle };

      // Run analysis (on-device, no network needed)
      const result = runFullAnalysis(documentText, metadata);

      // Save document and result
      const savedDoc = await saveDocument(docTitle, documentText, metadata);
      await saveAnalysisResult(savedDoc.id, result);

      // Navigate to results
      router.replace({
        pathname: '/results',
        params: { documentId: savedDoc.id },
      });
    } catch (error) {
      Alert.alert(
        'Analysis Error',
        'An error occurred during analysis. Please try again.'
      );
    } finally {
      setAnalyzing(false);
    }
  }, [title, documentText, router]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={[styles.scroll, { backgroundColor: isDark ? '#111827' : '#f9fafb' }]}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={[styles.label, { color: isDark ? '#d1d5db' : '#374151' }]}>
          Document Title
        </Text>
        <TextInput
          style={[
            styles.titleInput,
            {
              backgroundColor: isDark ? '#1f2937' : '#ffffff',
              color: isDark ? '#f3f4f6' : '#1f2937',
              borderColor: isDark ? '#374151' : '#e5e7eb',
            },
          ]}
          value={title}
          onChangeText={setTitle}
          placeholder="Enter document title..."
          placeholderTextColor={isDark ? '#6b7280' : '#9ca3af'}
          accessibilityLabel="Document title"
        />

        <Text style={[styles.label, { color: isDark ? '#d1d5db' : '#374151' }]}>
          Document Text
        </Text>
        <TextInput
          style={[
            styles.textInput,
            {
              backgroundColor: isDark ? '#1f2937' : '#ffffff',
              color: isDark ? '#f3f4f6' : '#1f2937',
              borderColor: isDark ? '#374151' : '#e5e7eb',
            },
          ]}
          value={documentText}
          onChangeText={setDocumentText}
          placeholder="Paste or type document text here..."
          placeholderTextColor={isDark ? '#6b7280' : '#9ca3af'}
          multiline
          textAlignVertical="top"
          accessibilityLabel="Document text"
        />

        <TouchableOpacity
          style={[
            styles.analyzeButton,
            !documentText.trim() && styles.analyzeButtonDisabled,
          ]}
          onPress={handleAnalyze}
          disabled={!documentText.trim() || analyzing}
          accessibilityRole="button"
          accessibilityLabel="Analyze document"
        >
          <Text style={styles.analyzeButtonText}>
            🔍 Analyze Document
          </Text>
        </TouchableOpacity>

        <Text style={[styles.hint, { color: isDark ? '#6b7280' : '#9ca3af' }]}>
          All analysis runs on-device. No data is sent to any server.
        </Text>
      </ScrollView>

      <LoadingOverlay visible={analyzing} message="Analyzing document..." />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 12,
  },
  titleInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    minHeight: 200,
    lineHeight: 20,
  },
  analyzeButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  analyzeButtonDisabled: {
    opacity: 0.5,
  },
  analyzeButtonText: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: '600',
  },
  hint: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 16,
  },
});
