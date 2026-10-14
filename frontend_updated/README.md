# ScholarSpace Frontend (Step 1)

React + TypeScript + Vite single-page app for the ScholarSpace backend
(`adityaDev-2005/Research-paper-assistant`). Place this folder at `frontend/` in that repo; no backend file is touched.

## Run
```bash
cp .env.example .env
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production bundle (verified passing)
```
`npm run sync:papers` regenerates `src/data/papers.snapshot.json` from `../data/metadata/papers.json` (read-only).

## Structure
```
src/
  lib/api.ts        centralised backend client, validation, timeouts, typed errors
  lib/provider.ts   the ONLY data boundary the UI uses (local snapshot vs api)
  lib/store.tsx     prototype state (localStorage): prefs, library, notes, recents
  lib/hooks.tsx     theme, reveal-on-scroll, localStorage, debounce
  auth/auth.tsx     Step 2 boundary: AuthState interface, stub, RequireAuth, postSignInRoute
  components/       ui.tsx (shared), Shell.tsx (workspace layout)
  pages/            Landing, Auth, Onboarding, Overview, Discover, PaperDetail, Assistant, Library, Notes, Settings
  styles.css        design tokens (light/dark) + all styles
  data/             papers.snapshot.json (read-only copy of backend papers.json)
```

## Backend contracts (verified from `app/main.py`)
| Endpoint | Request | Response |
|---|---|---|
| `GET /papers` | `query` (<=200), `field` = all/title/author/year/domain/keyword | `{query, field, count, papers[{paper_id,title,domain,authors,year,doi,url,pdf_filename,pdf_path,pdf_available}]}` |
| `POST /ask` | `{question, paper_id}` | `{question, paper_id, answer, sources[{source,paper_id,page}]}` |
| `POST /summarize` | `{paper_id, focus?}` | `{paper_id, focus, summary, sources[]}` |
| `POST /explain` | `{question, paper_id, level, history[<=10 turns]}` | `{paper_id, question, level, answer, sources[]}` |
| `GET /recommend` | `domain, year_from, year_to, limit` | `{recommendations[], count}` (no `paper_id`; matched by title) |

## Auth & onboarding flow
Implemented routing (inactive until a real session exists, because sign-in is a stub):
- First sign-in -> `/onboarding` (reading level + interests) -> saved -> `/app`.
- Returning user who finished onboarding -> `/app`. Signed-in user who hasn't finished onboarding -> `/onboarding`.
- `VITE_AUTH_GUARD=on` enforces this (signed-out -> `/signin`). Default `off` so pages stay reachable by URL during development.

Still to implement (Step 2): Google OAuth + session in `src/auth/auth.tsx` (`AuthProvider`), and persistent per-user profile storage behind `profileStorage`
(the backend has no auth or profile endpoints). Until then preferences and the "onboarding completed" flag are browser localStorage only, not tied to an account.

## Step 3 (connect backend)
1. `.env`: `VITE_DATA_SOURCE=api`. Dev requests go to `/api`, proxied by Vite to `VITE_PROXY_TARGET`.
2. **Production needs CORS**: `app/main.py` has no `CORSMiddleware`. Add one (or serve behind a reverse proxy).
3. Run Ollama + Chroma index so `/ask`, `/explain`, `/summarize` can answer. Generation can be slow; the client waits up to 3 min.

## Implemented
Landing, sign-in/up UI, onboarding, workspace shell (collapsible sidebar, mobile drawer), overview, discover (search/domain/year/sort/reset, URL-synced), paper details, assistant (paper selector, level, chat with history, summarize mode, citation dialog, copy, retry, new conversation), library, notes (create/edit/delete with confirm/search/tags/paper link), settings, light/dark/system theme without flash, reduced-motion support, keyboard/focus/ARIA basics.

## Not implemented / gaps (by design or backend limits)
- **Google OAuth & sessions**: stub only. Sign-in shows a "not available yet" error. Nothing fakes a user.
- **Persistence**: library, notes, recents, preferences are browser localStorage only.
- **AI**: never mocked. In `local` mode the assistant shows a "not connected" error. `/ask` is in the API client but the UI uses `/explain` (supports level + history).
- **Citations**: backend returns source number, paper id and page only, so no passage text is shown. Add passage text to the API to enable it.
- **Abstracts / keywords / methodology**: absent from backend metadata; the UI says so rather than inventing them.
- **No list-all endpoint**: `/papers` returns `[]` for an empty query, so browsing uses the snapshot.
- **Search is substring metadata search**, not semantic; labelled as such.
- **Interests** AI, NLP and RL have no matching `domain` (collection has Computer Vision, Remote Sensing, Machine Learning, Robotics).
- **PDF highlighting**, collections, cross-device sync, automated tests: not built.

## Metadata to double-check (not changed)
- `ML04` "Auto-Encoding Variational Bayes": year 2024 and DOI `10.61603/ceas.v2i1.33` look inconsistent with the well-known 2013 paper.
- `RS09` URL points to a DOAJ record rather than the publisher/DOI.
- `ROB04` lists 100 authors (cards truncate to 3 + count).
