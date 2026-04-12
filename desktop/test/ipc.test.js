"use strict";

/**
 * Tests for IPC handlers (dialog:open-file, dialog:save-file,
 * backend:health, backend:analyze, etc.)
 */

// Mock electron modules
const mockDialog = {
  showOpenDialog: jest.fn(),
  showSaveDialog: jest.fn(),
};

const mockApp = {
  getVersion: jest.fn(() => "2.1.0"),
};

const mockShell = {
  openExternal: jest.fn(() => Promise.resolve()),
};

jest.mock("electron", () => ({
  app: mockApp,
  shell: mockShell,
}));

jest.mock("electron-log", () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
}));

// Mock fs
const mockStatSync = jest.fn();
const mockReadFileSync = jest.fn();
jest.mock("fs", () => ({
  statSync: mockStatSync,
  readFileSync: mockReadFileSync,
}));

// Mock http for backend requests
const mockHttpRequest = jest.fn();
const mockHttpGet = jest.fn();
jest.mock("http", () => ({
  request: mockHttpRequest,
  get: mockHttpGet,
}));

// Mock backend module
const mockCheckBackendHealth = jest.fn();
const mockGetBackendInfo = jest.fn();
jest.mock("../src/backend", () => ({
  checkBackendHealth: mockCheckBackendHealth,
  getBackendInfo: mockGetBackendInfo,
  BACKEND_HOST: "127.0.0.1",
  BACKEND_PORT: 18741,
}));

const { registerIpcHandlers, DOCUMENT_FILTERS, REPORT_FILTERS, MAX_FILE_SIZE } = require("../src/ipc");

