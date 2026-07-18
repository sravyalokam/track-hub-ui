# Track Hub

A personal, solo-use tracker for logging daily work items, learnings, and appreciations/kudos received.

Frontend-only scaffold — no backend, no API calls. Entries are kept in React state and persisted to `localStorage`, so refreshing the page doesn't lose data.

## Stack

- React + TypeScript + Vite
- Tailwind CSS

## Setup

Install dependencies:

```bash
npm install
```

## Run

Start the dev server:

```bash
npm run dev
```

Then open the URL printed in the terminal (typically http://localhost:5173).

## Other scripts

- `npm run build` — type-check and build for production
- `npm run preview` — preview the production build locally
- `npm run lint` — run ESLint

## Notes

- Data lives entirely in the browser's `localStorage` under the key `track-hub:entries`. Clearing site data / browser storage will erase entries.
- There is no backend, authentication, or sync between devices/browsers by design — this is a solo, local-only scaffold to build on.
