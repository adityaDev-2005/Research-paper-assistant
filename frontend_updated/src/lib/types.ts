export type Level = 'beginner' | 'intermediate' | 'expert'

/** Shape of backend GET /papers items (retrieval/paper_search.py). The metadata has no abstract/keywords. */
export interface Paper {
  paper_id: string
  title: string
  domain: string
  authors: string[]
  year: number | null
  doi: string | null
  url: string | null
  source?: string | null
  pdf_available?: boolean
}
/** Backend citation: only source number, paper id and page. No passage text is returned. */
export interface Source { source: number; paper_id: string; page: string | number }
export interface AiResult { text: string; sources: Source[] }
export interface ChatTurn { role: 'user' | 'assistant'; content: string }
