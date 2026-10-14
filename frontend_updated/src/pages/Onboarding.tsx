import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Check, ArrowRight, ArrowLeft } from 'lucide-react'
import { Logo, ThemeToggle, Notice } from '../components/ui'
import { INTERESTS, LEVELS, useStore } from '../lib/store'
import { profileStorage, useAuth } from '../auth/auth'
import type { Level } from '../lib/types'

export default function Onboarding() {
  const { prefs, setPrefs } = useStore(); const nav = useNavigate(); const auth = useAuth()
  const [step, setStep] = useState(0); const [level, setLevel] = useState<Level>(prefs.level); const [ints, setInts] = useState<string[]>(prefs.interests)
  const toggle = (id: string) => setInts((a) => (a.includes(id) ? a.filter((x) => x !== id) : [...a, id]))
  const finish = async () => {
  const data = { level, interests: ints, onboarded: true }

  setPrefs(data)

  if (auth.user) {
    try {
      await profileStorage.save(auth.user.id, data)
      await auth.refreshProfile()
      nav('/app', { replace: true })
    } catch (error) {
      console.error('Failed to save your profile:', error)
      alert('Could not save your profile. Please check your connection and try again.')
    }
  } else {
    nav('/app', { replace: true })
  }
}

  if (auth.status === 'signed-in' && auth.profile?.onboarded) return <Navigate to="/app" replace />
  return (
    <div className="onb">
      <header className="container row"><Logo /><span className="grow" /><ThemeToggle /></header>
      <main className="onb-main">
        <div className="progress" role="progressbar" aria-valuemin={1} aria-valuemax={2} aria-valuenow={step + 1} aria-label={`Step ${step + 1} of 2`}><i style={{ width: `${(step + 1) * 50}%` }} /></div>
        <p className="eyebrow">Step {step + 1} of 2</p>
        {step === 0 ? (<>
          <h1>How do you like papers explained?</h1><p className="muted">This becomes your default reading level. You can change it any time.</p>
          <div className="choice-grid" role="radiogroup" aria-label="Reading level">{LEVELS.map((l) => (
            <button key={l.id} role="radio" aria-checked={level === l.id} className={`choice ${level === l.id ? 'on' : ''}`} onClick={() => setLevel(l.id)}>
              <span className="tick">{level === l.id && <Check size={14} />}</span><strong>{l.label}</strong><span className="muted">{l.desc}</span></button>))}</div>
        </>) : (<>
          <h1>What do you research?</h1><p className="muted">Pick any that apply. They shape your recommendations.</p>
          <div className="choice-grid" role="group" aria-label="Research interests">{INTERESTS.map((i) => (
            <button key={i.id} aria-pressed={ints.includes(i.id)} className={`choice ${ints.includes(i.id) ? 'on' : ''}`} onClick={() => toggle(i.id)}>
              <span className="tick">{ints.includes(i.id) && <Check size={14} />}</span><strong>{i.label}</strong><span className="muted">{i.desc}</span>
              {!i.domain && <span className="muted sm">No separate domain in the current collection</span>}</button>))}</div>
        </>)}
        <div className="row gap onb-actions">
          {step > 0 && <button className="btn" onClick={() => setStep(0)}><ArrowLeft size={16} /> Back</button>}
          <span className="grow" />
          {step === 0 ? <button className="btn primary" onClick={() => setStep(1)}>Continue <ArrowRight size={16} /></button> : <button className="btn primary" onClick={finish}>Finish</button>}
        </div>
        <Notice>Your choices are saved in this browser only. Saving them to your account needs Google sign-in and profile storage, which are not implemented yet.</Notice>
      </main>
    </div>
  )
}
