import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { CardSkeletons, Empty, ErrorBox, Notice, PageHead, PaperCard } from '../components/ui'
import { DOMAINS, YEAR_MAX, YEAR_MIN, dataSource, domainCount, searchPapers } from '../lib/provider'
import { useDebounced } from '../lib/hooks'
import type { Paper } from '../lib/types'

export default function Discover() {
  const [sp, setSp] = useSearchParams()
  const [text, setText] = useState(sp.get('q') ?? '')
  const q = useDebounced(text); const domain = sp.get('domain') ?? ''; const from = sp.get('from') ?? ''; const to = sp.get('to') ?? ''; const sort = sp.get('sort') ?? 'relevance'
  const [res, setRes] = useState<Paper[]>([]); const [loading, setLoading] = useState(true); const [err, setErr] = useState(''); const [tick, setTick] = useState(0)
  const set = (k: string, v: string) => setSp((o) => { const n = new URLSearchParams(o); v ? n.set(k, v) : n.delete(k); return n }, { replace: true })
  useEffect(() => { set('q', q) }, [q]) // eslint-disable-line
  useEffect(() => {
    const ctl = new AbortController(); setLoading(true); setErr('')
    searchPapers(q, ctl.signal).then((r) => { setRes(r); setLoading(false) }).catch((e) => { if (e.name !== 'AbortError') { setErr(e.message); setLoading(false) } })
    return () => ctl.abort()
  }, [q, tick])
  const shown = useMemo(() => {
    let r = res.filter((p) => (!domain || p.domain === domain) && (!from || (p.year ?? 0) >= +from) && (!to || (p.year ?? 9999) <= +to))
    if (sort === 'newest') r = [...r].sort((a, b) => (b.year ?? 0) - (a.year ?? 0))
    if (sort === 'oldest') r = [...r].sort((a, b) => (a.year ?? 0) - (b.year ?? 0))
    if (sort === 'title') r = [...r].sort((a, b) => a.title.localeCompare(b.title))
    return r
  }, [res, domain, from, to, sort])
  const active = [domain && `Domain: ${domain}`, from && `From ${from}`, to && `To ${to}`].filter(Boolean) as string[]
  const reset = () => { setText(''); setSp({}, { replace: true }) }
  const years = Array.from({ length: YEAR_MAX - YEAR_MIN + 1 }, (_, i) => YEAR_MAX - i)
  return (
    <>
      <PageHead title="Discover papers" sub="Browse the curated collection." />
      <Notice>{dataSource === 'api' ? 'Search runs on the backend /papers endpoint.' : 'Local metadata snapshot.'} Search matches title, authors, year and domain text. It is metadata search, not semantic search. Abstracts are not available in the collection yet.</Notice>
      <div className="filters">
        <label className="field grow"><span className="sr">Search</span><span className="input-ic"><Search size={16} aria-hidden="true" /><input type="search" value={text} onChange={(e) => setText(e.target.value)} placeholder="Search title, author, year, domain" /></span></label>
        <label className="field"><span>Domain</span><select value={domain} onChange={(e) => set('domain', e.target.value)}><option value="">All domains</option>{DOMAINS.map((d) => <option key={d} value={d}>{d} ({domainCount(d)})</option>)}</select></label>
        <label className="field"><span>From</span><select value={from} onChange={(e) => set('from', e.target.value)}><option value="">Any</option>{years.map((y) => <option key={y}>{y}</option>)}</select></label>
        <label className="field"><span>To</span><select value={to} onChange={(e) => set('to', e.target.value)}><option value="">Any</option>{years.map((y) => <option key={y}>{y}</option>)}</select></label>
        <label className="field"><span>Sort</span><select value={sort} onChange={(e) => set('sort', e.target.value)}><option value="relevance">Collection order</option><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="title">Title A–Z</option></select></label>
      </div>
      <div className="row wrap gap sm-gap" aria-live="polite">
        <span className="muted sm"><SlidersHorizontal size={14} className="inl" /> {loading ? 'Loading…' : `${shown.length} paper${shown.length === 1 ? '' : 's'}`}</span>
        {active.map((a) => <span className="chip" key={a}>{a}</span>)}
        {(active.length > 0 || text) && <button className="btn sm ghost" onClick={reset}><X size={14} /> Reset filters</button>}
      </div>
      {err ? <ErrorBox message={err} onRetry={() => setTick((t) => t + 1)} /> : loading ? <CardSkeletons n={6} />
        : shown.length ? <div className="grid-papers">{shown.map((p) => <PaperCard key={p.paper_id} p={p} />)}</div>
        : <Empty icon={<Search />} title="No papers match" action={<button className="btn" onClick={reset}>Reset filters</button>}>Try a different search or remove a filter.</Empty>}
    </>
  )
}
