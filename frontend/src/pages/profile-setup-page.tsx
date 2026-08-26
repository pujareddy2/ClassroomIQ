import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrainCircuit, Upload, Trash2, User, Building, BookOpen, GraduationCap, ArrowRight, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'
import { Button } from '@/components/ui'

export function ProfileSetupPage() {
  const navigate = useNavigate()
  const { user, updateUserProfile } = useAuthStore()

  const [fullName, setFullName] = useState(user?.full_name || '')
  const [institution, setInstitution] = useState(user?.institution || '')
  const [department, setDepartment] = useState(user?.department || '')
  const [designation, setDesignation] = useState(user?.designation || 'Assistant Professor')
  const [profileImage, setProfileImage] = useState<string | undefined>(user?.profileImage)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // Generate initials avatar (e.g., "Puja Midde" => "PM")
  const getInitials = (name: string) => {
    if (!name) return 'IQ'
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Client-side file size validation (Max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('Image size must be less than 5MB.')
      return
    }

    if (!['image/jpeg', 'image/jpg', 'image/png', 'image/webp'].includes(file.type)) {
      setErrorMsg('Please upload a valid image file (JPG, PNG, or WEBP).')
      return
    }

    setErrorMsg(null)
    const reader = new FileReader()
    reader.onloadend = () => {
      setProfileImage(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleRemoveImage = () => {
    setProfileImage(undefined)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!fullName.trim()) {
      setErrorMsg('Full Name is required.')
      return
    }
    if (!institution.trim()) {
      setErrorMsg('Institution / University is required.')
      return
    }
    if (!department.trim()) {
      setErrorMsg('Department is required.')
      return
    }
    if (!designation) {
      setErrorMsg('Designation is required.')
      return
    }

    setErrorMsg(null)
    setIsSubmitting(true)

    // Simulate saving profile and updating auth state
    setTimeout(() => {
      updateUserProfile({
        full_name: fullName.trim(),
        institution: institution.trim(),
        department: department.trim(),
        designation,
        profileImage,
        profileCompleted: true
      })
      setIsSubmitting(false)
      navigate('/dashboard', { replace: true })
    }, 400)
  }

  return (
    <div className="min-h-screen flex flex-col justify-between bg-canvas text-ink antialiased p-4 sm:p-8 relative overflow-hidden">
      {/* Top Brand Header */}
      <div className="mx-auto w-full max-w-lg flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-sm">
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-brand text-white shadow-soft">
            <BrainCircuit className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="tracking-tight font-extrabold text-ink dark:text-white leading-none">ClassroomIQ</span>
            <span className="text-[9px] font-semibold text-muted dark:text-slate-300 uppercase tracking-wider mt-0.5">Teaching Intelligence</span>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-brand bg-brand-soft px-3 py-1 rounded-full border border-brand/20">
          PROFILE SETUP
        </span>
      </div>

      {/* Main Profile Setup Card */}
      <main className="my-auto mx-auto w-full max-w-lg">
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 backdrop-blur-xl p-8 sm:p-10 shadow-float">
          
          {/* Header */}
          <div className="text-center space-y-1.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-ink dark:text-white">Complete your profile</h1>
            <p className="text-xs text-muted dark:text-slate-300 font-bold">
              Tell us a little about yourself so we can personalize your teaching workspace.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            
            {/* Prominent Profile Photo Area */}
            <div className="flex flex-col items-center justify-center space-y-3 pb-2 border-b border-line">
              <div className="relative">
                {profileImage ? (
                  <img 
                    src={profileImage} 
                    alt="Profile Preview" 
                    className="h-24 w-24 rounded-2xl object-cover border-2 border-brand shadow-soft"
                  />
                ) : (
                  <div className="grid h-24 w-24 place-items-center rounded-2xl bg-gradient-to-br from-brand via-indigo-500 to-purple-600 text-2xl font-extrabold text-white shadow-soft">
                    {getInitials(fullName)}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept="image/jpeg,image/jpg,image/png,image/webp" 
                  onChange={handleImageUpload}
                  className="hidden" 
                />

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-line bg-canvas px-4 text-xs font-bold text-ink dark:text-white hover:bg-surface transition shadow-soft"
                >
                  <Upload className="h-3.5 w-3.5 text-brand" />
                  <span>{profileImage ? 'Replace Photo' : 'Upload Photo'}</span>
                </button>

                {profileImage && (
                  <button
                    type="button"
                    onClick={handleRemoveImage}
                    className="inline-flex h-9 items-center justify-center rounded-xl border border-danger/30 bg-danger/10 px-3 text-xs font-bold text-danger hover:bg-danger/20 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <span className="text-[11px] text-muted dark:text-slate-400 font-semibold">
                JPG, PNG, or WEBP (Max 5MB). Photo is optional.
              </span>
            </div>

            {/* Fields Grid */}
            <div className="space-y-4">
              
              {/* 1. Full Name */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Full Name <span className="text-danger">*</span>
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                    <User className="h-4 w-4" />
                  </div>
                  <input
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Eleanor Vance"
                    className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                  />
                </div>
              </div>

              {/* 2. Institution / University */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Institution / University <span className="text-danger">*</span>
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                    <Building className="h-4 w-4" />
                  </div>
                  <input
                    required
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    placeholder="Stanford University"
                    className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                  />
                </div>
              </div>

              {/* 3. Department */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Department <span className="text-danger">*</span>
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                    <BookOpen className="h-4 w-4" />
                  </div>
                  <input
                    required
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="Computer Science"
                    className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-medium"
                  />
                </div>
              </div>

              {/* 4. Designation Dropdown */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Designation <span className="text-danger">*</span>
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted dark:text-slate-300">
                    <GraduationCap className="h-4 w-4" />
                  </div>
                  <select
                    value={designation}
                    onChange={(e) => setDesignation(e.target.value)}
                    className="h-11 w-full rounded-xl border border-line bg-canvas pl-10 pr-3.5 text-sm text-ink dark:text-white outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 font-bold appearance-none cursor-pointer"
                  >
                    <option value="Professor">Professor</option>
                    <option value="Associate Professor">Associate Professor</option>
                    <option value="Assistant Professor">Assistant Professor</option>
                    <option value="Lecturer">Lecturer</option>
                    <option value="Faculty">Faculty Member</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-semibold text-danger">
                {errorMsg}
              </div>
            )}

            {/* Progress Indicator */}
            <div className="text-center">
              <span className="text-xs font-semibold text-muted dark:text-slate-300">
                Almost ready — complete your profile to continue.
              </span>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isSubmitting}
              className="h-12 w-full gap-2 text-sm font-bold shadow-float"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Saving Profile…</span>
                </>
              ) : (
                <>
                  <span>Complete Profile</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>

          </form>

        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-muted dark:text-slate-400 font-semibold py-2">
        ClassroomIQ Teaching Intelligence Platform © {new Date().getFullYear()}
      </footer>
    </div>
  )
}
