import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { BrainCircuit, Eye, EyeOff, ArrowLeft, Loader2, Lock, Mail } from 'lucide-react'
import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/store/auth-store'
import { Button } from '@/components/ui'
import { friendlyError } from '@/hooks/use-api-query'

export function LoginPage() {
  const navigate = useNavigate()
  const { token, user, setSession } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const mutation = useMutation({
    mutationFn: authService.login,
    onSuccess: ({ access_token, user: loggedUser }) => {
      setSession(access_token, loggedUser)
      if (loggedUser.profileCompleted) {
        navigate('/dashboard', { replace: true })
      } else {
        navigate('/profile-setup', { replace: true })
      }
    }
  })

  if (token) {
    if (user?.profileCompleted) {
      return <Navigate to="/dashboard" replace />
    }
    return <Navigate to="/profile-setup" replace />
  }

  return (
    <div className="min-h-screen flex flex-col justify-between bg-canvas text-ink antialiased p-4 sm:p-8 relative overflow-hidden">
      {/* Top Header */}
      <div className="mx-auto w-full max-w-md flex items-center justify-between">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-xs font-semibold text-muted transition hover:text-ink dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Home</span>
        </Link>
        <div className="flex items-center gap-2 font-bold text-sm">
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-brand text-white shadow-soft">
            <BrainCircuit className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="tracking-tight font-extrabold text-ink dark:text-white leading-none">ClassroomIQ</span>
            <span className="text-[9px] font-semibold text-muted dark:text-slate-300 uppercase tracking-wider mt-0.5">Teaching Intelligence</span>
          </div>
        </div>
      </div>

      {/* Main Login Card */}
      <main className="my-auto mx-auto w-full max-w-md">
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 backdrop-blur-xl p-8 sm:p-10 shadow-float">
          <div className="text-center space-y-1.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-ink dark:text-white">Welcome back</h1>
            <p className="text-xs text-muted dark:text-slate-300 font-semibold">
              Sign in to continue to your teaching workspace.
            </p>
          </div>

          <form 
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate({ email, password })
            }}
            className="mt-8 space-y-5"
          >
            {/* Email Input */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="faculty@university.edu"
                  className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-ink dark:text-white">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => alert('Password reset link will be sent to your email.')}
                  className="text-xs font-bold text-brand hover:underline"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  required
                  minLength={8}
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-10 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {mutation.error && (
              <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-semibold text-danger">
                {friendlyError(mutation.error)}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={mutation.isPending}
              className="h-11 w-full gap-2 text-sm font-bold shadow-soft"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Signing in…</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </Button>
          </form>

          {/* Switch to Register */}
          <div className="mt-6 border-t border-line pt-6 text-center text-xs text-muted dark:text-slate-300 font-semibold">
            <span>Don't have an account? </span>
            <Link to="/register" className="font-bold text-brand hover:underline">
              Create one
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-muted dark:text-slate-400 font-semibold py-2">
        ClassroomIQ Teaching Intelligence Platform © {new Date().getFullYear()}
      </footer>
    </div>
  )
}
