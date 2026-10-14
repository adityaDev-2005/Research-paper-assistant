import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { Logo, ThemeToggle, Spinner } from '../components/ui'
import { postSignInRoute, useAuth } from '../auth/auth'
import { useStore } from '../lib/store'


// const [busy, setBusy] = useState(false)
// const [err, setErr] = useState('')


const G = () => <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.9 2.4 30.4 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.5 17.7 9.5 24 9.5z" /><path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.4 5.8c4.3-4 6.9-9.9 6.9-17.2z" /><path fill="#FBBC05" d="M10.5 28.7a14.5 14.5 0 0 1 0-9.4l-7.9-6.1a24 24 0 0 0 0 21.6l7.9-6.1z" /><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.4-5.8c-2.1 1.4-4.9 2.3-8.5 2.3-6.3 0-11.6-4-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z" /></svg>

export default function Auth({ mode }: { mode: 'signin' | 'signup' }) {
  const auth = useAuth();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('')
  const up = mode === 'signup'
  const nav = useNavigate(); const { prefs } = useStore()
  // Once a real session exists (Step 2): first-time users -> onboarding, returning users -> workspace.
  useEffect(() => {
    if (auth.status === 'signed-in') {
      nav(postSignInRoute(auth.profile?.onboarded === true), {
        replace: true,
      })
    }
  }, [auth.status, auth.profile, nav])// eslint-disable-line
  const go = async () => { setBusy(true); setErr(''); try { await auth.signInWithGoogle() } catch (e) { setErr((e as Error).message) } finally { setBusy(false) } }
  return (
    <div className="auth">
      <aside className="auth-side" aria-hidden="true"><div className="glow" /><Sparkles size={22} /><p>Ask a paper a question and see exactly which pages the answer came from.</p></aside>
      <main className="auth-main">
        <div className="auth-top"><Link to="/" className="btn ghost sm"><ArrowLeft size={15} /> Back to home</Link><ThemeToggle /></div>
        <div className="auth-card">
          <Logo /><h1>{up ? 'Create your account' : 'Welcome back'}</h1>
          <p className="muted">{up ? 'Continue with Google to start reading smarter.' : 'Sign in to pick up where you left off.'}</p>
          <button className="btn google" onClick={go} disabled={busy} aria-busy={busy}>{busy ? <Spinner /> : <G />} {busy ? 'Connecting…' : `${up ? 'Sign up' : 'Sign in'} with Google`}</button>
          <div aria-live="polite">{err && <div className="error-box" role="alert"><div><strong>Not available yet</strong><p>{err}</p></div></div>}</div>
          <p className="muted sm">{up ? 'Already have an account?' : 'New here?'} <Link to={up ? '/signin' : '/signup'}>{up ? 'Sign in' : 'Create an account'}</Link></p>
          {!up && (<>
            <hr />
            {/* <Link className="btn ghost" to="/onboarding">Preview onboarding</Link>
            <Link className="btn ghost" to="/app">Preview the workspace (no account)</Link>
            <p className="muted sm">Authentication is connected in Step 2. These previews create no account and save nothing to a server.</p> */}
          </>)}
        </div>
      </main>
    </div>
  )
}
