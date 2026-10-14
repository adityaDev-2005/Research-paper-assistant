import { useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from 'react'

export function useLS<T>(key: string, init: T): [T, (v: T | ((p: T) => T)) => void] {
  const [v, setV] = useState<T>(() => { try { const r = localStorage.getItem(key); return r ? JSON.parse(r) : init } catch { return init } })
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify(v)) } catch { /* storage unavailable */ } }, [key, v])
  return [v, setV]
}

export function Reveal({ children, className = '' }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current; if (!el) return
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) { el.classList.add('in'); return }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { el.classList.add('in'); io.disconnect() } }, { threshold: 0.12 })
    io.observe(el); return () => io.disconnect()
  }, [])
  return <div ref={ref} className={`reveal ${className}`}>{children}</div>
}

export function useDebounced<T>(value: T, ms = 250) {
  const [v, setV] = useState(value)
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t) }, [value, ms])
  return v
}

export type ThemePref = 'system' | 'light' | 'dark'
const readPref = (): ThemePref => { try { return (localStorage.getItem('ss.theme') as ThemePref) || 'system' } catch { return 'system' } }

/** Theme state is derived from React state only (never read back from the DOM), so repeated toggles always work. */
export function useTheme() {
  const [pref, setPref] = useState<ThemePref>(readPref)
  const [sysDark, setSysDark] = useState(() => matchMedia('(prefers-color-scheme: dark)').matches)
  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)'); const on = () => { setSysDark(mq.matches) }
    mq.addEventListener('change', on); return () => { mq.removeEventListener('change', on) }
  }, [])
  useEffect(() => {
    const f = () => { setPref(readPref()) }
    window.addEventListener('ss-theme', f); return () => { window.removeEventListener('ss-theme', f) }
  }, [])
  const isDark = pref === 'dark' || (pref === 'system' && sysDark)
  useEffect(() => { document.documentElement.dataset.theme = isDark ? 'dark' : 'light' }, [isDark])
  const set = (p: ThemePref) => { try { localStorage.setItem('ss.theme', p) } catch { /* blocked */ } setPref(p); window.dispatchEvent(new Event('ss-theme')) }
  return { pref, set, toggle: () => set(isDark ? 'light' : 'dark'), isDark }
}
