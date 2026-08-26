import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { BrainCircuit, Eye, EyeOff, ArrowLeft, Loader2, User, Mail, Lock } from 'lucide-react'
import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/store/auth-store'
import { Button } from '@/components/ui'
import { friendlyError } from '@/hooks/use-api-query'

export function RegisterPage() {
  const navigate = useNavigate()
  const { setSession } = useAuthStore()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: authService.register,
    onSuccess: (registeredUser, variables) => {
      // Create session for new user with profileCompleted: false
      const newUser = {
        id: String(registeredUser?.id || 'usr_' + Date.now()),
        full_name: String(registeredUser?.full_name || variables.full_name),
        email: String(registeredUser?.email || variables.email),
        profileCompleted: false
      }
      setSession('registered_token_' + Date.now(), newUser)
      navigate('/profile-setup', { replace: true })
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match.')
      return
    }
    setValidationError(null)
    mutation.mutate({ full_name: fullName, email, password, role: 'faculty' })
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

      {/* Main Register Card */}
      <main className="my-auto mx-auto w-full max-w-md">
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 backdrop-blur-xl p-8 sm:p-10 shadow-float">
          <div className="text-center space-y-1.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-ink dark:text-white">Create your ClassroomIQ account</h1>
            <p className="text-xs text-muted dark:text-slate-300 font-semibold">
              Set up your account to begin building your teaching workspace.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {/* 1. Full Name */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                Full Name
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                  <User className="h-4 w-4" />
                </div>
                <input
                  required
                  minLength={2}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Dr. Eleanor Vance"
                  className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                />
              </div>
            </div>

            {/* 2. Email Address */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                Institutional Email
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
                  placeholder="eleanor.vance@university.edu"
                  className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                />
              </div>
            </div>

            {/* 3. Password */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                Password
              </label>
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

            {/* 4. Confirm Password */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  required
                  minLength={8}
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                />
              </div>
            </div>

            {/* Validation & API Errors */}
            {(validationError || mutation.error) && (
              <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-semibold text-danger">
                {validationError || friendlyError(mutation.error)}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={mutation.isPending}
              className="h-11 w-full gap-2 text-sm font-bold shadow-soft mt-2"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Creating account…</span>
                </>
              ) : (
                <span>Create Account</span>
              )}
            </Button>
          </form>

          {/* Switch to Login */}
          <div className="mt-6 border-t border-line pt-6 text-center text-xs text-muted dark:text-slate-300 font-semibold">
            <span>Already have an account? </span>
            <Link to="/login" className="font-bold text-brand hover:underline">
              Sign in
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
