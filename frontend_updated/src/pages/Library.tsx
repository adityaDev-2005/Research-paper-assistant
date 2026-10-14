import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, Search, Trash2 } from 'lucide-react'
import { Empty, Notice, PageHead, PaperCard } from '../components/ui'
import { byId } from '../lib/provider'
import { useStore } from '../lib/store'
import type { Paper } from '../lib/types'

export default function Library() {
  const { library, toggleSave } = useStore(); const [q, setQ] = useState(''); const [sort, setSort] = useState('saved')
  let items = library.map((l) => ({ p: byId(l.id) as Paper, at: l.at })).filter((x) => x.p)
  items = items.filter(({ p }) => !q || [p.title, p.domain, ...p.authors].join(' ').toLowerCase().includes(q.toLowerCase()))
  if (sort === 'year') items.sort((a, b) => (b.p.year ?? 0) - (a.p.year ?? 0)); if (sort === 'title') items.sort((a, b) => a.p.title.localeCompare(b.p.title))
  return (
    <>
      <PageHead title="My Library" sub={`${library.length} saved`} />
      <Notice>Prototype: saved papers live in this browser only and are not synced across devices.</Notice>
      {library.length === 0 ? <Empty icon={<Bookmark />} title="Your library is empty" action={<Link className="btn primary" to="/app/discover">Discover papers</Link>}>Save papers with the bookmark icon to keep them here.</Empty> : (<>
        <div className="filters"><label className="field grow"><span className="sr">Search library</span><span className="input-ic"><Search size={16} aria-hidden="true" /><input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search saved papers" /></span></label>
          <label className="field"><span>Sort</span><select value={sort} onChange={(e) => setSort(e.target.value)}><option value="saved">Recently saved</option><option value="year">Newest</option><option value="title">Title A–Z</option></select></label></div>
        {items.length ? <div className="grid-papers">{items.map(({ p }) => <PaperCard key={p.paper_id} p={p} actions={<button className="btn sm ghost danger" onClick={() => toggleSave(p.paper_id)}><Trash2 size={13} /> Remove</button>} />)}</div>
          : <Empty icon={<Search />} title="No saved paper matches">Try another search.</Empty>}</>)}
    </>
  )
}
