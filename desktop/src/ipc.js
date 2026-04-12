"use strict";

const { app, shell } = require("electron");
const fs = require("fs");
const path = require("path");
const http = require("http");
const log = require("electron-log");
const { checkBackendHealth, getBackendInfo, BACKEND_HOST, BACKEND_PORT } = require("./backend");

/**
 * Allowed file extensions for document import.
 * @type {Array<{name: string, extensions: string[]}>}
 */
const DOCUMENT_FILTERS = [
  { name: "All Supported Documents", extensions: ["pdf", "txt", "json", "xml"] },
  { name: "PDF Documents", extensions: ["pdf"] },
  { name: "Text Files", extensions: ["txt"] },
  { name: "JSON Files", extensions: ["json"] },
  { name: "XML Files", extensions: ["xml"] },
];

/**
 * Report export file filters.
 * @type {Array<{name: string, extensions: string[]}>}
 */
const REPORT_FILTERS = [
  { name: "Markdown Report", extensions: ["md"] },
  { name: "JSON Report", extensions: ["json"] },
  { name: "Text Report", extensions: ["txt"] },
];

/**
 * Maximum allowed file size for document import (50 MB).
 * @type {number}
 */
const MAX_FILE_SIZE = 50 * 1024 * 1024;

/**
 * Make an HTTP request to the backend API.
 * @param {string} method - HTTP method
 * @param {string} urlPath - URL path
 * @param {Object|null} body - Request body (JSON)
 * @returns {Promise<Object>} Response data
 */
function backendRequest(method, urlPath, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: BACKEND_HOST,
      port: BACKEND_PORT,
      path: urlPath,
      method,
      timeout: 60000,
      headers: {
        "Content-Type": "application/json",
      },
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          reject(new Error(`Invalid response from backend: ${data.substring(0, 200)}`));
        }
      });
    });

    req.on("error", (err) => reject(err));
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Backend request timed out"));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

/**
 * Register all IPC handlers for the main process.
 * Each handler is isolated and validates its inputs.
 *
 * @param {Electron.IpcMain} ipcMain - Electron IPC main module
 * @param {Electron.Dialog} dialog - Electron dialog module
 */
function registerIpcHandlers(ipcMain, dialog) {
  /**
   * Open native file dialog for document selection.
   * Returns an array of selected file paths, or empty array if cancelled.
   */
  ipcMain.handle("dialog:open-file", async (_event, options = {}) => {
    const result = await dialog.showOpenDialog({
      title: "Select Documents for Analysis",
      filters: DOCUMENT_FILTERS,
      properties: [
        "openFile",
        options.multiple ? "multiSelections" : undefined,
      ].filter(Boolean),
    });

    if (result.canceled || !result.filePaths.length) {
      return [];
    }

    // Validate file sizes
    const validPaths = [];
    for (const filePath of result.filePaths) {
      try {
        const stats = fs.statSync(filePath);
        if (stats.size > MAX_FILE_SIZE) {
          log.warn(`File too large (${stats.size} bytes): ${filePath}`);
          continue;
        }
        validPaths.push(filePath);
      } catch (err) {
        log.error(`Cannot access file: ${filePath}`, err);
      }
    }

    return validPaths;
  });

  /**
   * Open native save dialog for report export.
   * Returns the selected path, or null if cancelled.
   */
  ipcMain.handle("dialog:save-file", async (_event, options = {}) => {
    const result = await dialog.showSaveDialog({
      title: options.title || "Save Report",
      defaultPath: options.defaultPath || "odia-report.md",
      filters: REPORT_FILTERS,
    });

    if (result.canceled) {
      return null;
    }

    return result.filePath;
  });

  /**
   * Check backend health status.
   */
  ipcMain.handle("backend:health", async () => {
    try {
      const healthy = await checkBackendHealth();
      if (healthy) {
        const data = await backendRequest("GET", "/api/v1/health");
        return data;
      }
      return { status: "unavailable" };
    } catch (err) {
      log.error("Health check failed:", err);
      return { status: "error", message: err.message };
    }
  });

  /**
   * Submit document for analysis.
   * Reads the file from disk and sends text content to the backend.
   */
  ipcMain.handle("backend:analyze", async (_event, payload) => {
    if (!payload || (!payload.documentText && !payload.filePath)) {
      throw new Error("Either documentText or filePath is required");
    }

    let documentText = payload.documentText;

    // If a file path is provided, read the file
    if (payload.filePath && !documentText) {
      const filePath = payload.filePath;

      // Security: validate the path exists and is a file
      const resolvedPath = path.resolve(filePath);
      try {
        const stats = fs.statSync(resolvedPath);
        if (!stats.isFile()) {
          throw new Error("Path is not a file");
        }
        if (stats.size > MAX_FILE_SIZE) {
          throw new Error(`File exceeds maximum size of ${MAX_FILE_SIZE} bytes`);
        }
      } catch (err) {
        if (err.code === "ENOENT") {
          throw new Error("File not found");
        }
        throw err;
      }

      documentText = fs.readFileSync(resolvedPath, "utf-8");
    }

    try {
      const result = await backendRequest("POST", "/analyze", {
        document_text: documentText,
        metadata: payload.metadata || {},
      });
      return result;
    } catch (err) {
      log.error("Analysis request failed:", err);
      throw new Error(`Analysis failed: ${err.message}`);
    }
  });

  /**
   * Get backend connection status.
   */
  ipcMain.handle("backend:status", async () => {
    const info = getBackendInfo();
    const healthy = await checkBackendHealth();
    return {
      ...info,
      connected: healthy,
    };
  });

  /**
   * Get app version.
   */
  ipcMain.handle("app:version", async () => {
    return app.getVersion();
  });

  /**
   * Open URL in default browser (security: only http/https).
   */
  ipcMain.handle("shell:open-external", async (_event, url) => {
    if (typeof url !== "string") {
      throw new Error("URL must be a string");
    }
    if (!url.startsWith("https://") && !url.startsWith("http://")) {
      throw new Error("Only http and https URLs are allowed");
    }
    await shell.openExternal(url);
  });

  log.info("IPC handlers registered");
}

module.exports = {
  registerIpcHandlers,
  DOCUMENT_FILTERS,
  REPORT_FILTERS,
  MAX_FILE_SIZE,
  backendRequest,
};
