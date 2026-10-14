import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Bookmark, Clock, MessageSquareText, Search, Sparkles } from 'lucide-react'
import { Empty, PageHead, PaperCard, Tag, Notice } from '../components/ui'
import { DOMAINS, byId, dataSource, recommended } from '../lib/provider'
import { INTERESTS, interestDomains, useStore } from '../lib/store'
import type { Paper } from '../lib/types'

export default function Overview() {
  const { prefs, library, recent } = useStore(); const nav = useNavigate(); const [q, setQ] = useState('')
  const [recs, setRecs] = useState<Paper[]>([])
  const doms = interestDomains(prefs.interests)
  useEffect(() => { let on = true; recommended(doms, 4).then((r) => on && setRecs(r)); return () => { on = false } }, [prefs.interests.join()])
  const recentPapers = recent.map(byId).filter(Boolean) as Paper[]
  const saved = library.map((l) => byId(l.id)).filter(Boolean) as Paper[]
  const cont = recentPapers[0]
  return (
    <>
      <PageHead title="Welcome back" sub="Search the collection or pick up where you left off." />
      <form className="bigsearch" role="search" onSubmit={(e) => { e.preventDefault(); nav(`/app/discover?q=${encodeURIComponent(q)}`) }}>
        <Search size={20} aria-hidden="true" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by title, author, year or domain" aria-label="Search papers" /><button className="btn primary">Search</button></form>
      <div className="row wrap gap sm-gap" aria-label="Research interest shortcuts">
        {(doms.length ? doms : DOMAINS).map((d) => <Link key={d} className="chip big" to={`/app/discover?domain=${encodeURIComponent(d)}`}>{d}</Link>)}
        {!doms.length && <span className="muted sm">Choose interests in <Link to="/app/settings">Settings</Link> to personalise these.</span>}
      </div>

      <div className="two-col">
        <section className="hero-card"><Sparkles size={20} aria-hidden="true" /><h2>AI Reading Assistant</h2>
          <p className="muted">Ask a paper a question at your {prefs.level} level and check the cited pages.</p>
          <Link className="btn primary" to={cont ? `/app/assistant?paper=${cont.paper_id}` : '/app/assistant'}><MessageSquareText size={16} /> Open assistant</Link></section>
        <section className="panel"><h2 className="h3"><Clock size={16} /> Continue reading</h2>
          {cont ? (<><Tag>{cont.domain}</Tag><h3 className="h4"><Link to={`/app/papers/${cont.paper_id}`}>{cont.title}</Link></h3>
            <Link to={`/app/assistant?paper=${cont.paper_id}`} className="link">Continue with the assistant <ArrowRight size={14} /></Link></>)
            : <p className="muted">Papers you open will appear here.</p>}</section>
      </div>

      <section className="block"><div className="row"><h2 className="h3">Recommended papers</h2><span className="grow" />
        <Tag>{dataSource === 'api' ? 'From backend /recommend' : 'Demo data · domain match, newest first'}</Tag></div>
        <div className="grid-papers">{recs.map((p) => <PaperCard key={p.paper_id} p={p} />)}</div>
        <Notice>Recommendations filter by domain and year. They are not a measure of quality or difficulty.</Notice></section>

      <div className="two-col even">
        <section className="block"><h2 className="h3">Recently opened</h2>
          {recentPapers.length ? <ul className="plain-list">{recentPapers.slice(0, 5).map((p) => <li key={p.paper_id}><Link to={`/app/papers/${p.paper_id}`}>{p.title}</Link><span className="muted sm">{p.year}</span></li>)}</ul>
            : <Empty icon={<Clock />} title="Nothing opened yet">Open a paper from Discover and it will show up here.</Empty>}</section>
        <section className="block"><h2 className="h3"><Bookmark size={16} /> Saved papers</h2>
          {saved.length ? <ul className="plain-list">{saved.slice(0, 5).map((p) => <li key={p.paper_id}><Link to={`/app/papers/${p.paper_id}`}>{p.title}</Link><span className="muted sm">{p.year}</span></li>)}</ul>
            : <Empty icon={<Bookmark />} title="No saved papers">Use the bookmark on any paper to keep it here.</Empty>}</section>
      </div>
      <p className="muted sm">Interests: {prefs.interests.length ? prefs.interests.map((i) => INTERESTS.find((x) => x.id === i)?.label).join(', ') : 'none selected'}. Recents, saves and notes are stored in this browser only.</p>
    </>
  )
}
