import { useEffect, useRef, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, Bookmark, BookmarkCheck, ExternalLink, Info, Loader2, Moon, Sun, RotateCcw } from 'lucide-react'
import { useTheme } from '../lib/hooks'
import { useStore } from '../lib/store'
import { authorLine, identifiers, originalUrl } from '../lib/provider'
import type { Paper, Source } from '../lib/types'

export const Logo = ({ to = '/' }: { to?: string }) => (
  <Link to={to} className="logo" aria-label="ScholarSpace home">
    <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="var(--primary)" /><path d="M9 21c0-3 2-4 5-4s5-1 5-4-2-4-5-4" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" /><circle cx="22.5" cy="22" r="2.2" fill="#c9c0ff" /></svg>
    <span>ScholarSpace</span>
  </Link>
)

export function ThemeToggle() {
  const { toggle, isDark } = useTheme()
  return <button className="icon-btn" onClick={toggle} aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'} title="Toggle theme">{isDark ? <Sun size={18} /> : <Moon size={18} />}</button>
}

export const Tag = ({ children, tone }: { children: ReactNode; tone?: 'ai' | 'warn' }) => <span className={`tag ${tone ?? ''}`}>{children}</span>

export const Notice = ({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'warn' }) => (
  <div className={`notice ${tone}`} role="note"><Info size={16} aria-hidden="true" /><div>{children}</div></div>
)

export const ErrorBox = ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
  <div className="error-box" role="alert"><AlertTriangle size={18} aria-hidden="true" /><div><strong>Something went wrong</strong><p>{message}</p></div>
    {onRetry && <button className="btn sm" onClick={onRetry}><RotateCcw size={14} /> Retry</button>}</div>
)

export const Empty = ({ icon, title, children, action }: { icon: ReactNode; title: string; children?: ReactNode; action?: ReactNode }) => (
  <div className="empty"><div className="empty-ic" aria-hidden="true">{icon}</div><h3>{title}</h3>{children && <p>{children}</p>}{action}</div>
)

export const Skeleton = ({ h = 16, w = '100%' }: { h?: number; w?: string }) => <span className="skeleton" style={{ height: h, width: w }} aria-hidden="true" />
export const CardSkeletons = ({ n = 4 }: { n?: number }) => (
  <div className="grid-papers" role="status" aria-label="Loading papers">{Array.from({ length: n }, (_, i) => (
    <div className="paper-card" key={i}><Skeleton h={14} w="30%" /><Skeleton h={20} /><Skeleton h={20} w="70%" /><Skeleton h={14} w="50%" /></div>))}</div>
)
export const Spinner = () => <Loader2 className="spin" size={16} aria-hidden="true" />

export function Dialog({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const d = ref.current; if (!d) return; if (open && !d.open) d.showModal(); if (!open && d.open) d.close() }, [open])
  return (
    <dialog ref={ref} className="dialog" onClose={onClose} onClick={(e) => e.target === ref.current && onClose()} aria-labelledby="dlg-title">
      <div className="dialog-body"><h2 id="dlg-title">{title}</h2>{children}</div>
    </dialog>
  )
}

export function BookmarkButton({ id, label = true }: { id: string; label?: boolean }) {
  const { isSaved, toggleSave } = useStore(); const s = isSaved(id)
  return <button className={`btn ${label ? '' : 'icon-btn'} ${s ? 'saved' : ''}`} aria-pressed={s} aria-label={s ? 'Remove from library' : 'Save to library'} onClick={() => toggleSave(id)}>
    {s ? <BookmarkCheck size={17} /> : <Bookmark size={17} />}{label && (s ? 'Saved' : 'Save to Library')}</button>
}

export function PaperCard({ p, actions }: { p: Paper; actions?: ReactNode }) {
  const ids = identifiers(p).filter((i) => i.label !== 'ID')
  return (
    <article className="paper-card">
      <div className="pc-top"><Tag>{p.domain}</Tag><span className="muted sm">{p.year ?? 'Year n/a'}</span><span className="grow" /><BookmarkButton id={p.paper_id} label={false} /></div>
      <h3><Link to={`/app/papers/${p.paper_id}`}>{p.title}</Link></h3>
      <p className="muted sm">{authorLine(p)}</p>
      <p className="ids">{[p.paper_id, ...ids.map((i) => `${i.label} ${i.value}`)].join(' · ')}</p>
      <div className="pc-actions">
        <Link className="btn sm" to={`/app/papers/${p.paper_id}`}>Details</Link>
        <Link className="btn sm ghost" to={`/app/assistant?paper=${p.paper_id}`}>Ask AI</Link>
        {originalUrl(p) && <a className="btn sm ghost" href={originalUrl(p)!} target="_blank" rel="noreferrer noopener">Original <ExternalLink size={13} /></a>}
        {actions}
      </div>
    </article>
  )
}

/** Minimal safe renderer for model output: paragraphs, lists, headings, **bold**, and [Source N] chips. No HTML injection. */
export function Prose({ text, sources, onCite }: { text: string; sources: Source[]; onCite: (s: Source) => void }) {
  const inline = (s: string, key: string) => s.split(/(\*\*[^*]+\*\*|\[Source \d+\])/g).map((part, i) => {
    const b = part.match(/^\*\*(.+)\*\*$/); if (b) return <strong key={key + i}>{b[1]}</strong>
    const c = part.match(/^\[Source (\d+)\]$/); const src = c && sources.find((x) => x.source === +c[1])
    if (src) return <button key={key + i} className="cite" onClick={() => onCite(src)} aria-label={`Source ${src.source}, page ${src.page}`}>{src.source}</button>
    return part
  })
  const blocks = text.trim().split(/\n{2,}/)
  return <div className="prose">{blocks.map((blk, bi) => {
    const lines = blk.split('\n')
    if (lines.every((l) => /^\s*([-*•]|\d+\.)\s+/.test(l))) {
      const ol = /^\s*\d+\./.test(lines[0]); const L = ol ? 'ol' : 'ul'
      return <L key={bi}>{lines.map((l, li) => <li key={li}>{inline(l.replace(/^\s*([-*•]|\d+\.)\s+/, ''), `${bi}-${li}`)}</li>)}</L>
    }
    const h = blk.match(/^#{1,4}\s+(.+)/); if (h) return <h4 key={bi}>{inline(h[1], String(bi))}</h4>
    return <p key={bi}>{lines.map((l, li) => <span key={li}>{li > 0 && <br />}{inline(l, `${bi}-${li}`)}</span>)}</p>
  })}</div>
}

export const SourceChips = ({ sources, onCite }: { sources: Source[]; onCite: (s: Source) => void }) => sources.length === 0 ? null : (
  <div className="sources" aria-label="Sources"><span className="muted sm">Sources</span>
    {sources.map((s) => <button key={s.source} className="chip" onClick={() => onCite(s)}><b>{s.source}</b> {s.paper_id} · {s.page === 'Unknown' ? 'page n/a' : `p. ${s.page}`}</button>)}</div>
)

export const PageHead = ({ title, sub, right }: { title: string; sub?: ReactNode; right?: ReactNode }) => (
  <header className="page-head"><div><h1>{title}</h1>{sub && <p className="muted">{sub}</p>}</div>{right}</header>
)
