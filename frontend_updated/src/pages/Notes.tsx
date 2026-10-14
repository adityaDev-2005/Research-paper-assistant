import { useState } from 'react'
import { NotebookPen, Plus, Search, Trash2 } from 'lucide-react'
import { Dialog, Empty, Notice, PageHead } from '../components/ui'
import { PAPERS, byId } from '../lib/provider'
import { useStore, type Note } from '../lib/store'

const blank = (): Note => ({ id: crypto.randomUUID(), title: '', body: '', paperId: null, tags: [], updated: Date.now() })

export default function Notes() {
  const { notes, saveNote, deleteNote } = useStore(); const [q, setQ] = useState(''); const [cur, setCur] = useState<Note | null>(null); const [del, setDel] = useState<Note | null>(null)
  const list = notes.filter((n) => !q || [n.title, n.body, n.tags.join(' '), byId(n.paperId)?.title ?? ''].join(' ').toLowerCase().includes(q.toLowerCase()))
  const commit = (n: Note) => { const x = { ...n, updated: Date.now() }; setCur(x); if (x.title || x.body) saveNote(x) }
  return (
    <>
      <PageHead title="Notes & Highlights" right={<button className="btn primary" onClick={() => setCur(blank())}><Plus size={16} /> New note</button>} />
      <Notice>These are notes linked to papers. PDF text highlighting and annotation are not implemented. Notes are stored in this browser only.</Notice>
      <div className="notes">
        <aside className="notes-list"><label className="field"><span className="sr">Search notes</span><span className="input-ic"><Search size={16} aria-hidden="true" /><input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search notes or tags" /></span></label>
          {list.length === 0 ? <Empty icon={<NotebookPen />} title={notes.length ? 'No matches' : 'No notes yet'}>{notes.length ? 'Try another search.' : 'Create a note and link it to a paper.'}</Empty> :
            <ul>{list.map((n) => <li key={n.id}><button className={`note-item ${cur?.id === n.id ? 'on' : ''}`} onClick={() => setCur(n)}><strong>{n.title || 'Untitled note'}</strong><span className="muted sm">{byId(n.paperId)?.paper_id ?? 'No paper'} · {new Date(n.updated).toLocaleDateString()}</span></button></li>)}</ul>}</aside>
        <section className="note-editor">{!cur ? <Empty icon={<NotebookPen />} title="Select or create a note" /> : (<>
          <label className="field"><span>Title</span><input value={cur.title} onChange={(e) => commit({ ...cur, title: e.target.value })} /></label>
          <label className="field"><span>Linked paper</span><select value={cur.paperId ?? ''} onChange={(e) => commit({ ...cur, paperId: e.target.value || null })}><option value="">None</option>{PAPERS.map((p) => <option key={p.paper_id} value={p.paper_id}>{p.paper_id} · {p.title}</option>)}</select></label>
          <label className="field"><span>Tags (comma separated)</span><input value={cur.tags.join(', ')} onChange={(e) => commit({ ...cur, tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean) })} /></label>
          <label className="field"><span>Note</span><textarea rows={12} value={cur.body} onChange={(e) => commit({ ...cur, body: e.target.value })} /></label>
          {notes.some((n) => n.id === cur.id) && <button className="btn danger" onClick={() => setDel(cur)}><Trash2 size={15} /> Delete note</button>}</>)}</section>
      </div>
      <Dialog open={!!del} onClose={() => setDel(null)} title="Delete this note?"><p className="muted">“{del?.title || 'Untitled note'}” will be removed from this browser. This cannot be undone.</p>
        <div className="row gap"><button className="btn danger" onClick={() => { deleteNote(del!.id); if (cur?.id === del!.id) setCur(null); setDel(null) }}>Delete</button><button className="btn" onClick={() => setDel(null)}>Cancel</button></div></Dialog>
    </>
  )
}
