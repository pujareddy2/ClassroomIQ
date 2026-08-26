import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './app-shell'
import { ProtectedRoute } from './protected-route'
import { LandingPage } from '@/pages/landing-page'
import { LoginPage } from '@/pages/login-page'
import { RegisterPage } from '@/pages/register-page'
import { ProfileSetupPage } from '@/pages/profile-setup-page'
import { CoursesPage } from '@/pages/courses-page'
import { CourseMaterialsPage } from '@/pages/course-materials-page'
import { LecturesPage } from '@/pages/lectures-page'
import { AiResultsPage } from '@/pages/ai-results-page'
import { HistoryPage } from '@/pages/history-page'
import { 
  AnalyticsPage, 
  CoveragePage, 
  CurriculumPage, 
  DashboardPage, 
  ExplainabilityPage, 
  ProfilePage, 
  RecommendationsPage, 
  ReferenceMaterialsPage, 
  ReportsPage, 
  SettingsPage, 
  SupportPage, 
  TeachingPage, 
  ValidationPage 
} from '@/pages/module-pages'

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/profile-setup', element: <ProfileSetupPage /> },
      {
        element: <AppShell />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/courses', element: <CoursesPage /> },
          { path: '/courses/:courseId/materials', element: <CourseMaterialsPage /> },
          { path: '/curriculum', element: <CurriculumPage /> },
          { path: '/reference-materials', element: <CourseMaterialsPage /> },
          { path: '/lectures', element: <LecturesPage /> },
          { path: '/history', element: <HistoryPage /> },
          { path: '/results', element: <AiResultsPage /> },
          { path: '/courses/:courseId/lectures/:lectureId/results', element: <AiResultsPage /> },
          { path: '/coverage', element: <CoveragePage /> },
          { path: '/validation', element: <ValidationPage /> },
          { path: '/teaching', element: <TeachingPage /> },
          { path: '/recommendations', element: <RecommendationsPage /> },
          { path: '/explainability', element: <ExplainabilityPage /> },
          { path: '/analytics', element: <AnalyticsPage /> },
          { path: '/reports', element: <ReportsPage /> },
          { path: '/profile', element: <ProfilePage /> },
          { path: '/settings', element: <SettingsPage /> },
          { path: '/support', element: <SupportPage /> }
        ]
      }
    ]
  }
])