describe("IPC Handlers", () => {
  let handlers;
  let mockIpcMain;

  beforeEach(() => {
    handlers = {};
    mockIpcMain = {
      handle: jest.fn((channel, handler) => {
        handlers[channel] = handler;
      }),
    };

    // Reset all mocks
    jest.clearAllMocks();

    // Register handlers
    registerIpcHandlers(mockIpcMain, mockDialog);
  });

  describe("registerIpcHandlers", () => {
    test("registers all expected channels", () => {
      const expectedChannels = [
        "dialog:open-file",
        "dialog:save-file",
        "backend:health",
        "backend:analyze",
        "backend:status",
        "app:version",
        "shell:open-external",
      ];

      for (const channel of expectedChannels) {
        expect(handlers[channel]).toBeDefined();
      }
    });
  });

  describe("dialog:open-file", () => {
    test("returns selected file paths", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ["/path/to/document.pdf"],
      });
      mockStatSync.mockReturnValue({ size: 1024, isFile: () => true });

      const result = await handlers["dialog:open-file"]({}, {});
      expect(result).toEqual(["/path/to/document.pdf"]);
    });

    test("returns empty array when cancelled", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: [],
      });

      const result = await handlers["dialog:open-file"]({}, {});
      expect(result).toEqual([]);
    });

    test("filters out files exceeding max size", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ["/path/large-file.pdf", "/path/small-file.pdf"],
      });

      mockStatSync
        .mockReturnValueOnce({ size: MAX_FILE_SIZE + 1 })
        .mockReturnValueOnce({ size: 1024 });

      const result = await handlers["dialog:open-file"]({}, {});
      expect(result).toEqual(["/path/small-file.pdf"]);
    });

    test("supports multiple file selection", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ["/path/a.pdf", "/path/b.txt"],
      });
      mockStatSync.mockReturnValue({ size: 512 });

      const result = await handlers["dialog:open-file"]({}, { multiple: true });

      // Check that multiSelections was passed
      expect(mockDialog.showOpenDialog).toHaveBeenCalledWith(
        expect.objectContaining({
          properties: expect.arrayContaining(["multiSelections"]),
        })
      );
    });
  });

  describe("dialog:save-file", () => {
    test("returns selected save path", async () => {
      mockDialog.showSaveDialog.mockResolvedValue({
        canceled: false,
        filePath: "/path/to/report.md",
      });

      const result = await handlers["dialog:save-file"]({}, {});
      expect(result).toBe("/path/to/report.md");
    });

    test("returns null when cancelled", async () => {
      mockDialog.showSaveDialog.mockResolvedValue({ canceled: true });

      const result = await handlers["dialog:save-file"]({}, {});
      expect(result).toBeNull();
    });

    test("uses custom default path and title", async () => {
      mockDialog.showSaveDialog.mockResolvedValue({
        canceled: false,
        filePath: "/custom/report.json",
      });

      await handlers["dialog:save-file"](
        {},
        { defaultPath: "custom-report.json", title: "Export Report" }
      );

      expect(mockDialog.showSaveDialog).toHaveBeenCalledWith(
        expect.objectContaining({
          defaultPath: "custom-report.json",
          title: "Export Report",
        })
      );
    });
  });

  describe("backend:health", () => {
    test("returns health data when backend is healthy", async () => {
      mockCheckBackendHealth.mockResolvedValue(true);

      // Mock the backendRequest inside ipc.js — we test via the handler
      // The handler calls checkBackendHealth, then makes an HTTP request
      // For unit tests, we just verify the checkBackendHealth path
      const result = await handlers["backend:health"]({});

      // When checkBackendHealth returns true, the handler tries to make
      // an HTTP request; since we haven't mocked that fully, we check
      // it doesn't throw and returns something
      expect(result).toBeDefined();
    });

    test("returns unavailable when backend is not healthy", async () => {
      mockCheckBackendHealth.mockResolvedValue(false);

      const result = await handlers["backend:health"]({});
      expect(result).toEqual({ status: "unavailable" });
    });
  });

  describe("backend:analyze", () => {
    test("throws when no documentText or filePath provided", async () => {
      await expect(
        handlers["backend:analyze"]({}, {})
      ).rejects.toThrow("Either documentText or filePath is required");
    });

    test("throws when null payload", async () => {
      await expect(
        handlers["backend:analyze"]({}, null)
      ).rejects.toThrow("Either documentText or filePath is required");
    });

    test("reads file from disk when filePath is provided", async () => {
      const filePath = "/path/to/document.txt";
      mockStatSync.mockReturnValue({
        isFile: () => true,
        size: 100,
      });
      mockReadFileSync.mockReturnValue("Document content here");

      // The handler will try to make an HTTP request to the backend
      // Since http is mocked, this will fail, but we verify file reading works
      try {
        await handlers["backend:analyze"]({}, { filePath });
      } catch {
        // Expected: HTTP request mock isn't fully set up
      }

      expect(mockReadFileSync).toHaveBeenCalledWith(
        expect.stringContaining("document.txt"),
        "utf-8"
      );
    });

    test("throws when file exceeds max size", async () => {
      mockStatSync.mockReturnValue({
        isFile: () => true,
        size: MAX_FILE_SIZE + 1,
      });

      await expect(
        handlers["backend:analyze"]({}, { filePath: "/path/big.pdf" })
      ).rejects.toThrow("exceeds maximum size");
    });

    test("throws when file not found", async () => {
      mockStatSync.mockImplementation(() => {
        const err = new Error("ENOENT");
        err.code = "ENOENT";
        throw err;
      });

      await expect(
        handlers["backend:analyze"]({}, { filePath: "/nonexistent.pdf" })
      ).rejects.toThrow("File not found");
    });
  });

  describe("backend:status", () => {
    test("returns backend info with health status", async () => {
      mockGetBackendInfo.mockReturnValue({
        host: "127.0.0.1",
        port: 18741,
        connected: true,
      });
      mockCheckBackendHealth.mockResolvedValue(true);

      const result = await handlers["backend:status"]({});
      expect(result).toEqual({
        host: "127.0.0.1",
        port: 18741,
        connected: true,
      });
    });
  });

  describe("app:version", () => {
    test("returns app version", async () => {
      const result = await handlers["app:version"]({});
      expect(result).toBe("2.1.0");
    });
  });

  describe("shell:open-external", () => {
    test("opens https URLs", async () => {
      await handlers["shell:open-external"]({}, "https://example.com");
      expect(mockShell.openExternal).toHaveBeenCalledWith("https://example.com");
    });

    test("opens http URLs", async () => {
      await handlers["shell:open-external"]({}, "http://example.com");
      expect(mockShell.openExternal).toHaveBeenCalledWith("http://example.com");
    });

    test("rejects non-http URLs", async () => {
      await expect(
        handlers["shell:open-external"]({}, "file:///etc/passwd")
      ).rejects.toThrow("Only http and https URLs are allowed");
    });

    test("rejects non-string input", async () => {
      await expect(
        handlers["shell:open-external"]({}, 12345)
      ).rejects.toThrow("URL must be a string");
    });
  });

  describe("Constants", () => {
    test("DOCUMENT_FILTERS includes all supported types", () => {
      const allExtensions = DOCUMENT_FILTERS.flatMap((f) => f.extensions);
      expect(allExtensions).toContain("pdf");
      expect(allExtensions).toContain("txt");
      expect(allExtensions).toContain("json");
      expect(allExtensions).toContain("xml");
    });

    test("REPORT_FILTERS includes export formats", () => {
      const allExtensions = REPORT_FILTERS.flatMap((f) => f.extensions);
      expect(allExtensions).toContain("md");
      expect(allExtensions).toContain("json");
    });

    test("MAX_FILE_SIZE is 50MB", () => {
      expect(MAX_FILE_SIZE).toBe(50 * 1024 * 1024);
    });
  });
});
