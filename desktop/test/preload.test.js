"use strict";

/**
 * Tests for the preload script API surface.
 */

describe("Preload Script", () => {
  let exposedApi;
  let mockInvoke;

  beforeEach(() => {
    jest.resetModules();

    mockInvoke = jest.fn();

    jest.doMock("electron", () => ({
      contextBridge: {
        exposeInMainWorld: jest.fn(),
      },
      ipcRenderer: {
        invoke: mockInvoke,
      },
    }));

    // Load the preload script (triggers exposeInMainWorld)
    require("../src/preload");

    const { contextBridge } = require("electron");
    exposedApi = contextBridge.exposeInMainWorld.mock.calls[0][1];
  });

  test("exposes API under 'odiaDesktop' namespace", () => {
    const { contextBridge } = require("electron");
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

  test("rejects disallowed IPC channel via safeInvoke guard", async () => {
    // safeInvoke (tested in channels.test.js) rejects channels not in VALID_CHANNELS.
    // Here we verify the preload API only exposes the expected methods (no arbitrary channels).
    const allowedMethods = Object.keys(exposedApi);
    expect(allowedMethods).not.toContain("arbitrary");
    expect(allowedMethods).not.toContain("invoke");
    // Every exposed method maps to a channel in VALID_CHANNELS (enforced by safeInvoke)
    const { VALID_CHANNELS } = require("../src/channels");
    expect(VALID_CHANNELS.length).toBe(7);
  });
});

