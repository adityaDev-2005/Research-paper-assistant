import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { useLS } from './hooks'
import type { Level } from './types'
import { db } from './firebase'
import { useAuth } from '../auth/auth'

export interface Prefs {
  level: Level
  interests: string[]
  onboarded: boolean
}

export interface Note {
  id: string
  title: string
  body: string
  paperId: string | null
  tags: string[]
  updated: number
}

interface Store {
  prefs: Prefs
  setPrefs: (p: Partial<Prefs>) => void
  library: { id: string; at: number }[]
  isSaved: (id: string) => boolean
  toggleSave: (id: string) => void
  notes: Note[]
  saveNote: (n: Note) => void
  deleteNote: (id: string) => void
  recent: string[]
  touch: (id: string) => void
  resetAll: () => void
}

const Ctx = createContext<Store>(null as unknown as Store)

export const useStore = () => useContext(Ctx)

export function StoreProvider({ children }: { children: ReactNode }) {
  const { status, user } = useAuth()

  const [prefs, setP] = useLS<Prefs>('ss.prefs', {
    level: 'intermediate',
    interests: [],
    onboarded: false,
  })

  const [library, setLib] = useLS<{ id: string; at: number }[]>(
    'ss.library',
    [],
  )

  const [notes, setNotes] = useLS<Note[]>('ss.notes', [])
  const [recent, setRecent] = useLS<string[]>('ss.recent', [])

  const [readyUser, setReadyUser] = useState<string | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)

  const activeUserRef = useRef<string | null>(null)
  const libraryRef = useRef(library)
  const notesRef = useRef(notes)

  // Keep the setter stable so effects depending on setPrefs do not rerun
  // merely because StoreProvider rendered again.
  const setPrefs = useCallback((p: Partial<Prefs>) => {
    setP((old) => ({ ...old, ...p }))
  }, [setP])

  useEffect(() => {
    libraryRef.current = library
  }, [library])

  useEffect(() => {
    notesRef.current = notes
  }, [notes])

  // Load cloud data when the signed-in account changes.
  useEffect(() => {
    if (status !== 'signed-in' || !user) {
      setReadyUser(null)
      activeUserRef.current = null
      return
    }

    let cancelled = false
    const userId = user.id

    setReadyUser(null)
    setSyncError(null)

    async function loadCloudData() {
      try {
        const libraryRefDoc = doc(db, 'users', userId, 'appData', 'library')
        const notesRefDoc = doc(db, 'users', userId, 'appData', 'notes')

        const [librarySnapshot, notesSnapshot] = await Promise.all([
          getDoc(libraryRefDoc),
          getDoc(notesRefDoc),
        ])

        if (cancelled) return

        const previousOwner = localStorage.getItem('ss.cloud.owner')
        const belongsToAnotherAccount =
          previousOwner !== null && previousOwner !== userId

        if (librarySnapshot.exists()) {
          const data = librarySnapshot.data()
          setLib(Array.isArray(data.items) ? data.items : [])
        } else {
          const localItems = belongsToAnotherAccount
            ? []
            : libraryRef.current

          await setDoc(libraryRefDoc, { items: localItems })
          if (cancelled) return
          setLib(localItems)
        }

        if (notesSnapshot.exists()) {
          const data = notesSnapshot.data()
          setNotes(Array.isArray(data.items) ? data.items : [])
        } else {
          const localItems = belongsToAnotherAccount ? [] : notesRef.current

          await setDoc(notesRefDoc, { items: localItems })
          if (cancelled) return
          setNotes(localItems)
        }

        localStorage.setItem('ss.cloud.owner', userId)
        activeUserRef.current = userId
        setReadyUser(userId)
      } catch (error) {
        console.error('Could not load research data:', error)
        if (!cancelled) {
          setSyncError('Could not load your cloud library and notes.')
        }
      }
    }

    void loadCloudData()

    return () => {
      cancelled = true
    }
  }, [status, user?.id, setLib, setNotes])

  // Persist library changes after the initial cloud load.
  useEffect(() => {
    if (
      status !== 'signed-in' ||
      !user ||
      readyUser !== user.id ||
      activeUserRef.current !== user.id
    ) {
      return
    }

    const save = async () => {
      try {
        await setDoc(
          doc(db, 'users', user.id, 'appData', 'library'),
          { items: library },
        )
        setSyncError(null)
      } catch (error) {
        console.error('Could not save library:', error)
        setSyncError('Could not save your library to the cloud.')
      }
    }

    void save()
  }, [library, readyUser, status, user?.id])

  // Persist notes after the initial cloud load.
  useEffect(() => {
    if (
      status !== 'signed-in' ||
      !user ||
      readyUser !== user.id ||
      activeUserRef.current !== user.id
    ) {
      return
    }

    const save = async () => {
      try {
        await setDoc(
          doc(db, 'users', user.id, 'appData', 'notes'),
          { items: notes },
        )
        setSyncError(null)
      } catch (error) {
        console.error('Could not save notes:', error)
        setSyncError('Could not save your notes to the cloud.')
      }
    }

    void save()
  }, [notes, readyUser, status, user?.id])

  const value: Store = {
    prefs,
    setPrefs,

    library,

    isSaved: (id) => library.some((item) => item.id === id),

    toggleSave: (id) => {
      setLib((old) =>
        old.some((item) => item.id === id)
          ? old.filter((item) => item.id !== id)
          : [{ id, at: Date.now() }, ...old],
      )
    },

    notes,

    saveNote: (note) => {
      setNotes((old) =>
        old.some((item) => item.id === note.id)
          ? old.map((item) => (item.id === note.id ? note : item))
          : [note, ...old],
      )
    },

    deleteNote: (id) => {
      setNotes((old) => old.filter((note) => note.id !== id))
    },

    recent,

    touch: (id) => {
      setRecent((old) => [id, ...old.filter((item) => item !== id)].slice(0, 8))
    },

    resetAll: () => {
      ;['ss.prefs', 'ss.library', 'ss.notes', 'ss.recent'].forEach((key) =>
        localStorage.removeItem(key),
      )
      window.location.href = '/'
    },
  }

  return (
    <Ctx.Provider value={value}>
      {syncError && (
        <div role="status" className="sync-warning">
          {syncError}
        </div>
      )}
      {children}
    </Ctx.Provider>
  )
}

