import { useAuth } from './auth/auth'
import { useStore } from './lib/store'
import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './auth/auth'
import { StoreProvider } from './lib/store'
import Shell from './components/Shell'
import { Empty } from './components/ui'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Overview from './pages/Overview'
import Discover from './pages/Discover'
import PaperDetail from './pages/PaperDetail'
import Library from './pages/Library'
import Notes from './pages/Notes'
import Settings from './pages/Settings'
const Assistant = lazy(() => import('./pages/Assistant'))

function ScrollTop() { const { pathname } = useLocation(); useEffect(() => { window.scrollTo(0, 0) }, [pathname]); return null }
function ProfileSync() {
  const { status, profile } = useAuth()
  const { setPrefs } = useStore()

  useEffect(() => {
    if (status !== 'signed-in' || !profile) return

    setPrefs({
      level: profile.level,
      interests: profile.interests,
      onboarded: profile.onboarded,
    })
  }, [
    status,
    profile?.level,
    profile?.onboarded,
    JSON.stringify(profile?.interests),
    setPrefs,
  ])

  return null
}
export default function App() {
  return (
    <BrowserRouter><AuthProvider><StoreProvider><ProfileSync /><ScrollTop />
      <Suspense fallback={<div className="center pad" role="status">Loading…</div>}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/signin" element={<Auth mode="signin" />} />
          <Route path="/signup" element={<Auth mode="signup" />} />
          <Route element={<RequireAuth />}><Route path="/onboarding" element={<Onboarding />} /></Route>
          <Route element={<RequireAuth needOnboarding />}>
            <Route path="/app" element={<Shell />}>
              <Route index element={<Overview />} />
              <Route path="discover" element={<Discover />} />
              <Route path="papers/:id" element={<PaperDetail />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="library" element={<Library />} />
              <Route path="notes" element={<Notes />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
          <Route path="*" element={<div className="pad"><Empty icon="404" title="Page not found" action={<Link className="btn" to="/">Go home</Link>} /></div>} />
        </Routes>
      </Suspense>
    </StoreProvider></AuthProvider></BrowserRouter>
  )
}
