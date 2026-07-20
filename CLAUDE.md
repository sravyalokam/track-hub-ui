# Track Hub — Frontend

Personal, solo-use work tracker: log daily work items, learnings, and
appreciations/kudos. This is the frontend half; `track-hub-backend`
(separate repo, sibling directory) is the FastAPI + Postgres API it's
meant to eventually replace `localStorage` with.

## Current state

**Still frontend-only.** Entries are kept in React state and persisted to
`localStorage` under the key `track-hub:entries`. The backend exists as a
standalone, working API (`GET/POST/DELETE /api/entries`) but nothing here
calls it yet — wiring the frontend to the real API is future work, not
done.

## Stack

- React + TypeScript + Vite
- Tailwind CSS (v4, via `@tailwindcss/vite` — no separate postcss config)
- No routing, no state library — everything is local `useState` +
  `useLocalStorage`

## Structure

- `src/types.ts` — the `Entry` type (`id`, `type`, `content`, `createdAt`)
  and `EntryType` union (`'Work' | 'Learning' | 'Appreciation'`)
- `src/hooks/useLocalStorage.ts` — generic localStorage-synced state hook
- `src/entryTypeStyles.ts` — single source of truth for per-type badge
  colors/labels (`Work`/`Learning`/`Appreciation`) — add a new entry type
  here, not by hardcoding colors in components
- `src/components/` — `EntryForm`, `FilterTabs`, `EntryList`/`EntryItem`
- `src/App.tsx` — wires state + components together

## Commands

- `npm run dev` — dev server at `http://localhost:5173`
- `npm run build` — typecheck (`tsc -b`) + production build
- `npm run lint` — ESLint
- `npm run preview` — preview the production build

**No test suite is configured yet.** If a skill/hook asks to "run the full
test suite," there isn't one — say so explicitly rather than assuming a
command exists.

## Conventions

- No comments unless the *why* is genuinely non-obvious — see the existing
  components for the level of terseness expected.
- Don't add a component-level abstraction for something used in one place.
- Keep entry-type-specific styling centralized in `entryTypeStyles.ts`
  rather than scattered `if (type === ...)` branches in components.

## Git / GitHub workflow

Governed by the device-wide `github-workflow` skill
(`~/.claude/skills/github-workflow/`) — branch model is
`feature → dev → qa → uat → main`, Conventional Commits, no Claude/Anthropic
attribution in commit messages. See that skill for the full rules; don't
duplicate them here.
