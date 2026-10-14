// Data provider boundary. UI imports from here, never from api.ts or the snapshot directly.
// VITE_DATA_SOURCE=local -> bundled metadata snapshot (a read-only copy of backend papers.json).
// VITE_DATA_SOURCE=api   -> backend for search/recommend/AI. AI is NEVER mocked.
import snapshot from '../data/papers.snapshot.json'
import { api, ApiError } from './api'
import type { AiResult, ChatTurn, Level, Paper } from './types'

export const dataSource: 'api' | 'local' = import.meta.env.VITE_DATA_SOURCE === 'api' ? 'api' : 'local'
export const PAPERS = snapshot.papers as Paper[]
export const byId = (id?: string | null) => PAPERS.find((p) => p.paper_id === id)
export const DOMAINS = [...new Set(PAPERS.map((p) => p.domain))].sort()
export const domainCount = (d: string) => PAPERS.filter((p) => p.domain === d).length
export const YEARS = PAPERS.map((p) => p.year).filter((y): y is number => !!y)
export const YEAR_MIN = Math.min(...YEARS)
export const YEAR_MAX = Math.max(...YEARS)

/** Backend GET /papers is a metadata substring match, not semantic search, and returns [] for an empty query. */
export async function searchPapers(query: string, signal?: AbortSignal): Promise<Paper[]> {
  const q = query.trim().toLowerCase()
  if (!q) return PAPERS // backend has no list-all endpoint; browse from the snapshot
  if (dataSource === 'api') return api.searchPapers(q, 'all', signal)
  return PAPERS.filter((p) => [p.title, p.domain, String(p.year ?? ''), ...p.authors].join(' ').toLowerCase().includes(q))
}

export async function recommended(domains: string[], limit = 4): Promise<Paper[]> {
  const pool = domains.length ? domains : DOMAINS
  if (dataSource === 'api') {
    try {
      const lists = await Promise.all(pool.map((d) => api.recommend({ domain: d, limit })))
      const titles = new Set(lists.flat().map((r) => r.title))
      return PAPERS.filter((p) => titles.has(p.title)).slice(0, limit)
    } catch { /* fall through to local */ }
  }
  return PAPERS.filter((p) => pool.includes(p.domain)).sort((a, b) => (b.year ?? 0) - (a.year ?? 0)).slice(0, limit)
}

const notConnected = () => new ApiError('The AI backend is not connected in this build. Set VITE_DATA_SOURCE=api and point VITE_API_BASE_URL at the FastAPI server (Step 3).')
export const ai = {
  explain: async (q: string, id: string, level: Level, history: ChatTurn[]): Promise<AiResult> => {
    if (dataSource !== 'api') throw notConnected()
    return api.explain(q, id, level, history)
  },
  summarize: async (id: string, focus?: string): Promise<AiResult> => {
    if (dataSource !== 'api') throw notConnected()
    return api.summarize(id, focus)
  },
}

export function identifiers(p: Paper) {
  const out: { label: string; value: string }[] = [{ label: 'ID', value: p.paper_id }]
  const ax = p.url?.match(/arxiv\.org\/abs\/([\w.\/-]+)/i)?.[1] ?? p.doi?.match(/arxiv\.([\d.]+)/i)?.[1]
  if (ax) out.push({ label: 'arXiv', value: ax })
  if (p.doi) out.push({ label: 'DOI', value: p.doi.replace(/^https?:\/\/doi\.org\//, '') })
  return out
}
export const originalUrl = (p: Paper) => p.url || p.doi || null
export const authorLine = (p: Paper, n = 3) =>
  p.authors.length === 0 ? 'Authors not listed' : p.authors.slice(0, n).join(', ') + (p.authors.length > n ? ` +${p.authors.length - n} more` : '')
