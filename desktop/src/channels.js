"use strict";

const { ipcRenderer } = require("electron");

/**
 * Exhaustive allowlist of IPC channels the renderer may invoke.
 * safeInvoke enforces this at runtime to prevent arbitrary IPC calls.
 * @type {string[]}
 */
const VALID_CHANNELS = [
  "dialog:open-file",
  "dialog:save-file",
  "backend:health",
  "backend:analyze",
  "backend:status",
  "app:version",
  "shell:open-external",
];

/**
 * Invoke an IPC channel after validating it against the allowlist.
 * Returns a rejected promise for any channel not in VALID_CHANNELS.
 * @param {string} channel
 * @param {...any} args
 * @returns {Promise<any>}
 */
function safeInvoke(channel, ...args) {
  if (!VALID_CHANNELS.includes(channel)) {
    return Promise.reject(new Error(`IPC channel not allowed: ${channel}`));
  }
  return ipcRenderer.invoke(channel, ...args);
}

module.exports = { VALID_CHANNELS, safeInvoke };
