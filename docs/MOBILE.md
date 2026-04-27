# O.D.I.A. — Mobile Platform Guide

This doc covers running O.D.I.A. on mobile devices.

**At v2.9.0 the mobile track ships as a Progressive Web App (PWA).**
That means installable on iOS Safari and Android Chrome via "Add to
Home Screen" — no App Store, no Play Store, no review cycle. The full
PWA inherits everything in the desktop frontend: gemstone palette,
texture system, Manual Triggers panel, RAIA synthesis, evidence packet
export.

Native iOS + Android via Capacitor (App Store + Play Store
distribution) is **deferred to v2.9.1+** pending operator decisions on
Apple Developer Program ($99/year) and Google Play Console ($25
one-time) accounts. The architecture supports it; the handoff
document is staged at `docs/handoffs/CLAUDE_CODE_HANDOFF_v2_9_0_mobile.md`
when the user is ready to escalate.

---

## Platform matrix

| Platform | Distribution | What works | What doesn't | Required infra |
|---|---|---|---|---|
| **Web** | URL | Everything except camera-as-default + biometric | Camera capture requires `capture="environment"` (works on phones) | Backend reachable |
| **PWA (this doc)** | "Add to Home Screen" | Everything Web does + offline shell + home-screen icon + splash | No App Store reach, no push notifications | Backend reachable |
| **Docker** | Self-hosted container | Everything | n/a | Docker host |
| **Electron** | Native installer (Win / macOS / Linux) | Everything + bundled Python backend (no separate hosting) | iOS / Android | Local file:// install |
| **Native iOS / Android** (deferred to v2.9.1+) | App Store / Play Store | Above + native camera + GPS + biometric + filesystem cache + push | n/a | Apple Developer + Google Play accounts |

---

## Installing the PWA

### iOS (Safari)

1. Open Safari and navigate to your O.D.I.A. instance (e.g.
   `https://odia.example.com` or whatever URL your backend serves).
2. Wait for the dashboard to load. The first visit shows a one-line
   tip near the bottom of the screen: *"Tap Share → Add to Home Screen
   to install."*
3. Tap the **Share** icon (square with up-arrow) at the bottom of
   Safari.
4. Scroll down in the share sheet and tap **Add to Home Screen**.
5. Confirm the name (`O.D.I.A.`) and tap **Add**.
6. The app appears on your home screen with the gold-swirl icon.
7. Launch from the home screen — it opens fullscreen in standalone
   mode (no Safari chrome).

iOS Safari does not fire `beforeinstallprompt`, so the in-app prompt
is informational only. The actual install happens through Safari's
share sheet.

### Android (Chrome / Edge / Samsung Internet)

1. Open Chrome and navigate to your O.D.I.A. instance.
2. Wait for the dashboard to load. Chrome detects PWA-eligibility and
   the in-app HUD pill appears at the bottom of the screen:
   *"Install O.D.I.A. on this device →"*.
3. Tap the pill, then tap **Install** in the resulting prompt.
4. The app appears in your launcher with the gold-swirl icon (Android
   adaptive-icon mask gets the maskable variant).
5. Launch from the launcher — it opens fullscreen in standalone mode.

If you don't see the install pill, verify:
- The page is served over HTTPS (PWA installation requires it on
  Android).
- The `manifest.json` is reachable at `/manifest.json` (returns 200).
- The service worker registers correctly (DevTools → Application →
  Service Workers).

### Desktop browsers (Chromium-based)

Chrome / Edge / Brave / Opera / Arc all support PWA install. Look for
the install icon in the URL bar (a small monitor with a down-arrow,
or three vertical dots → "Install O.D.I.A.").

Firefox does not implement the install prompt API but will render the
PWA correctly as a normal tab.

---

## Mobile-specific UI

The Next.js frontend has been mobile-aware since Sprint E (2026-03):

| Feature | Behaviour |
|---|---|
| **Sidebar** | Hidden on `<md:` (768px). Top bar collapses to a single chrome line. |
| **Bottom tab bar** | Replaces the sidebar on mobile. Five tabs: Home, Upload, Results, Documents, Settings. |
| **Hero panels** | Texture variants at `<md:` viewport substitute the smaller `-mobile.webp` files (~30 KB each instead of ~80 KB). |
| **Upload table** | Replaced with a card layout on `<md:` (v2.9.0 B1) — name + format on row 1, size + truncated SHA on row 2, full-width Remove button on row 3. Touch-target is 44px high. |
| **Pull-to-refresh** | Documents, Results, and Anomalies pages support native-feel pull-to-refresh on touch devices (v2.9.0 B3). |
| **Camera capture** | Upload page's "From Camera" button uses `<input type="file" accept="image/*" capture="environment">` so phones open the rear camera directly. |
| **Touch targets** | Every interactive element (button, link, tab) is at least 44px high (iOS HIG) / 48dp (Material Design). The `Button` component enforces this via the `size="md"` default (v2.9.0 B2). |
| **Install prompt** | Auto-shows on first visit per platform (v2.9.0 B5). Suppresses when running in standalone mode. |

---

## Build commands

```bash
# Standard web build (Docker / hosted PWA)
cd frontend && npm run build

# Electron desktop bundle
cd frontend && ELECTRON_BUILD=1 npm run build
cd ../desktop && npm run build:win    # or build:mac / build:linux

# Mobile native bundle (deferred to v2.9.1+)
# cd frontend && CAPACITOR_BUILD=1 npm run build && npx cap sync
# cd ../frontend && npx cap run ios
# cd ../frontend && npx cap run android
```

The PWA install path uses the standard web build — no special command.
Whatever URL you serve the build from is the PWA's home base.

---

## Backend deployment requirement

