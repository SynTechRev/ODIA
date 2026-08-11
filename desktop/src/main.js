"use strict";

const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const path = require("path");
const http = require("http");
const fs = require("fs");
const log = require("electron-log");

const { startBackend, stopBackend, waitForBackend, BACKEND_PORT, BACKEND_HOST } = require("./backend");
const { registerIpcHandlers } = require("./ipc");

// ---------------------------------------------------------------------------
// Ollama proxy — fixes model="" sent by compiled binary.
// Listens on 11435, forwards to real Ollama on 11434.
// Patches model name to "odia-v1" on /api/chat and /api/generate when empty.
// ---------------------------------------------------------------------------
const OLLAMA_REAL_PORT = 11434;
const OLLAMA_PROXY_PORT = 11435;
const DEFAULT_MODEL = "odia-v1";

function startOllamaProxy() {
  const proxy = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      let rawBody = Buffer.concat(chunks);
      const isGenerate = req.url === "/api/generate";

      if (isGenerate && rawBody.length > 0) {
        let body;
        try { body = JSON.parse(rawBody.toString("utf8")); } catch (_) { body = null; }

        if (body) {
          // Fix empty model name.
          if (!body.model || body.model === "") {
            body.model = DEFAULT_MODEL;
            log.info(`[ollama-proxy] Patched empty model → ${DEFAULT_MODEL}`);
          }
          // Cap num_predict — frontend now has a 15-min timeout so we can
          // afford longer responses; 1000 tokens ≈ 2–3 minutes at 6 t/s.
          body.options = body.options || {};
          if (!body.options.num_predict || body.options.num_predict > 1000) {
            body.options.num_predict = 1000;
          }

          // STREAMING KEEP-ALIVE: the binary sends stream=false and blocks until
          // Ollama returns the full response.  On a cold HDD load the model can
          // take > 300 s, which trips Python's requests timeout.  We convert the
          // request to stream=true, buffer every token, and meanwhile send a
          // harmless space every 30 s over chunked transfer encoding to keep
          // Python's read-socket alive.  json.loads() strips leading whitespace,
          // so the final assembled payload parses cleanly on the Python side.
          const nonStreaming = body.stream === false || body.stream === undefined;
          if (nonStreaming) {
            body.stream = true;
            rawBody = Buffer.from(JSON.stringify(body), "utf8");

            log.info(`[ollama-proxy] generate intercept — streaming to Ollama, keepalive to Python`);

            // Send headers immediately so Python's recv() starts receiving data
            // on the very first call, never hitting the 300 s read timeout.
            res.writeHead(200, { "Content-Type": "application/json" });
            // Force-flush headers by writing the first keepalive byte now.
            try { res.write(" "); } catch (_) {}

            // Disable Node.js socket timeout on this connection so it never
            // drops the Python side during a long model load.
            if (res.socket) res.socket.setTimeout(0);

            // Keep-alive: send a space every 5 s to prevent Python's per-read timeout.
            let kaCount = 0;
            const keepAlive = setInterval(() => {
              kaCount++;
              try {
                res.write(" ");
                if (kaCount % 12 === 0) log.info(`[ollama-proxy] keepalive ${kaCount * 5}s elapsed`);
              } catch (_) { clearInterval(keepAlive); }
            }, 5000);

            let lineBuf = "";
            let assembled = "";
            let finalObj = null;

            const upOpts = {
              hostname: "127.0.0.1",
              port: OLLAMA_REAL_PORT,
              path: req.url,
              method: "POST",
              headers: { ...req.headers, "content-length": rawBody.length },
            };

            const up = http.request(upOpts, (upRes) => {
              upRes.on("data", (chunk) => {
                lineBuf += chunk.toString("utf8");
                const lines = lineBuf.split("\n");
                lineBuf = lines.pop() || "";
                for (const line of lines) {
                  const t = line.trim();
                  if (!t) continue;
                  try {
                    const tok = JSON.parse(t);
                    if (tok.response) assembled += tok.response;
                    // Strip context array — can be 10k+ chars and Python doesn't need it.
                    if (tok.done) {
                      const { context: _ctx, ...rest } = tok;
                      finalObj = { ...rest, response: assembled };
                    }
                  } catch (_) {}
                }
              });

              upRes.on("end", () => {
                clearInterval(keepAlive);

                // The model echoes its system-context preamble before the
                // actual Q&A content.  Strip everything up to (but not
                // including) the first "Question:" so the frontend receives
                // only the substantive answer.
                const qIdx = assembled.indexOf("Question:");
                if (qIdx > 50) {
                  assembled = assembled.slice(qIdx);
                }

                const respObj = finalObj
                  ? { ...finalObj, response: assembled }
                  : { model: body.model, response: assembled, done: true };
                const payload = JSON.stringify(respObj);
                let writeOk = false;
                try { res.write(payload); res.end(); writeOk = true; } catch (e) {
                  log.error("[ollama-proxy] final write failed (Python closed socket?):", e.message);
                }
                log.info(`[ollama-proxy] Streamed → assembled ${assembled.length} chars (write ${writeOk ? "ok" : "FAILED"})`);
              });
            });

            up.on("error", (err) => {
              clearInterval(keepAlive);
              log.error("[ollama-proxy] upstream error:", err.message);
              try { res.end(); } catch (_) {}
            });

            up.end(rawBody);
            return; // response handled above — skip transparent proxy below
          }

          rawBody = Buffer.from(JSON.stringify(body), "utf8");
        }
      }

      // Transparent proxy for all other requests (tags, chat, pull, etc.).
      const opts = {
        hostname: "127.0.0.1",
        port: OLLAMA_REAL_PORT,
        path: req.url,
        method: req.method,
        headers: { ...req.headers, "content-length": rawBody.length },
      };
      const upstream = http.request(opts, (upRes) => {
        res.writeHead(upRes.statusCode, upRes.headers);
        upRes.pipe(res);
      });
      upstream.on("error", (err) => {
        log.error("[ollama-proxy] upstream error:", err.message);
        res.writeHead(502);
        res.end("Proxy error: " + err.message);
      });
      upstream.end(rawBody);
    });
  });
  proxy.listen(OLLAMA_PROXY_PORT, "127.0.0.1", () => {
    log.info(`Ollama proxy: 127.0.0.1:${OLLAMA_PROXY_PORT} → Ollama:${OLLAMA_REAL_PORT}`);
  });
  proxy.on("error", (err) => log.error("Ollama proxy error:", err.message));
  return proxy;
}

