/**
 * Shared utility functions for analysis modules.
 * 
 * Direct port of src/oraculus_di_auditor/analysis/text_utils.py
 */

import { NormalizedDocument } from './types';

/**
 * Extract all text content from document for analysis.
 * 
 * Mirrors Python: extract_text_content(doc)
 * Extracts from raw_text and sections[].content, joins with space.
 */
export function extractTextContent(doc: NormalizedDocument): string {
  const textParts: string[] = [];

  // Extract from raw_text field
  if ('raw_text' in doc && typeof doc.raw_text === 'string') {
    textParts.push(doc.raw_text);
  }

  // Extract from sections
  const sections = doc.sections;
  if (Array.isArray(sections)) {
    for (const section of sections) {
      if (
        section !== null &&
        typeof section === 'object' &&
        'content' in section
      ) {
        textParts.push(String(section.content));
      }
    }
  }

  return textParts.join(' ');
}
