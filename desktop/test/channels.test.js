"use strict";

/**
 * Tests for channels.js — VALID_CHANNELS allowlist and safeInvoke guard.
 */

const mockInvoke = jest.fn(() => Promise.resolve("ok"));

jest.mock("electron", () => ({
  ipcRenderer: {
    invoke: mockInvoke,
  },
}));

const { VALID_CHANNELS, safeInvoke } = require("../src/channels");

describe("channels", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("VALID_CHANNELS", () => {
    test("contains all expected channels", () => {
      expect(VALID_CHANNELS).toContain("dialog:open-file");
      expect(VALID_CHANNELS).toContain("dialog:save-file");
      expect(VALID_CHANNELS).toContain("backend:health");
      expect(VALID_CHANNELS).toContain("backend:analyze");
      expect(VALID_CHANNELS).toContain("backend:status");
      expect(VALID_CHANNELS).toContain("app:version");
      expect(VALID_CHANNELS).toContain("shell:open-external");
    });

    test("has exactly 7 channels", () => {
      expect(VALID_CHANNELS).toHaveLength(7);
    });
  });

  describe("safeInvoke", () => {
    test("calls ipcRenderer.invoke for valid channel", async () => {
      await safeInvoke("backend:health");
      expect(mockInvoke).toHaveBeenCalledWith("backend:health");
    });

    test("passes additional arguments to ipcRenderer.invoke", async () => {
      const payload = { documentText: "test" };
      await safeInvoke("backend:analyze", payload);
      expect(mockInvoke).toHaveBeenCalledWith("backend:analyze", payload);
    });

    test("rejects with error for disallowed channel", async () => {
      await expect(safeInvoke("arbitrary:channel")).rejects.toThrow(
        "IPC channel not allowed: arbitrary:channel"
      );
      expect(mockInvoke).not.toHaveBeenCalled();
    });

    test("rejects for empty string channel", async () => {
      await expect(safeInvoke("")).rejects.toThrow("IPC channel not allowed:");
      expect(mockInvoke).not.toHaveBeenCalled();
    });

    test("rejects for channel with extra suffix", async () => {
      await expect(safeInvoke("backend:health:extra")).rejects.toThrow(
        "IPC channel not allowed"
      );
      expect(mockInvoke).not.toHaveBeenCalled();
    });

    test("allows all 7 valid channels without throwing", async () => {
      for (const channel of VALID_CHANNELS) {
        await expect(safeInvoke(channel)).resolves.toBe("ok");
      }
    });
  });
});
