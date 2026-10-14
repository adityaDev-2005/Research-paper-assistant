// Centralised client for the FastAPI backend. Contracts verified against app/main.py.
import type { AiResult, ChatTurn, Level, Paper, Source } from './types'

export const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string) || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message: string, public status?: number, public retryable = false) { super(message) }
}
const isObj = (x: unknown): x is Record<string, any> => typeof x === 'object' && x !== null

async function request<T>(path: string, parse: (x: unknown) => T, o: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort('timeout'), 180_000) // local LLM generation can be slow
  o.signal?.addEventListener('abort', () => ctl.abort())
  let res: Response
  try {
    res = await fetch(API_BASE + path, {
      method: o.method ?? 'GET',
      headers: o.body ? { 'Content-Type': 'application/json' } : undefined,
      body: o.body ? JSON.stringify(o.body) : undefined,
      signal: ctl.signal,
    })
  } catch (e) {
    if (ctl.signal.reason === 'timeout') throw new ApiError('The backend took too long to respond (3 min). The model may still be loading.', undefined, true)
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError(`Cannot reach the API at ${API_BASE}. Check that it is running (and CORS or the dev proxy is set up).`, undefined, true)
  } finally { clearTimeout(timer) }
  let data: unknown = null
  try { data = await res.json() } catch { /* non-JSON body */ }
  if (!res.ok) {
    const d = isObj(data) ? data.detail : null
    const msg = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x: any) => x?.msg).filter(Boolean).join('; ') : `Request failed (${res.status})`
    throw new ApiError(msg, res.status, res.status >= 500)
  }
  try { return parse(data) } catch { throw new ApiError('The API returned an unexpected response shape.', res.status) }
}

const sources = (x: unknown): Source[] =>
  Array.isArray(x) ? x.filter((s) => isObj(s) && typeof s.source === 'number' && typeof s.paper_id === 'string')
    .map((s) => ({ source: s.source, paper_id: s.paper_id, page: s.page ?? 'Unknown' })) : []

const aiParse = (key: 'answer' | 'summary') => (x: unknown): AiResult => {
  if (!isObj(x) || typeof x[key] !== 'string') throw new Error('bad shape')
  return { text: x[key], sources: sources(x.sources) }
}
const papersParse = (x: unknown): Paper[] => {
  if (!isObj(x) || !Array.isArray(x.papers)) throw new Error('bad shape')
  return x.papers.filter((p) => isObj(p) && typeof p.paper_id === 'string' && typeof p.title === 'string') as Paper[]
}

export const api = {
  health: () => request('/', (x) => { if (!isObj(x)) throw 0; return x as { message?: string } }),
  searchPapers: (query: string, field = 'all', signal?: AbortSignal) =>
    request(`/papers?query=${encodeURIComponent(query)}&field=${field}`, papersParse, { signal }),
  ask: (question: string, paper_id: string) => request('/ask', aiParse('answer'), { method: 'POST', body: { question, paper_id } }),
  summarize: (paper_id: string, focus?: string) =>
    request('/summarize', aiParse('summary'), { method: 'POST', body: { paper_id, ...(focus ? { focus } : {}) } }),
  explain: (question: string, paper_id: string, level: Level, history: ChatTurn[]) =>
    request('/explain', aiParse('answer'), { method: 'POST', body: { question, paper_id, level, history: history.slice(-10) } }),
  /** Items have no paper_id; callers match by title. */
  recommend: (p: { domain?: string; year_from?: number; year_to?: number; limit?: number }) => {
    const q = new URLSearchParams(Object.entries(p).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)]))
    return request(`/recommend?${q}`, (x) => {
      if (!isObj(x) || !Array.isArray(x.recommendations)) throw new Error('bad shape')
      return x.recommendations as Partial<Paper>[]
    })
  },
}
