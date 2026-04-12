"use strict";

const { contextBridge, ipcRenderer } = require("electron");

/**
 * Expose a safe, limited API to the renderer process via contextBridge.
 * This maintains context isolation while providing necessary functionality.
 *
 * Available channels are explicitly allowlisted to prevent arbitrary IPC calls.
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

contextBridge.exposeInMainWorld("odiaDesktop", {
  /**
   * Open a native file dialog to select documents for analysis.
   * @param {Object} options - Dialog options
   * @param {string[]} [options.filters] - File type filters
   * @param {boolean} [options.multiple] - Allow multiple file selection
   * @returns {Promise<string[]>} Selected file paths
   */
  openFileDialog: (options = {}) =>
    ipcRenderer.invoke("dialog:open-file", options),

  /**
   * Open a native save dialog for exporting reports.
   * @param {Object} options - Dialog options
   * @param {string} [options.defaultPath] - Default file name
   * @param {string} [options.title] - Dialog title
   * @returns {Promise<string|null>} Selected save path or null if cancelled
   */
  saveFileDialog: (options = {}) =>
    ipcRenderer.invoke("dialog:save-file", options),

  /**
   * Check backend health status.
   * @returns {Promise<{status: string, version: string}>}
   */
  checkHealth: () => ipcRenderer.invoke("backend:health"),

  /**
   * Submit a document for analysis via the backend.
   * @param {Object} payload - Analysis request
   * @param {string} payload.documentText - Document text content
   * @param {Object} [payload.metadata] - Optional metadata
   * @returns {Promise<Object>} Analysis results
   */
  analyzeDocument: (payload) => ipcRenderer.invoke("backend:analyze", payload),

  /**
   * Get the current backend connection status.
   * @returns {Promise<{connected: boolean, port: number}>}
   */
  getBackendStatus: () => ipcRenderer.invoke("backend:status"),

  /**
   * Get the application version.
   * @returns {Promise<string>}
   */
  getAppVersion: () => ipcRenderer.invoke("app:version"),

  /**
   * Open a URL in the default external browser.
   * @param {string} url - URL to open (must be http/https)
   * @returns {Promise<void>}
   */
  openExternal: (url) => ipcRenderer.invoke("shell:open-external", url),
});
