"use strict";

const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const path = require("path");
const log = require("electron-log");

const { startBackend, stopBackend, waitForBackend } = require("./backend");
const { registerIpcHandlers } = require("./ipc");

// Configure logging
log.transports.file.level = "info";
log.transports.console.level = "debug";

/** @type {BrowserWindow | null} */
let mainWindow = null;

/** @type {boolean} */
let isQuitting = false;

/**
 * Resolve the path to the frontend static files.
 * In development, serves from the Next.js export directory.
 * In production, serves from the bundled resources.
 * @returns {string} Absolute path to frontend directory
 */
function getFrontendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "frontend");
  }
  // Development: use Next.js export output
  return path.join(__dirname, "..", "..", "frontend", "out");
}

/**
 * Create the main application window with security best practices.
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: "ODIA — Document Analysis",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
    show: false,
  });

  // Show window when ready to avoid visual flash
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  // Open external links in the default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  // Load frontend
  const frontendPath = getFrontendPath();
  const indexPath = path.join(frontendPath, "index.html");
  log.info(`Loading frontend from: ${indexPath}`);
  mainWindow.loadFile(indexPath).catch((err) => {
    log.error("Failed to load frontend:", err);
    // Show error page if frontend fails to load
    mainWindow.loadURL(
      `data:text/html,<html><body style="font-family:sans-serif;padding:40px;">
        <h1>ODIA</h1>
        <p>Frontend failed to load. Please check the installation.</p>
        <pre>${err.message}</pre>
      </body></html>`
    );
  });
}

/**
 * Application startup sequence:
 * 1. Start Python backend
 * 2. Wait for backend health check
 * 3. Create main window
 * 4. Register IPC handlers
 */
async function onReady() {
  log.info("ODIA Desktop starting...");
  log.info(`App version: ${app.getVersion()}`);
  log.info(`Electron: ${process.versions.electron}`);
  log.info(`Platform: ${process.platform} ${process.arch}`);

  try {
    // Start backend
    log.info("Starting Python backend...");
    startBackend();

    // Wait for backend to be ready (30 second timeout)
    const backendReady = await waitForBackend(30000);
    if (!backendReady) {
      log.error("Backend failed to start within 30 seconds");
      dialog.showErrorBox(
        "Backend Startup Error",
        "The analysis backend failed to start within 30 seconds.\n\n" +
          "Please ensure ODIA is installed correctly and try again."
      );
    } else {
      log.info("Backend is ready");
    }
  } catch (err) {
    log.error("Backend startup error:", err);
  }

  // Register IPC handlers
  registerIpcHandlers(ipcMain, dialog);

  // Create the main window
  createWindow();
}

// App lifecycle
app.whenReady().then(onReady);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on("before-quit", () => {
  isQuitting = true;
  log.info("Shutting down backend...");
  stopBackend();
});

// Security: Prevent navigation to external URLs
app.on("web-contents-created", (_event, contents) => {
  contents.on("will-navigate", (event, url) => {
    const frontendPath = getFrontendPath();
    if (!url.startsWith("file://") || !url.includes(frontendPath)) {
      event.preventDefault();
      log.warn(`Blocked navigation to: ${url}`);
    }
  });
});

module.exports = { createWindow, getFrontendPath };
