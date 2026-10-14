import { useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink, FileText, MessageSquareText, Sparkles } from 'lucide-react'
import { BookmarkButton, Empty, Notice, Tag } from '../components/ui'
import { byId, identifiers, originalUrl } from '../lib/provider'
import { useStore } from '../lib/store'

export default function PaperDetail() {
  const { id } = useParams(); const p = byId(id); const { touch, notes } = useStore(); const nav = useNavigate()
  useEffect(() => { if (p) touch(p.paper_id) }, [p?.paper_id]) // eslint-disable-line
  if (!p) return <Empty icon={<FileText />} title="Paper not found" action={<Link className="btn" to="/app/discover">Back to Discover</Link>}>No paper with ID “{id}” exists in the collection.</Empty>
  const url = originalUrl(p); const linked = notes.filter((n) => n.paperId === p.paper_id)
  return (
    <article className="detail">
      <button className="btn ghost sm" onClick={() => nav(-1)}><ArrowLeft size={15} /> Back</button>
      <div className="detail-head"><Tag>{p.domain}</Tag><span className="muted">{p.year ?? 'Year n/a'}</span></div>
      <h1>{p.title}</h1>
      <p className="authors">{p.authors.length ? p.authors.join(', ') : 'Authors not listed'}</p>
      <div className="actions">
        {url ? <a className="btn primary" href={url} target="_blank" rel="noreferrer noopener"><ExternalLink size={16} /> Read Original Paper</a> : <button className="btn" disabled>Original link unavailable</button>}
        <Link className="btn" to={`/app/assistant?paper=${p.paper_id}`}><MessageSquareText size={16} /> Ask AI About This Paper</Link>
        <Link className="btn" to={`/app/assistant?paper=${p.paper_id}&mode=summarize`}><Sparkles size={16} /> Summarize Paper</Link>
        <BookmarkButton id={p.paper_id} />
      </div>
      <div className="detail-grid">
        <section><h2 className="h3">Abstract</h2><p className="muted">Not available. The backend metadata does not include abstracts. Use Read Original Paper for the abstract, or ask the assistant.</p>
          <h2 className="h3">AI overview, methodology and contributions</h2><p className="muted">Generated on demand in the assistant from retrieved passages. Nothing is pre-written here.</p>
          <h2 className="h3">Linked notes</h2>{linked.length ? <ul className="plain-list">{linked.map((n) => <li key={n.id}><Link to="/app/notes">{n.title || 'Untitled note'}</Link></li>)}</ul> : <p className="muted">No notes linked to this paper. <Link to="/app/notes">Write one</Link>.</p>}</section>
        <aside className="meta"><h2 className="h3">Details</h2><dl>
          {identifiers(p).map((i) => <div key={i.label}><dt>{i.label}</dt><dd>{i.value}</dd></div>)}
          <div><dt>Year</dt><dd>{p.year ?? 'n/a'}</dd></div><div><dt>Domain</dt><dd>{p.domain}</dd></div><div><dt>Metadata source</dt><dd>{p.source ?? 'n/a'}</dd></div>
          <div><dt>Original URL</dt><dd className="break">{url ?? 'Unavailable until verified'}</dd></div></dl>
          <Notice>Links are as recorded in the backend metadata. The frontend does not independently verify them.</Notice></aside>
      </div>
    </article>
  )
}
