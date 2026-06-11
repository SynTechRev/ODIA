"use strict";

const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const { app } = require("electron");
const log = require("electron-log");
const { version: PACKAGE_VERSION } = require("../package.json");

/** @type {import('child_process').ChildProcess | null} */
let backendProcess = null;

/** @type {number} */
const BACKEND_PORT = 18741;

/** @type {string} */
const BACKEND_HOST = "127.0.0.1";

/**
 * Get the path to the backend executable.
 * In packaged mode, uses the PyInstaller-bundled binary.
 * In development, launches uvicorn directly.
 * @returns {{ command: string, args: string[] }}
 */
function getBackendCommand() {
  if (app.isPackaged) {
    const ext = process.platform === "win32" ? ".exe" : "";
    const backendPath = path.join(
      process.resourcesPath,
      "backend",
      `odia-backend${ext}`
    );
    return {
      command: backendPath,
      args: [
        "--host",
        BACKEND_HOST,
        "--port",
        String(BACKEND_PORT),
      ],
    };
  }

  // Development mode: use uvicorn.
  // Note: interface/api.py exposes a `create_app()` factory (no module-level `app`),
  // so we must invoke uvicorn with --factory.
  return {
    command: process.platform === "win32" ? "python" : "python3",
    args: [
      "-m",
      "uvicorn",
      "oraculus_di_auditor.interface.api:create_app",
      "--factory",
      "--host",
      BACKEND_HOST,
      "--port",
      String(BACKEND_PORT),
      "--no-access-log",
    ],
  };
}

/**
 * Start the Python backend process.
 * Sets environment variables for offline-only operation.
 */
function startBackend() {
  if (backendProcess) {
    log.warn("Backend already running");
    return;
  }

  const { command, args } = getBackendCommand();
  log.info(`Starting backend: ${command} ${args.join(" ")}`);

  // Resolve stable, per-user paths that survive reinstalls.
  // Packaged: %APPDATA%\ODIA\  (Windows) or ~/Library/Application Support/ODIA/ (macOS)
  // Dev:      repo-root/  (two levels up from desktop/src/)
  const dataRoot = app.isPackaged
    ? app.getPath("userData")
    : path.join(__dirname, "..", "..");
  const dbPath = path.join(dataRoot, "oraculus_audit.db");
  const vectorsDir = path.join(dataRoot, "data", "vectors");

  const env = {
    ...process.env,
    ODIA_VERSION: PACKAGE_VERSION,
    ODIA_OFFLINE_MODE: "1",
    ORACULUS_CORS_ORIGINS: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
    PYTHONUNBUFFERED: "1",
    DATABASE_URL: `sqlite:///${dbPath}`,
    ODIA_VECTORS_DIR: vectorsDir,
  };

  backendProcess = spawn(command, args, {
    env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });

  backendProcess.stdout.on("data", (data) => {
    log.info(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on("data", (data) => {
    log.warn(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.on("error", (err) => {
    log.error("Backend process error:", err);
    backendProcess = null;
  });

  backendProcess.on("exit", (code, signal) => {
    log.info(`Backend exited with code=${code} signal=${signal}`);
    backendProcess = null;
  });
}

/**
 * Stop the backend process gracefully.
 * Sends SIGTERM first, then SIGKILL after 5 seconds if still running.
 */
function stopBackend() {
  if (!backendProcess) {
    return;
  }

  log.info("Stopping backend process...");

  const proc = backendProcess;
  backendProcess = null;

  // Try graceful shutdown
  if (process.platform === "win32") {
    // Windows: use taskkill for tree kill
    spawn("taskkill", ["/pid", String(proc.pid), "/T", "/F"], {
      windowsHide: true,
    });
  } else {
    proc.kill("SIGTERM");

    // Force kill after 5 seconds if still running
    const forceKillTimer = setTimeout(() => {
      try {
        proc.kill("SIGKILL");
      } catch {
        // Process already exited
      }
    }, 5000);

    proc.on("exit", () => {
      clearTimeout(forceKillTimer);
    });
  }
}

/**
 * Check if the backend is healthy by hitting the health endpoint.
 * @returns {Promise<boolean>}
 */
function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(
      `http://${BACKEND_HOST}:${BACKEND_PORT}/api/v1/health`,
      { timeout: 2000 },
      (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            const data = JSON.parse(body);
            resolve(data.status === "healthy");
          } catch {
            resolve(false);
          }
        });
      }
    );

    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Wait for the backend to become healthy, polling every second.
 * @param {number} timeoutMs - Maximum time to wait in milliseconds
 * @returns {Promise<boolean>} True if backend started successfully
 */
async function waitForBackend(timeoutMs = 30000) {
  const startTime = Date.now();
  const pollInterval = 1000;

  while (Date.now() - startTime < timeoutMs) {
    const healthy = await checkBackendHealth();
    if (healthy) {
      return true;
    }

    // Check if backend process crashed
    if (!backendProcess) {
      log.error("Backend process exited unexpectedly");
      return false;
    }

    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  return false;
}

/**
 * Get the backend connection info.
 * @returns {{ host: string, port: number, connected: boolean }}
 */
function getBackendInfo() {
  return {
    host: BACKEND_HOST,
    port: BACKEND_PORT,
    connected: backendProcess !== null,
  };
}

module.exports = {
  startBackend,
  stopBackend,
  waitForBackend,
  checkBackendHealth,
  getBackendInfo,
  BACKEND_PORT,
  BACKEND_HOST,
};
