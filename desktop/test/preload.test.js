"use strict";

/**
 * Tests for the preload script API surface.
 */

// Mock electron
const mockInvoke = jest.fn();

jest.mock("electron", () => ({
  contextBridge: {
    exposeInMainWorld: jest.fn(),
  },
  ipcRenderer: {
    invoke: mockInvoke,
  },
}));

const { contextBridge } = require("electron");

describe("Preload Script", () => {
  let exposedApi;

  beforeEach(() => {
    jest.clearAllMocks();
    // Load the preload script
    require("../src/preload");

    // Capture the exposed API
    exposedApi = contextBridge.exposeInMainWorld.mock.calls[0][1];
  });

  afterEach(() => {
    jest.resetModules();
  });

  test("exposes API under 'odiaDesktop' namespace", () => {
    expect(contextBridge.exposeInMainWorld).toHaveBeenCalledWith(
      "odiaDesktop",
      expect.any(Object)
    );
  });

  test("exposes openFileDialog method", () => {
    expect(typeof exposedApi.openFileDialog).toBe("function");
    exposedApi.openFileDialog({ multiple: true });
    expect(mockInvoke).toHaveBeenCalledWith("dialog:open-file", {
      multiple: true,
    });
  });

  test("exposes saveFileDialog method", () => {
    expect(typeof exposedApi.saveFileDialog).toBe("function");
    exposedApi.saveFileDialog({ defaultPath: "report.md" });
    expect(mockInvoke).toHaveBeenCalledWith("dialog:save-file", {
      defaultPath: "report.md",
    });
  });

  test("exposes checkHealth method", () => {
    expect(typeof exposedApi.checkHealth).toBe("function");
    exposedApi.checkHealth();
    expect(mockInvoke).toHaveBeenCalledWith("backend:health");
  });

  test("exposes analyzeDocument method", () => {
    expect(typeof exposedApi.analyzeDocument).toBe("function");
    const payload = { documentText: "test content" };
    exposedApi.analyzeDocument(payload);
    expect(mockInvoke).toHaveBeenCalledWith("backend:analyze", payload);
  });

  test("exposes getBackendStatus method", () => {
    expect(typeof exposedApi.getBackendStatus).toBe("function");
    exposedApi.getBackendStatus();
    expect(mockInvoke).toHaveBeenCalledWith("backend:status");
  });

  test("exposes getAppVersion method", () => {
    expect(typeof exposedApi.getAppVersion).toBe("function");
    exposedApi.getAppVersion();
    expect(mockInvoke).toHaveBeenCalledWith("app:version");
  });

  test("exposes openExternal method", () => {
    expect(typeof exposedApi.openExternal).toBe("function");
    exposedApi.openExternal("https://example.com");
    expect(mockInvoke).toHaveBeenCalledWith(
      "shell:open-external",
      "https://example.com"
    );
  });

  test("API has exactly the expected methods", () => {
    const expectedMethods = [
      "openFileDialog",
      "saveFileDialog",
      "checkHealth",
      "analyzeDocument",
      "getBackendStatus",
      "getAppVersion",
      "openExternal",
    ];

    const actualMethods = Object.keys(exposedApi);
    expect(actualMethods.sort()).toEqual(expectedMethods.sort());
  });
});
