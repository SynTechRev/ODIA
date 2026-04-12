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

// Mock fs — include promises.readFile for async file reads
const mockStatSync = jest.fn();
const mockReadFileAsync = jest.fn();
jest.mock("fs", () => ({
  statSync: mockStatSync,
  promises: {
    readFile: mockReadFileAsync,
  },
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

const {
  registerIpcHandlers,
  DOCUMENT_FILTERS,
  REPORT_FILTERS,
  MAX_FILE_SIZE,
  backendRequest,
} = require("../src/ipc");

/**
 * Helper to create a minimal mock HTTP response.
 * @param {number} statusCode
 * @param {string} body
 * @returns {Object} mock request
 */
function mockHttpResponse(statusCode, body) {
  let dataHandler;
  let endHandler;

  const mockRes = {
    statusCode,
    on: jest.fn((event, handler) => {
      if (event === "data") dataHandler = handler;
      if (event === "end") endHandler = handler;
    }),
  };

  const mockReq = {
    on: jest.fn(),
    write: jest.fn(),
    end: jest.fn(() => {
      // Simulate async response
      setImmediate(() => {
        dataHandler(body);
        endHandler();
      });
    }),
  };

  mockHttpRequest.mockImplementation((_opts, callback) => {
    callback(mockRes);
    return mockReq;
  });

  return mockReq;
}

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
        .mockReturnValueOnce({ size: MAX_FILE_SIZE + 1, isFile: () => true })
        .mockReturnValueOnce({ size: 1024, isFile: () => true });

      const result = await handlers["dialog:open-file"]({}, {});
      expect(result).toEqual(["/path/small-file.pdf"]);
    });

    test("filters out non-file paths (directories, special files)", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ["/path/a-directory", "/path/real-file.txt"],
      });

      mockStatSync
        .mockReturnValueOnce({ size: 0, isFile: () => false })
        .mockReturnValueOnce({ size: 512, isFile: () => true });

      const result = await handlers["dialog:open-file"]({}, {});
      expect(result).toEqual(["/path/real-file.txt"]);
    });

    test("supports multiple file selection", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: false,
        filePaths: ["/path/a.pdf", "/path/b.txt"],
      });
      mockStatSync.mockReturnValue({ size: 512, isFile: () => true });

      await handlers["dialog:open-file"]({}, { multiple: true });

      expect(mockDialog.showOpenDialog).toHaveBeenCalledWith(
        expect.objectContaining({
          properties: expect.arrayContaining(["multiSelections"]),
        })
      );
    });

    test("uses DOCUMENT_FILTERS when no custom filters provided", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: [],
      });

      await handlers["dialog:open-file"]({}, {});

      expect(mockDialog.showOpenDialog).toHaveBeenCalledWith(
        expect.objectContaining({ filters: DOCUMENT_FILTERS })
      );
    });

    test("honors custom filters from options", async () => {
      const customFilters = [{ name: "CSV Files", extensions: ["csv"] }];
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: [],
      });

      await handlers["dialog:open-file"]({}, { filters: customFilters });

      expect(mockDialog.showOpenDialog).toHaveBeenCalledWith(
        expect.objectContaining({ filters: customFilters })
      );
    });

    test("falls back to DOCUMENT_FILTERS when options.filters is empty", async () => {
      mockDialog.showOpenDialog.mockResolvedValue({
        canceled: true,
        filePaths: [],
      });

      await handlers["dialog:open-file"]({}, { filters: [] });

      expect(mockDialog.showOpenDialog).toHaveBeenCalledWith(
        expect.objectContaining({ filters: DOCUMENT_FILTERS })
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
    test("returns unavailable when backend is not healthy", async () => {
      mockCheckBackendHealth.mockResolvedValue(false);

      const result = await handlers["backend:health"]({});
      expect(result).toEqual({ status: "unavailable" });
    });

    test("returns health data on 2xx response when backend is healthy", async () => {
      mockCheckBackendHealth.mockResolvedValue(true);
      mockHttpResponse(200, JSON.stringify({ status: "healthy", version: "1.0.0" }));

      const result = await handlers["backend:health"]({});
      expect(result).toEqual({ status: "healthy", version: "1.0.0" });
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

    test("reads file async when filePath is provided", async () => {
      mockStatSync.mockReturnValue({ isFile: () => true, size: 100 });
      mockReadFileAsync.mockResolvedValue("Document content here");
      mockHttpResponse(200, JSON.stringify({ findings: {} }));

      const result = await handlers["backend:analyze"](
        {},
        { filePath: "/path/to/document.txt" }
      );

      expect(mockReadFileAsync).toHaveBeenCalledWith(
        expect.stringContaining("document.txt"),
        "utf-8"
      );
      expect(result).toEqual({ findings: {} });
    });

    test("throws when file path is a directory (not a regular file)", async () => {
      mockStatSync.mockReturnValue({ isFile: () => false, size: 0 });

      await expect(
        handlers["backend:analyze"]({}, { filePath: "/path/to/directory" })
      ).rejects.toThrow("Path is not a file");
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

    test("uses documentText directly without file read", async () => {
      mockHttpResponse(200, JSON.stringify({ findings: {} }));

      const result = await handlers["backend:analyze"](
        {},
        { documentText: "inline content", metadata: { title: "Test" } }
      );

      expect(mockReadFileAsync).not.toHaveBeenCalled();
      expect(result).toEqual({ findings: {} });
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

describe("backendRequest", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("resolves with parsed body on 2xx response", async () => {
    mockHttpResponse(200, JSON.stringify({ status: "healthy" }));
    const result = await backendRequest("GET", "/api/v1/health");
    expect(result).toEqual({ status: "healthy" });
  });

  test("rejects on 4xx response", async () => {
    mockHttpResponse(400, JSON.stringify({ detail: "Bad Request" }));
    await expect(backendRequest("POST", "/analyze", {})).rejects.toThrow(
      "Backend request failed with status 400"
    );
  });

  test("rejects on 5xx response", async () => {
    mockHttpResponse(500, JSON.stringify({ detail: "Internal Server Error" }));
    await expect(backendRequest("GET", "/analyze")).rejects.toThrow(
      "Backend request failed with status 500"
    );
  });

  test("rejects on invalid JSON response", async () => {
    mockHttpResponse(200, "not json");
    await expect(backendRequest("GET", "/api/v1/health")).rejects.toThrow(
      "Invalid response from backend"
    );
  });
});
