import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Check, Copy, ExternalLink, FileText, Plus, Send, ShieldAlert, Sparkles } from 'lucide-react'
import { Dialog, ErrorBox, Notice, Prose, Spinner, SourceChips, Tag } from '../components/ui'
import { PAPERS, ai, byId, originalUrl } from '../lib/provider'
import { LEVELS, useStore } from '../lib/store'
import type { Level, Source } from '../lib/types'

interface Msg { id: number; role: 'user' | 'assistant'; content: string; sources?: Source[]; error?: string; retry?: string; sample?: boolean }
const SUGGEST = ['What problem does this paper address?', 'What method do the authors propose?', 'What are the main limitations?', 'Explain the key terms I need to know first.']
let uid = 0

export default function Assistant() {
  const [sp, setSp] = useSearchParams(); const { prefs, touch } = useStore()
  const paperId = sp.get('paper') ?? ''; const mode = sp.get('mode') === 'summarize' ? 'summarize' : 'chat'; const paper = byId(paperId)
  const [level, setLevel] = useState<Level>(prefs.level)
  const [msgs, setMsgs] = useState<Msg[]>([]); const [text, setText] = useState(''); const [busy, setBusy] = useState(false)
  const [focus, setFocus] = useState('main contributions and methodology')
  const [sum, setSum] = useState<{ text: string; sources: Source[] } | null>(null); const [sumErr, setSumErr] = useState('')
  const [cite, setCite] = useState<Source | null>(null); const [copied, setCopied] = useState<number | null>(null)
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { if (paper) touch(paper.paper_id); setMsgs([]); setSum(null); setSumErr('') }, [paperId]) // eslint-disable-line
  useEffect(() => { end.current?.scrollIntoView({ block: 'end', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }) }, [msgs, busy])

  const send = async (q: string, base: Msg[] = msgs) => {
    if (!paper || !q.trim() || busy) return
    const user: Msg = { id: ++uid, role: 'user', content: q.trim() }
    const history = base.filter((m) => !m.error && !m.sample).map(({ role, content }) => ({ role, content }))
    setMsgs([...base, user]); setText(''); setBusy(true)
    try {
      const r = await ai.explain(q.trim(), paper.paper_id, level, history)
      setMsgs((m) => [...m, { id: ++uid, role: 'assistant', content: r.text, sources: r.sources }])
    } catch (e) { setMsgs((m) => [...m, { id: ++uid, role: 'assistant', content: '', error: (e as Error).message, retry: q.trim() }]) }
    finally { setBusy(false) }
  }
  const summarize = async () => {
    if (!paper) return; setBusy(true); setSumErr(''); setSum(null)
    try { setSum(await ai.summarize(paper.paper_id, focus.trim() || undefined)) } catch (e) { setSumErr((e as Error).message) } finally { setBusy(false) }
  }
  const copy = async (m: Msg) => { try { await navigator.clipboard.writeText(m.content); setCopied(m.id); setTimeout(() => setCopied(null), 1500) } catch { /* clipboard blocked */ } }
  const citeInfo = cite && byId(cite.paper_id)

  return (
    <div className="assistant">
      <header className="as-head">
        <div className="as-paper"><FileText size={18} aria-hidden="true" />
          <label className="field"><span className="sr">Paper</span>
            <select value={paperId} onChange={(e) => setSp({ paper: e.target.value, ...(mode === 'summarize' ? { mode } : {}) })}>
              <option value="">Select a paper…</option>{PAPERS.map((p) => <option key={p.paper_id} value={p.paper_id}>{p.paper_id} · {p.title}</option>)}</select></label></div>
        <div className="seg" role="group" aria-label="Mode">
          {(['chat', 'summarize'] as const).map((m) => <button key={m} aria-pressed={mode === m} className={mode === m ? 'on' : ''} onClick={() => setSp({ ...(paperId ? { paper: paperId } : {}), ...(m === 'summarize' ? { mode: m } : {}) })}>{m === 'chat' ? 'Ask & explain' : 'Summarize'}</button>)}</div>
        <div className="seg" role="group" aria-label="Reading level">{LEVELS.map((l) => <button key={l.id} aria-pressed={level === l.id} className={level === l.id ? 'on' : ''} onClick={() => setLevel(l.id)} title={l.desc}>{l.label}</button>)}</div>
      </header>

      {!paper ? <div className="as-empty"><Sparkles size={26} aria-hidden="true" /><h2>Choose a paper to start</h2><p className="muted">Pick one above, or <Link to="/app/discover">find one in Discover</Link>.</p></div> : (
        <>
          <div className="as-sub"><Tag tone="ai">Reading level: {level}</Tag><span className="muted sm">{paper.title}</span>
            {originalUrl(paper) && <a className="link sm" href={originalUrl(paper)!} target="_blank" rel="noreferrer noopener">Original <ExternalLink size={12} /></a>}
            <span className="grow" />{mode === 'chat' && msgs.length > 0 && <button className="btn sm ghost" onClick={() => setMsgs([])}><Plus size={14} /> New conversation</button>}</div>

          {mode === 'summarize' ? (
            <section className="as-body"><div className="thread">
              <Notice>Summaries are generated from passages retrieved from the paper. They are not guaranteed to cover the full paper.</Notice>
              <label className="field"><span>Focus</span><input value={focus} onChange={(e) => setFocus(e.target.value)} maxLength={300} /></label>
              <button className="btn primary" onClick={summarize} disabled={busy}>{busy ? <><Spinner /> Generating…</> : 'Generate summary'}</button>
              <div aria-live="polite">{sumErr && <ErrorBox message={sumErr} onRetry={summarize} />}
                {sum && <article className="answer article"><Prose text={sum.text} sources={sum.sources} onCite={setCite} /><SourceChips sources={sum.sources} onCite={setCite} /></article>}</div>
            </div></section>
          ) : (
            <section className="as-body"><div className="thread" aria-live="polite">
              {msgs.length === 0 && <div className="suggest"><p className="muted">Try a question:</p>{SUGGEST.map((s) => <button key={s} className="chip big" onClick={() => send(s)}>{s}</button>)}
                {import.meta.env.DEV && <button className="btn sm ghost" onClick={() => setMsgs([
                  { id: ++uid, role: 'user', content: 'Layout sample question', sample: true },
                  { id: ++uid, role: 'assistant', sample: true, content: 'LAYOUT SAMPLE, NOT MODEL OUTPUT.\n\nThis shows how a **grounded answer** renders, with a citation chip [Source 1] and a list:\n\n- First point\n- Second point', sources: [{ source: 1, paper_id: paper.paper_id, page: 'Unknown' }] }])}>Preview layout sample (dev only)</button>}</div>}
              {msgs.map((m) => m.role === 'user' ? <div key={m.id} className="bubble user">{m.content}</div> : (
                <div key={m.id} className="answer">
                  {m.sample && <Tag tone="warn">Layout sample, not real output</Tag>}
                  {m.error ? <ErrorBox message={m.error} onRetry={m.retry ? () => { const base = msgs.slice(0, msgs.findIndex((x) => x.id === m.id) - 1); send(m.retry!, base) } : undefined} /> : (<>
                    <Prose text={m.content} sources={m.sources ?? []} onCite={setCite} /><SourceChips sources={m.sources ?? []} onCite={setCite} />
                    <div className="ans-actions"><button className="btn sm ghost" onClick={() => copy(m)}>{copied === m.id ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy</>}</button></div></>)}
                </div>))}
              {busy && <div className="answer" role="status"><Spinner /> <span className="muted">Reading the paper…</span></div>}
              <div ref={end} />
            </div>
            <form className="composer" onSubmit={(e) => { e.preventDefault(); send(text) }}>
              <label className="sr" htmlFor="q">Your question</label>
              <textarea id="q" rows={1} value={text} maxLength={2000} placeholder={msgs.length ? 'Ask a follow-up…' : 'Ask about this paper…'} onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(text) } }} />
              <button className="btn primary" disabled={busy || !text.trim()} aria-label="Send"><Send size={16} /></button></form></section>)}
          <p className="disclaimer"><ShieldAlert size={13} aria-hidden="true" /> AI answers may be incomplete or wrong. Check them against the original paper.</p>
        </>)}

      <Dialog open={!!cite} onClose={() => setCite(null)} title={cite ? `Source ${cite.source}` : ''}>
        {cite && <dl className="kv"><div><dt>Paper</dt><dd>{citeInfo?.title ?? cite.paper_id}</dd></div><div><dt>Paper ID</dt><dd>{cite.paper_id}</dd></div><div><dt>Page</dt><dd>{cite.page === 'Unknown' ? 'Not provided' : cite.page}</dd></div></dl>}
        <p className="muted sm">The backend returns the source number, paper and page only. The retrieved passage text is not returned yet, so none is shown.</p>
        <div className="row gap">{citeInfo && originalUrl(citeInfo) && <a className="btn primary sm" href={originalUrl(citeInfo)!} target="_blank" rel="noreferrer noopener">Open original <ExternalLink size={13} /></a>}<button className="btn sm" onClick={() => setCite(null)}>Close</button></div>
      </Dialog>
    </div>
  )
}