O.D.I.A. is a **thin client**: the frontend is Next.js, all detectors
and analysis logic live in the Python backend. The mobile app cannot
function offline beyond the cached app shell — it needs to reach the
backend at `/api/v1/*` for every audit operation.

Three deployment options for the backend:

| Option | Audience | Cost | Trade-off |
|---|---|---|---|
| **Self-hosted via Docker** | Privacy-first operators, technical users | Server cost only | Operator must run + maintain the container |
| **Hosted by SynTechRev** (planned) | Casual / non-technical users | TBD | Documents pass through SynTechRev infrastructure |
| **Hosted by your organization** | Newsroom, advocacy org, oversight body | Server cost + ops time | Documents stay inside org boundary |

The mobile PWA points at whichever backend URL is configured in
`NEXT_PUBLIC_API_URL` at build time, or stored under
`localStorage['odia.apiBaseURL']` at runtime (Settings page allows
the user to override). Self-hosted users can run the backend on a
VPS or Raspberry Pi at home and tunnel via Tailscale or Cloudflare
Tunnel.

---

## Service worker behaviour on mobile

The service worker (`frontend/public/sw.js`, cache name `odia-shell-v4`
at v2.9.0) handles offline behaviour for the PWA. It does **not**
intercept iOS Safari's WebView for the native Capacitor build (when
that ships) — Capacitor uses native HTTP, not the SW.

| Cache | What | Strategy |
|---|---|---|
| `odia-shell-v4` | App shell (HTML, root pages) + intro asset | Cache-first; pre-cached on install |
| `odia-static-v1` (v2.9.0 B4) | `/_next/static/*`, `/icons/*`, `/textures/*` | Cache-first runtime, stale-while-revalidate |
| **Never cached** | `/api/*`, `/api/uploads/*`, anything POST | Privacy: documents and audit results never enter the SW cache |

When the user goes offline mid-session, navigation falls back to the
cached app shell. Pages that need backend data (Dashboard summary,
Results, Anomalies) show a clearly-marked offline state rather than a
broken empty-data render.

---

## Known PWA limitations

- **No push notifications.** The Web Push API works on Android but
  not on iOS Safari (Apple permits push only for App Store apps and
  Web Push registration in standalone-mode PWAs from iOS 16.4 onward;
  the registration flow + APNs backend wiring is operator work
  deferred to the Capacitor track).
- **No background fetch / sync.** PWAs cannot run audits on a
  schedule. For scheduled audits, run the n8n stack (see
  [docs/AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)).
- **No deep file system access.** The PWA can read files the user
  picks via the file picker but cannot scan a folder. For batch
  ingestion, use the Upload page's multi-select or the Legistar
  retrieval flow.
- **Camera permission resets on each visit (iOS).** Safari does not
  persist camera permission for PWAs across cold launches. Users
  re-prompt every time.

The Capacitor track (deferred) addresses each of these by routing
through the native runtime.

---

## Path forward

If the basic PWA experience is sufficient, **stay on v2.9.0**. It runs
on every modern mobile browser, installs to the home screen, works
offline for cached pages, and shares the codebase with desktop +
Electron 1:1.

If you need **native camera-as-default, native filesystem caching,
biometric workspace lock, native share sheet integration, or push
notifications**, the Capacitor track unlocks those. Trigger the
v2.9.1 mobile-track handoff (`docs/handoffs/CLAUDE_CODE_HANDOFF_v2_9_0_mobile.md`)
when ready. Native distribution requires:

- **Apple Developer Program** account ($99/year)
- **Google Play Console** account ($25 one-time)
- Signing certificates (Apple keychain + Android keystore)
- Privacy nutrition label / data safety questionnaires
- Screenshots (5 per platform per device class)

The CI pipeline (Track C7 of the deferred handoff) builds unsigned
artifacts you can install on personal devices via `xcodebuild` /
`adb install` without store accounts. Those provide the same native
runtime the store distribution does, just without store discovery.

---

## Troubleshooting

### "Add to Home Screen" doesn't appear in iOS Safari

- Confirm the page is served over HTTPS (a non-HTTPS page is not PWA-
  eligible on iOS).
- Confirm `manifest.json` is reachable: `curl -I https://your-
  instance/manifest.json` should return 200.

### Install pill never shows on Android Chrome

The `beforeinstallprompt` event only fires after Chrome's heuristics
decide the page is install-worthy (typically after a few seconds of
interaction). Reload, scroll, click a sidebar entry — the event
should fire within 30 seconds.

You can also manually trigger install via Chrome's three-dot menu →
"Install app" or "Add to Home screen".

### Pages render but `/api/*` calls 404 on the installed PWA

The PWA captures the URL at install time. If you installed before
deploying the backend, the PWA points at a stale URL. Uninstall and
reinstall, or update `NEXT_PUBLIC_API_URL` and rebuild.

### Hero panel textures don't show

Confirm `frontend/public/textures/` is deployed and reachable:

```bash
curl -I https://your-instance/textures/texture-malachite-bg.webp
```

Should return 200 with `Content-Type: image/webp`. If 404, your build
output is missing the textures directory. Rebuild and redeploy.

For Electron file:// installs, the TextureResolver client component
(v2.8.1) handles the leading-slash → file:// rewrite at runtime — no
manual config needed.

---

## See also

- [QUICKSTART.md](../QUICKSTART.md) — desktop / web operator workflow
- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) — n8n + Docker stack for
  scheduled audits + push-equivalent alerts via webhook
- [BRAND.md](BRAND.md) — visual identity reference (palette + texture
  system locked at v2.8.0)
- The deferred Capacitor track handoff lives at the local path
  `C:\Users\yahua\Downloads\v2.8.1_Updates\CLAUDE_CODE_HANDOFF_v2_9_0_mobile.md`
  — invoke that when ready to escalate to App Store / Play Store
  distribution.
