import { Link } from 'react-router-dom'
import { ArrowRight, BookOpenCheck, Compass, Layers, MessageSquareText, NotebookPen, Quote, ShieldCheck, Sparkles } from 'lucide-react'
import { Logo, ThemeToggle, Tag } from '../components/ui'
import { Reveal } from '../lib/hooks'
import { PAPERS, DOMAINS, byId } from '../lib/provider'

function Preview() {
  const p = byId('ML03')!
  return (
    <div className="preview" aria-label="Illustration of the reading assistant interface">
      <div className="pv-bar"><span /><span /><span /><em>Interface illustration · sample content</em></div>
      <div className="pv-paper"><Tag>{p.domain}</Tag><h3>{p.title}</h3><p className="muted sm">{p.authors[0]} et al. · {p.year}</p></div>
      <div className="pv-chat">
        <div className="bubble user">What problem does this paper set out to solve?</div>
        <div className="bubble ai"><div className="ai-label"><Sparkles size={14} /> Intermediate level</div>
          <p>An answer is written from retrieved passages of the paper, at the reading level you choose.<button className="cite" tabIndex={-1}>1</button><button className="cite" tabIndex={-1}>2</button></p>
          <div className="pv-src"><span className="chip"><b>1</b> {p.paper_id} · page</span><span className="chip"><b>2</b> {p.paper_id} · page</span></div></div>
      </div>
      <div className="pv-in"><span>Ask a follow-up…</span><ArrowRight size={16} /></div>
    </div>
  )
}

const FEATURES = [
  { i: Compass, t: 'Discover', d: 'Search a curated collection by title, author, year or domain, and filter down to what you need.' },
  { i: MessageSquareText, t: 'Source-grounded answers', d: 'Questions are answered from passages retrieved from the paper, with source numbers and page references.' },
  { i: Layers, t: 'Adaptive explanations', d: 'Choose Beginner, Intermediate or Expert and get explanations pitched at that level, with follow-ups.' },
  { i: NotebookPen, t: 'Library & notes', d: 'Keep papers you care about and write notes linked to them.' },
]
const STEPS = [['Find', 'Search or browse the collection.'], ['Open', 'Read details and go to the original paper.'], ['Ask', 'Question the paper at your reading level.'], ['Verify', 'Check each answer against its cited pages.']]
const USES = ['Get oriented in an unfamiliar area', 'Work through a difficult paper section by section', 'Check an answer against the source pages', 'Keep notes beside the paper you are reading']

export default function Landing() {
  return (
    <div className="landing">
      <a href="#top" className="skip">Skip to content</a>
      <header className="l-head"><div className="container row">
        <Logo />
        <nav className="l-nav" aria-label="Primary"><a href="#features">Features</a><a href="#about">About</a></nav>
        <span className="grow" /><ThemeToggle />
        <Link className="btn ghost hide-sm" to="/signin">Sign in</Link><Link className="btn primary" to="/signup">Get started</Link>
      </div></header>

      <main id="top">
        <section className="hero"><div className="glow" aria-hidden="true" />
          <div className="container hero-grid">
            <div className="hero-copy">
              <Tag tone="ai"><Sparkles size={13} /> Research paper intelligence</Tag>
              <h1>Understand research papers, at your level.</h1>
              <p className="lead">Discover papers, ask questions and get source-grounded answers with page references, explained the way you prefer to read.</p>
              <div className="row gap"><Link className="btn primary lg" to="/signup">Get started <ArrowRight size={18} /></Link><a className="btn lg" href="#how">See how it works</a></div>
              <p className="muted sm">Starting with {PAPERS.length} curated papers across {DOMAINS.join(', ')}.</p>
            </div>
            <div className="float"><Preview /></div>
          </div>
        </section>

        <section id="features" className="section"><div className="container">
          <Reveal><p className="eyebrow">Why ScholarSpace</p><h2 className="h2">Read faster without losing the source.</h2>
            <p className="lead narrow">Most AI tools give you an answer. ScholarSpace keeps you connected to where it came from.</p></Reveal>
          <div className="feature-list">{FEATURES.map(({ i: I, t, d }) => (
            <Reveal key={t} className="feature"><I size={22} aria-hidden="true" /><h3>{t}</h3><p className="muted">{d}</p></Reveal>))}</div>
        </div></section>

        <section id="how" className="section alt"><div className="container">
          <Reveal><p className="eyebrow">Workflow</p><h2 className="h2">From question to verified answer.</h2></Reveal>
          <ol className="steps">{STEPS.map(([t, d], n) => <Reveal key={t} className="step"><span className="step-n">{n + 1}</span><h3>{t}</h3><p className="muted">{d}</p></Reveal>)}</ol>
        </div></section>

        <section className="section"><div className="container split">
          <Reveal><p className="eyebrow">Reading assistant</p><h2 className="h2">Three levels. One paper.</h2>
            <dl className="levels"><dt>Beginner</dt><dd>Accessible explanations with fundamentals and added context.</dd>
              <dt>Intermediate</dt><dd>Technical explanations with relevant background and methodology.</dd>
              <dt>Expert</dt><dd>Concise analysis of methods, assumptions, results and limitations.</dd></dl>
            <p className="muted sm"><ShieldCheck size={14} className="inl" /> AI answers may be incomplete. Always check them against the original paper.</p></Reveal>
          <Reveal><Preview /></Reveal>
        </div></section>

        <section className="section alt"><div className="container split">
          <Reveal><p className="eyebrow">Workflows</p><h2 className="h2">Built for how people actually read papers.</h2></Reveal>
          <Reveal><ul className="uses">{USES.map((u) => <li key={u}><BookOpenCheck size={18} aria-hidden="true" />{u}</li>)}</ul></Reveal>
        </div></section>

        <section id="about" className="section"><div className="container narrow-col">
          <Reveal><p className="eyebrow">About</p><h2 className="h2">A student-built research assistant.</h2>
            <p className="lead">ScholarSpace combines a metadata search, retrieval-augmented generation over indexed papers, and adaptive explanations. It runs on a FastAPI backend with ChromaDB, BGE-M3 embeddings and a local Phi-3 model through Ollama.</p>
            <p className="muted">Evaluation results are preliminary. Summaries are generated from retrieved passages, not guaranteed full-paper coverage.</p></Reveal>
        </div></section>

        <section className="cta"><div className="container center"><Reveal><Quote size={26} aria-hidden="true" className="cta-q" />
          <h2 className="h2">Open your first paper.</h2><Link className="btn primary lg" to="/signup">Get started <ArrowRight size={18} /></Link></Reveal></div></section>
      </main>

      <footer className="l-foot"><div className="container foot-grid">
        <div><Logo /><p className="muted sm">Research Paper Intelligence & Reading Assistant.</p></div>
        <div><h4>Product</h4><a href="#features">Features</a><a href="#how">How it works</a><a href="#about">About</a></div>
        <div><h4>Account</h4><Link to="/signin">Sign in</Link><Link to="/signup">Get started</Link></div>
        <div><h4>Project</h4><a href="https://github.com/adityaDev-2005/Research-paper-assistant" target="_blank" rel="noreferrer noopener">Backend on GitHub</a><span className="muted sm">Frontend prototype · not yet connected to the backend</span></div>
      </div></footer>
    </div>
  )
}
