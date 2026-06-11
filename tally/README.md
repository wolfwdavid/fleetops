# Tally

A small mobile-first task tracker. Add what's next, strike it through.
Every task you complete today becomes a tally mark in the header —
groups of five, the fifth stroke drawn through in marigold.

No build step, no dependencies: plain HTML/CSS/JS, installable as a PWA,
works fully offline once loaded.

## Run it

```
cd tally
python -m http.server 8741
```

Open http://localhost:8741 (phone-sized window or device emulation looks best).

## Install on your phone

1. Serve the folder over HTTPS or your LAN (e.g. `python -m http.server` and
   visit `http://<your-pc-ip>:8741` from the phone — note: service workers
   require HTTPS or localhost, so for full offline install use a tunnel like
   `npx serve` + ngrok, or any static host such as GitHub Pages / Vercel).
2. In the browser menu choose **Add to Home Screen** / **Install app**.
3. It launches standalone, themed, and offline-capable.

## Features

- Add / complete / delete tasks; swipe a row left to delete on touch
- All / Active / Done filters
- Animated strike-through on complete; tally-mark count of strikes made today
  (strikes survive deleting the task — the tally records the work, not the row)
- Tasks persist in `localStorage`; tally resets each day
- Offline via service worker (`sw.js`); bump `CACHE` in `sw.js` when you
  change files so installed clients pick up the update

## Files

- `index.html` / `styles.css` / `app.js` — the whole app
- `manifest.webmanifest` + `icons/` — install metadata (icons are generated,
  a five-tally on ink)
- `sw.js` — cache-first offline shell
