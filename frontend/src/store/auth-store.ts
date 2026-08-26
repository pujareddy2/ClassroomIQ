import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type CurrentUser = {
  id: string
  full_name: string
  email: string
  role?: string
  profileImage?: string
  institution?: string
  department?: string
  designation?: string
  profileCompleted?: boolean
}

type AuthState = {
  token: string | null
  user: CurrentUser | null
  setSession: (token: string, user: CurrentUser) => void
  updateUserProfile: (profile: Partial<CurrentUser>) => void
  clearSession: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => {
        localStorage.setItem('classroomiq.token', token)
        set({ token, user })
      },
      updateUserProfile: (profileData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...profileData } : null
        }))
      },
      clearSession: () => {
        localStorage.removeItem('classroomiq.token')
        set({ token: null, user: null })
      }
    }),
    { name: 'classroomiq-auth' }
  )
)
