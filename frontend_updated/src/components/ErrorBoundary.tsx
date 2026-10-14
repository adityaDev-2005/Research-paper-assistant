import { Component, type ReactNode } from 'react'

/** Shows the crash message on screen instead of a blank page. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { err: Error | null }> {
  state = { err: null as Error | null }
  static getDerivedStateFromError(err: Error) { return { err } }
  render() {
    if (!this.state.err) return this.props.children
    return (
      <div style={{ padding: 32, maxWidth: 720, margin: '0 auto', fontFamily: 'system-ui, sans-serif', color: 'inherit' }} role="alert">
        <h1>ScholarSpace hit an error</h1>
        <p>Please copy the message below.</p>
        <pre style={{ whiteSpace: 'pre-wrap', padding: 16, borderRadius: 8, background: 'rgba(127,127,127,.15)' }}>{String(this.state.err.stack || this.state.err.message)}</pre>
        <button onClick={() => { try { localStorage.clear() } catch { /* blocked */ } location.href = '/' }}>Clear local data and reload</button>
      </div>
    )
  }
}
