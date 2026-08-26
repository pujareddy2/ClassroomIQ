import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { router } from '@/app/routes'
import { shouldRetry } from '@/hooks/use-api-query'
import '@/styles/index.css'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: shouldRetry, refetchOnWindowFocus: false } } })
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><RouterProvider router={router}/><Toaster position="bottom-right"/></QueryClientProvider></StrictMode>)
