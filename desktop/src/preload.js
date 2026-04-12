"use strict";

const { contextBridge, ipcRenderer } = require("electron");

/**
 * Expose a safe, limited API to the renderer process via contextBridge.
 * This maintains context isolation while providing necessary functionality.
 *
 * VALID_CHANNELS is the exhaustive allowlist of IPC channels the renderer
 * may invoke. The safeInvoke wrapper enforces this at runtime so that
 * future refactors cannot accidentally expose arbitrary channels.
 */

const VALID_CHANNELS = [
  "dialog:open-file",
  "dialog:save-file",
  "backend:health",
  "backend:analyze",
  "backend:status",
  "app:version",
  "shell:open-external",
];

/**
 * Invoke an IPC channel after validating it against the allowlist.
 * @param {string} channel
 * @param {...any} args
 * @returns {Promise<any>}
 */
function safeInvoke(channel, ...args) {
  if (!VALID_CHANNELS.includes(channel)) {
    return Promise.reject(new Error(`IPC channel not allowed: ${channel}`));
  }
  return ipcRenderer.invoke(channel, ...args);
}

contextBridge.exposeInMainWorld("odiaDesktop", {
  /**
   * Open a native file dialog to select documents for analysis.
   * @param {Object} options - Dialog options
   * @param {Array<{name: string, extensions: string[]}>} [options.filters] - File type filters
   * @param {boolean} [options.multiple] - Allow multiple file selection
   * @returns {Promise<string[]>} Selected file paths
   */
  openFileDialog: (options = {}) =>
    safeInvoke("dialog:open-file", options),

  /**
   * Open a native save dialog for exporting reports.
   * @param {Object} options - Dialog options
   * @param {string} [options.defaultPath] - Default file name
   * @param {string} [options.title] - Dialog title
   * @returns {Promise<string|null>} Selected save path or null if cancelled
   */
  saveFileDialog: (options = {}) =>
    safeInvoke("dialog:save-file", options),

  /**
   * Check backend health status.
   * @returns {Promise<{status: string, version: string}>}
   */
  checkHealth: () => safeInvoke("backend:health"),

  /**
   * Submit a document for analysis via the backend.
   * Accepts either inline document text or a file path to analyze.
   * @param {Object} payload - Analysis request
   * @param {string} [payload.documentText] - Document text content
   * @param {string} [payload.filePath] - Path to a document file to analyze
   * @param {Object} [payload.metadata] - Optional metadata
   * @returns {Promise<Object>} Analysis results
   */
  analyzeDocument: (payload) => safeInvoke("backend:analyze", payload),

  /**
   * Get the current backend connection status.
   * @returns {Promise<{connected: boolean, port: number}>}
   */
  getBackendStatus: () => safeInvoke("backend:status"),

  /**
   * Get the application version.
   * @returns {Promise<string>}
   */
  getAppVersion: () => safeInvoke("app:version"),

  /**
   * Open a URL in the default external browser.
   * @param {string} url - URL to open (must be http/https)
   * @returns {Promise<void>}
   */
  openExternal: (url) => safeInvoke("shell:open-external", url),
});
