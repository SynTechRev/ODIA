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
 * Kill any orphaned process still holding the given port from a previous session.
 * Uses execSync so the kill completes before spawn() is called — avoids a race
 * where waitForBackend() polls before backendProcess is set.
 * @param {number} port
 */
function killOrphanOnPort(port) {
  if (process.platform !== "win32") return;
  try {
    const { execSync } = require("child_process");
    execSync(
      `powershell -NonInteractive -Command "$c=Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue; if ($c) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 600 }"`,
      { timeout: 4000, stdio: "ignore" }
    );
  } catch {
    // Non-fatal — proceed even if the kill fails or times out
  }
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

  // Clear any orphaned backend from a previous session before binding the port.
  // Synchronous so the process is gone before spawn() runs.
  killOrphanOnPort(BACKEND_PORT);

  // Write rag_config.py to the path the binary resolves via _REPO_ROOT.
  // The binary computes _REPO_ROOT = Path(__file__).parent × 4, which lands in
  // %TEMP% (one level above the MEI extraction dir), then appends /config.
  // Without this file the import falls back to the openai provider default.
  const tempConfigDir = require("os").tmpdir() + require("path").sep + "config";
  try {
    require("fs").mkdirSync(tempConfigDir, { recursive: true });
    const ragConfigContent = [
      '"""RAG config override — written by ODIA Electron at startup."""',
      'import os',
      'RAG_LLM_PROVIDER = "ollama"',
      'RAG_LLM_MODEL = "odia-v1"',
      'RAG_TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.1"))',
      'RAG_MAX_RESPONSE_TOKENS = int(os.getenv("RAG_MAX_RESPONSE_TOKENS", "1000"))',
      'RAG_TOP_K = int(os.getenv("RAG_TOP_K", "15"))',
      'RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.2"))',
      'RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "4000"))',
      'OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")',
      'ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")',
      'OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11435")',
      'VECTOR_INDICES = {"corpus":"data/vectors/collection","ace":"data/vectors/ace_collection","jim":"data/vectors/jim_collection"}',
      'DEFAULT_VOCAB_PATH = "data/vectors/collection_vocab.pkl"',
      'RAG_ENABLE_CACHING = False',
      'RAG_ENABLE_STREAMING = False',
      'RAG_ENABLE_ROUTING = True',
      'RAG_LOG_LEVEL = "INFO"',
      'RAG_LOG_API_CALLS = False',
    ].join("\n");
    require("fs").writeFileSync(
      require("path").join(tempConfigDir, "rag_config.py"),
      ragConfigContent,
      "utf8"
    );
    log.info(`Wrote rag_config.py to ${tempConfigDir} (provider=ollama model=odia-v1)`);
  } catch (err) {
    log.error("Failed to write rag_config.py override:", err.message);
  }

  const { command, args } = getBackendCommand();
  log.info(`Starting backend: ${command} ${args.join(" ")}`);

  // Resolve data paths.
  // Dev:      repo-root/ (two levels up from desktop/src/)
  // Packaged: the install directory (process.resourcesPath/..) holds the
  //           bundled oraculus_audit.db and data/vectors/ that ship with the
  //           installer.  userData (%APPDATA%\ODIA) would be empty on first
  //           launch because the installer only writes to the install dir.
  let dataRoot;
  if (app.isPackaged) {
    // process.resourcesPath = <install_dir>/resources — go one level up.
    const installDir = path.join(process.resourcesPath, "..");
    const fs = require("fs");
    const bundledDb = path.join(installDir, "oraculus_audit.db");
    // Use install dir when the bundled DB exists there (normal install).
    // Fall back to userData so user-created data persists across reinstalls.
    dataRoot = fs.existsSync(bundledDb) ? installDir : app.getPath("userData");
  } else {
    dataRoot = path.join(__dirname, "..", "..");
  }
  const dbPath = path.join(dataRoot, "oraculus_audit.db");
  const vectorsDir = path.join(dataRoot, "data", "vectors");

  const env = {
    ...process.env,
    ODIA_VERSION: PACKAGE_VERSION,
    ODIA_OFFLINE_MODE: "1",
    // Frontend is served from an in-process Node.js HTTP server on 18742.
    // Include that origin so the API's CORS policy accepts its requests.
    ORACULUS_CORS_ORIGINS: `http://127.0.0.1:18742,http://${BACKEND_HOST}:${BACKEND_PORT}`,
    PYTHONUNBUFFERED: "1",
    DATABASE_URL: `sqlite:///${dbPath}`,
    ODIA_VECTORS_DIR: vectorsDir,
    // RAG model — explicitly set so the binary never inherits an empty value
    // from the parent process or an older default in the compiled code.
    RAG_LLM_PROVIDER: "ollama",
    RAG_LLM_MODEL: "odia-v1",
    // Point backend at the Electron-hosted Ollama proxy (port 11435).
    // The proxy fixes model="" → "odia-v1" before forwarding to real Ollama (11434).
    OLLAMA_BASE_URL: "http://127.0.0.1:11435",
    // TF-IDF cosine similarity for NL queries is typically 0.05-0.15;
    // the compiled default of 0.3 filters every result. Use 0.05.
    RAG_SIMILARITY_THRESHOLD: "0.05",
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
