
import { Check, UserRound } from 'lucide-react'
import { PageHead } from '../components/ui'
import { INTERESTS, LEVELS, useStore } from '../lib/store'
import { useTheme, type ThemePref } from '../lib/hooks'
import { useAuth, profileStorage } from '../auth/auth'
import { useState } from 'react'

export default function Settings() {
  const { prefs, setPrefs } = useStore()
  const { pref, set } = useTheme()
  const auth = useAuth()
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const updatePreferences = async (
  patch: {
    level?: 'beginner' | 'intermediate' | 'expert'
    interests?: string[]
  },
) => {
  const updated = {
    level: patch.level ?? prefs.level,
    interests: patch.interests ?? prefs.interests,
    onboarded: auth.profile?.onboarded ?? prefs.onboarded,
  }

  setPrefs(updated)
  setSaveError('')

  if (auth.status !== 'signed-in' || !auth.user) {
    return
  }

  setSaving(true)

  try {
    await profileStorage.save(auth.user.id, updated)
    await auth.refreshProfile()
  } catch (error) {
    console.error('Could not save preferences:', error)
    setSaveError(
      'Your changes are shown locally but could not be saved to your account.',
    )
  } finally {
    setSaving(false)
  }
}

  return (
    <>
      <PageHead title="Settings" />

      <div className="settings">
        <section>
          <h2 className="h3">Profile</h2>

          {auth.status === 'loading' ? (
            <p className="muted">Loading account…</p>
          ) : auth.user ? (
            <div className="row gap">
              {auth.user.photoUrl ? (
                <img
                  src={auth.user.photoUrl}
                  alt=""
                  width={44}
                  height={44}
                  style={{
                    borderRadius: '50%',
                    objectFit: 'cover',
                    flexShrink: 0,
                  }}
                />
              ) : (
                <UserRound size={32} />
              )}

              <div>
                <strong>{auth.user.name}</strong>
                <p
                  className="muted"
                  style={{
                    overflowWrap: 'anywhere',
                    maxWidth: '320px',
                  }}
                >
                  {auth.user.email}
                </p>
                <p className="muted sm">Signed in with Google</p>
              </div>
            </div>
          ) : (
            <p className="muted">You are not signed in.</p>
          )}

          <p className="muted sm">
            Your account is used for authentication and your saved profile
            preferences.
          </p>
        </section>

        <section>
          <h2 className="h3">Reading level</h2>
          <p className="muted">Default level for paper explanations.</p>

          <div
            className="choice-grid"
            role="radiogroup"
            aria-label="Reading level"
          >
            {LEVELS.map((level) => (
              <button
                key={level.id}
                role="radio"
                aria-checked={prefs.level === level.id}
                className={`choice ${
                  prefs.level === level.id ? 'on' : ''
                }`}
                onClick={() => updatePreferences({ level: level.id })}
              >
                <span className="tick">
                  {prefs.level === level.id && <Check size={14} />}
                </span>
                <strong>{level.label}</strong>
                <span className="muted">{level.desc}</span>
              </button>
            ))}
          </div>
        </section>

        <section>
          <h2 className="h3">Research interests</h2>
          <p className="muted">
            Select the topics you want to explore.
          </p>

          <div className="row wrap gap sm-gap">
            {INTERESTS.map((interest) => {
              const selected = prefs.interests.includes(interest.id)

              return (
                <button
                  key={interest.id}
                  aria-pressed={selected}
                  className={`chip big ${selected ? 'on' : ''}`}
                  // onClick={() =>
                  //   setPrefs({
                  //     interests: selected
                  //       ? prefs.interests.filter(
                  //           (id) => id !== interest.id,
                  //         )
                  //       : [...prefs.interests, interest.id],
                  //   })
                  // }
                  onClick={() =>
                  updatePreferences({
                    interests: selected
                      ? prefs.interests.filter((id) => id !== interest.id)
                      : [...prefs.interests, interest.id],
                  })
                }
                >
                  {selected && <Check size={13} />}
                  {interest.label}
                </button>
              )
            })}
          </div>
        </section>

          {saving && (
          <p className="muted sm" role="status">
            Saving preferences…
          </p>
        )}

        {saveError && (
          <p className="err-text" role="alert">
            {saveError}
          </p>
        )}

        <section>
          <h2 className="h3">Theme</h2>

          <div
            className="seg"
            role="radiogroup"
            aria-label="Theme"
          >
            {(['system', 'light', 'dark'] as ThemePref[]).map((theme) => (
              <button
                key={theme}
                role="radio"
                aria-checked={pref === theme}
                className={pref === theme ? 'on' : ''}
                onClick={() => set(theme)}
              >
                {theme[0].toUpperCase() + theme.slice(1)}
              </button>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
