import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/store/auth-store'

export function ProtectedRoute() {
  const { token, user, setSession, clearSession } = useAuthStore()
  const location = useLocation()

  const query = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authService.me,
    enabled: Boolean(token),
    retry: false
  })

  useEffect(() => {
    if (token && query.data) {
      setSession(token, { ...query.data, profileCompleted: user?.profileCompleted ?? query.data.profileCompleted })
    }
  }, [query.data, setSession, token, user?.profileCompleted])

  if (!token) return <Navigate to="/login" replace />

  if (query.isError) {
    clearSession()
    return <Navigate to="/login" replace />
  }

  if (query.isLoading) {
    return (
      <div className="grid min-h-screen place-items-center bg-canvas text-sm font-semibold text-muted">
        Restoring your workspace…
      </div>
    )
  }

  // Profile setup completion enforcement
  const isProfileSetupPath = location.pathname === '/profile-setup'
  const isProfileIncomplete = user && !user.profileCompleted

  if (isProfileIncomplete && !isProfileSetupPath) {
    return <Navigate to="/profile-setup" replace />
  }

  if (!isProfileIncomplete && isProfileSetupPath) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