log.transports.file.level = "info";
log.transports.console.level = "debug";

/** Port for the in-process static file server (frontend only). */
const FRONTEND_PORT = 18742;

/** @type {BrowserWindow | null} */
let mainWindow = null;

/** @type {http.Server | null} */
let frontendServer = null;

function getFrontendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "frontend");
  }
  return path.join(__dirname, "..", "..", "frontend", "out");
}

function getWindowIconPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "icon.png");
  }
  return path.join(__dirname, "..", "resources", "icon.png");
}

// ---------------------------------------------------------------------------
// Minimal static file server
// Serves Next.js static export over HTTP so:
//   • Absolute paths like /_next/... resolve correctly (not to C:/_next/)
//   • Directory routes (/documents) auto-serve index.html (SPA behaviour)
//   • window.location.protocol is "http:", not "file:" — normal Chromium mode
// ---------------------------------------------------------------------------
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".txt": "text/plain",
  ".webmanifest": "application/manifest+json",
};

function startFrontendServer(frontendDir) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const rawPath = req.url.split("?")[0];
      let relative = decodeURIComponent(rawPath.replace(/^\//, "")) || "index.html";

      // Directory (trailing slash) → index.html
      if (relative.endsWith("/")) relative += "index.html";

      // Extension-less path → try <path>/index.html first, then <path>.html
      if (!path.extname(relative)) {
        const dirIndex = path.join(frontendDir, relative, "index.html");
        if (fs.existsSync(dirIndex)) {
          relative = path.join(relative, "index.html");
        } else {
          relative = relative + ".html";
        }
      }

      const fsPath = path.join(frontendDir, relative);
      const ext = path.extname(fsPath).toLowerCase();
      const contentType = MIME[ext] || "application/octet-stream";

      fs.readFile(fsPath, (err, data) => {
        if (err) {
          // SPA fallback: serve index.html for unknown routes so Next.js router
          // can handle them client-side rather than showing a hard 404.
          fs.readFile(path.join(frontendDir, "index.html"), (e2, d2) => {
            if (e2) { res.writeHead(404); res.end("Not found"); return; }
            res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
            res.end(d2);
          });
          return;
        }
        res.writeHead(200, { "Content-Type": contentType });
        res.end(data);
      });
    });

    server.listen(FRONTEND_PORT, "127.0.0.1", () => {
      log.info(`Frontend server: http://127.0.0.1:${FRONTEND_PORT} → ${frontendDir}`);
      resolve(server);
    });
    server.on("error", reject);
  });
}

