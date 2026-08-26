import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Footer } from '@/layout/footer'
import { Header } from '@/layout/header'
import { MobileSidebar, Sidebar } from '@/layout/navigation'
import { GlobalSearch, NotificationPanel } from '@/layout/overlays'
import { AssistantPanel } from '@/layout/assistant-panel'
import { useUiStore } from '@/store/ui-store'

export function AppShell() { const [mobileOpen, setMobileOpen] = useState(false); const { sidebarCollapsed } = useUiStore(); return <div className="min-h-screen"><Sidebar/><MobileSidebar open={mobileOpen} close={() => setMobileOpen(false)}/><div className={sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-[264px]'}><Header onOpenMobile={() => setMobileOpen(true)}/><main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-[1600px] flex-col px-4 sm:px-6 lg:px-8"><div className="py-8"><Outlet/></div><Footer/></main></div><GlobalSearch/><NotificationPanel/><AssistantPanel/></div> }
