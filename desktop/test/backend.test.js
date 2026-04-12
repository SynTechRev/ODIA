"use strict";

/**
 * Tests for backend lifecycle management (startup, health check, shutdown).
 */

// Mock electron
jest.mock("electron", () => ({
  app: {
    isPackaged: false,
    getVersion: jest.fn(() => "2.1.0"),
  },
}));

jest.mock("electron-log", () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
}));

// Track spawned processes
const mockProcess = {
  stdout: { on: jest.fn() },
  stderr: { on: jest.fn() },
  on: jest.fn(),
  kill: jest.fn(),
  pid: 12345,
};

jest.mock("child_process", () => ({
  spawn: jest.fn(() => mockProcess),
}));

// Mock http for health checks
const mockHttpGet = jest.fn();
jest.mock("http", () => ({
  get: mockHttpGet,
}));

const { spawn } = require("child_process");

describe("Backend Module", () => {
  let backend;

  beforeEach(() => {
    jest.clearAllMocks();
    // Re-require to reset module state
    jest.resetModules();

    // Re-mock after resetModules
    jest.mock("electron", () => ({
      app: {
        isPackaged: false,
        getVersion: jest.fn(() => "2.1.0"),
      },
    }));
    jest.mock("electron-log", () => ({
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn(),
    }));
    jest.mock("child_process", () => ({
      spawn: jest.fn(() => ({
        stdout: { on: jest.fn() },
        stderr: { on: jest.fn() },
        on: jest.fn(),
        kill: jest.fn(),
        pid: 12345,
      })),
    }));
    jest.mock("http", () => ({
      get: mockHttpGet,
    }));

    backend = require("../src/backend");
  });

  describe("startBackend", () => {
    test("spawns uvicorn in development mode", () => {
      backend.startBackend();
      const { spawn: spawnFn } = require("child_process");

      expect(spawnFn).toHaveBeenCalledTimes(1);
      const [command, args, options] = spawnFn.mock.calls[0];

      // Should use python/python3
      expect(command).toMatch(/python/);
      expect(args).toContain("-m");
      expect(args).toContain("uvicorn");
      expect(args).toContain("oraculus_di_auditor.interface.api:app");
      expect(args).toContain("--host");
      expect(args).toContain("127.0.0.1");
      expect(args).toContain("--port");
      expect(args).toContain("18741");

      // Should set offline mode
      expect(options.env.ODIA_OFFLINE_MODE).toBe("1");
      expect(options.windowsHide).toBe(true);
    });

    test("does not spawn duplicate if already running", () => {
      backend.startBackend();
      backend.startBackend();

      const { spawn: spawnFn } = require("child_process");
      expect(spawnFn).toHaveBeenCalledTimes(1);
    });
  });

  describe("stopBackend", () => {
    test("does nothing if no backend is running", () => {
      // Should not throw
      backend.stopBackend();
    });

    test("kills the backend process", () => {
      backend.startBackend();
      backend.stopBackend();
      // After stop, getBackendInfo should show not connected
      const info = backend.getBackendInfo();
      expect(info.connected).toBe(false);
    });
  });

  describe("checkBackendHealth", () => {
    test("returns false when request fails", async () => {
      mockHttpGet.mockImplementation((_url, _opts, _cb) => {
        const req = {
          on: jest.fn((event, handler) => {
            if (event === "error") {
              handler(new Error("Connection refused"));
            }
            return req;
          }),
        };
        return req;
      });

      const result = await backend.checkBackendHealth();
      expect(result).toBe(false);
    });
  });

  describe("getBackendInfo", () => {
    test("returns connection info", () => {
      const info = backend.getBackendInfo();
      expect(info).toEqual({
        host: "127.0.0.1",
        port: 18741,
        connected: false,
      });
    });

    test("shows connected after start", () => {
      backend.startBackend();
      const info = backend.getBackendInfo();
      expect(info.connected).toBe(true);
    });
  });

  describe("Constants", () => {
    test("BACKEND_PORT is 18741", () => {
      expect(backend.BACKEND_PORT).toBe(18741);
    });

    test("BACKEND_HOST is 127.0.0.1", () => {
      expect(backend.BACKEND_HOST).toBe("127.0.0.1");
    });
  });
});