export const INTERESTS = [
  { id: 'ai', label: 'Artificial Intelligence', desc: 'Broad AI methods and systems.', domain: null },
  { id: 'ml', label: 'Machine Learning', desc: 'Optimisation, generative and RL methods.', domain: 'Machine Learning' },
  { id: 'cv', label: 'Computer Vision', desc: 'Detection, segmentation, vision models.', domain: 'Computer Vision' },
  { id: 'rob', label: 'Robotics', desc: 'Manipulation, SLAM, learned control.', domain: 'Robotics' },
  { id: 'rs', label: 'Remote Sensing', desc: 'Satellite imagery and Earth observation.', domain: 'Remote Sensing' },
  { id: 'nlp', label: 'Natural Language Processing', desc: 'Language models and text understanding.', domain: null },
  { id: 'rl', label: 'Reinforcement Learning', desc: 'Policies, rewards and control from experience.', domain: null },
] as const

export const interestDomains = (ids: string[]) =>
  INTERESTS.filter((interest) => ids.includes(interest.id) && interest.domain)
    .map((interest) => interest.domain as string)

export const LEVELS: { id: Level; label: string; desc: string }[] = [
  { id: 'beginner', label: 'Beginner', desc: 'Accessible explanations, fundamental concepts and extra context.' },
  { id: 'intermediate', label: 'Intermediate', desc: 'Technical explanations with relevant background and methodology.' },
  { id: 'expert', label: 'Expert', desc: 'Concise technical analysis: methods, assumptions, results, limitations.' },
]