// ---------------------------------------------------------------------------

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: "ODIA — Document Analysis",
    icon: getWindowIconPath(),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
    show: false,
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  const frontendURL = `http://127.0.0.1:${FRONTEND_PORT}`;
  log.info(`Loading frontend from: ${frontendURL}`);
  mainWindow.loadURL(frontendURL).catch((err) => {
    log.error("Failed to load frontend:", err);
  });
}

async function onReady() {
  log.info("ODIA Desktop starting...");
  log.info(`App version: ${app.getVersion()}`);
  log.info(`Electron: ${process.versions.electron}`);
  log.info(`Platform: ${process.platform} ${process.arch}`);

  if (process.platform === "win32" && app.setAppUserModelId) {
    app.setAppUserModelId("com.syntechrev.odia");
  }

  // Start Ollama proxy (patches model="" before backend calls hit real Ollama).
  startOllamaProxy();

  // Fire-and-forget: preload odia-v1 into Ollama's RAM now so the user's first
  // RAG query doesn't have to pay the 200–300 s cold-model-load penalty.
  // We route through the proxy so the num_predict cap applies.
  setTimeout(() => {
    const warmBody = Buffer.from(JSON.stringify({
      model: DEFAULT_MODEL,
      prompt: ".",
      stream: false,
      options: { num_predict: 1 },
    }), "utf8");
    const warmReq = http.request({
      hostname: "127.0.0.1",
      port: OLLAMA_PROXY_PORT,
      path: "/api/generate",
      method: "POST",
      headers: { "Content-Type": "application/json", "content-length": warmBody.length },
    }, (res) => {
      res.resume();
      log.info(`[ollama-proxy] Model warm-up complete (HTTP ${res.statusCode})`);
    });
    warmReq.on("error", (e) => log.warn("[ollama-proxy] Warm-up error:", e.message));
    warmReq.setTimeout(360000, () => { warmReq.destroy(); });
    warmReq.end(warmBody);
    log.info(`[ollama-proxy] Warming up ${DEFAULT_MODEL} in background…`);
  }, 2000);

  // Start the in-process frontend HTTP server before creating the window.
  try {
    frontendServer = await startFrontendServer(getFrontendPath());
  } catch (err) {
    log.error("Frontend server failed to start:", err);
    // Fall back to file:// if the port is taken
  }

  registerIpcHandlers(ipcMain, dialog);
  createWindow();

  try {
    log.info("Starting Python backend (background)...");
    startBackend();
  } catch (err) {
    log.error("Backend failed to spawn:", err);
    dialog.showErrorBox(
      "Backend failed to start",
      "The analysis backend could not be launched.\n\n" +
        (err && err.message ? err.message : String(err)) +
        "\n\nPlease reinstall O.D.I.A. or check the application logs."
    );
    return;
  }

  const startedAt = Date.now();
  waitForBackend(120_000)
    .then((ready) => {
      if (ready) {
        log.info(`Backend ready after ${Date.now() - startedAt} ms`);
      } else {
        log.error("Backend did not respond within 120 s (sidebar will still show offline)");
      }
    })
    .catch((err) => {
      log.error("Backend readiness check failed:", err);
    });
}

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
  log.info("Shutting down backend...");
  stopBackend();
  if (frontendServer) {
    frontendServer.close();
    frontendServer = null;
  }
});

// Navigation guard: allow navigation within the in-process frontend server only.
app.on("web-contents-created", (_event, contents) => {
  contents.on("will-navigate", (event, url) => {
    if (url.startsWith(`http://127.0.0.1:${FRONTEND_PORT}/`)) return;
    if (url.startsWith(`http://${BACKEND_HOST}:${BACKEND_PORT}/`)) return;
    event.preventDefault();
    log.warn(`Blocked navigation to: ${url}`);
  });
});

module.exports = { createWindow, getFrontendPath, getWindowIconPath };
