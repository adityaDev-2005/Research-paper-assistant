
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { onAuthStateChanged, signInWithPopup, signOut as firebaseSignOut } from 'firebase/auth'
import {
  doc,
  getDoc,
  setDoc,
} from 'firebase/firestore'
import { Navigate, Outlet } from 'react-router-dom'
import { auth, db, googleProvider } from '../lib/firebase'
import { useStore } from '../lib/store'

export interface AuthUser {
  id: string
  name: string
  email: string
  photoUrl?: string
}

export interface ProfileData {
  level: 'beginner' | 'intermediate' | 'expert'
  interests: string[]
  onboarded: boolean
}

export interface AuthState {
  status: 'signed-out' | 'loading' | 'signed-in'
  user: AuthUser | null
  profile: ProfileData | null
  signInWithGoogle(): Promise<void>
  signOut(): Promise<void>
  refreshProfile(): Promise<ProfileData | null>
}

export class NotImplementedError extends Error {}

const Ctx = createContext<AuthState>({
  status: 'loading',
  user: null,
  profile: null,
  async signInWithGoogle() {},
  async signOut() {},
  async refreshProfile() { return null },
})

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [status, setStatus] = useState<AuthState['status']>('loading')
  const [user, setUser] = useState<AuthUser | null>(null)
  const [profile, setProfile] = useState<ProfileData | null>(null)

  const refreshProfile = async (): Promise<ProfileData | null> => {
    const currentUser = auth.currentUser

    if (!currentUser) {
      setProfile(null)
      return null
    }

    const snapshot = await getDoc(doc(db, 'users', currentUser.uid))
    const data = snapshot.exists()
      ? snapshot.data() as ProfileData
      : null

    setProfile(data)
    return data
  }

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setStatus('loading')

      if (!firebaseUser) {
        setUser(null)
        setProfile(null)
        setStatus('signed-out')
        return
      }

      setUser({
        id: firebaseUser.uid,
        name: firebaseUser.displayName || firebaseUser.email || 'ScholarSpace User',
        email: firebaseUser.email || '',
        photoUrl: firebaseUser.photoURL || undefined,
      })

      try {
        const snapshot = await getDoc(doc(db, 'users', firebaseUser.uid))
        setProfile(
          snapshot.exists()
            ? snapshot.data() as ProfileData
            : null,
        )
      } catch (error) {
        console.error('Could not load the user profile:', error)
        setProfile(null)
      }

      setStatus('signed-in')
    })

    return unsubscribe
  }, [])

  const signInWithGoogle = async () => {
    await signInWithPopup(auth, googleProvider)
  }

  const signOut = async () => {
    await firebaseSignOut(auth)
  }

  return (
    <Ctx.Provider
      value={{
        status,
        user,
        profile,
        signInWithGoogle,
        signOut,
        refreshProfile,
      }}
    >
      {children}
    </Ctx.Provider>
  )
}

export const useAuth = () => useContext(Ctx)

export function postSignInRoute(onboardingComplete: boolean) {
  return onboardingComplete ? '/app' : '/onboarding'
}

export const AUTH_GUARD_ON = true

export function RequireAuth({
  needOnboarding = false,
}: {
  needOnboarding?: boolean
}) {
  const { status, profile } = useAuth()
  const { prefs } = useStore()

  if (status === 'loading') {
    return <div className="center pad" role="status">Loading…</div>
  }

  if (status !== 'signed-in') {
    return <Navigate to="/signin" replace />
  }

  if (needOnboarding && !profile?.onboarded) {
    return <Navigate to="/onboarding" replace />
  }

  if (!needOnboarding && profile?.onboarded && prefs.onboarded === false) {
    // The server profile is authoritative; local preferences may be out of date.
  }

  return <Outlet />
}

export const profileStorage = {
  async load(userId: string): Promise<ProfileData | null> {
    const snapshot = await getDoc(doc(db, 'users', userId))
    return snapshot.exists()
      ? snapshot.data() as ProfileData
      : null
  },

  async save(userId: string, data: ProfileData): Promise<void> {
    await setDoc(doc(db, 'users', userId), data, { merge: true })
  },
}
