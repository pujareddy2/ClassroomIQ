import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { NotificationItem } from '@/types/api'

type Theme = 'light' | 'dark' | 'system'
type UiState = { theme: Theme; sidebarCollapsed: boolean; searchOpen: boolean; notificationsOpen: boolean; notifications: NotificationItem[]; setTheme: (theme: Theme) => void; toggleSidebar: () => void; setSearchOpen: (open: boolean) => void; setNotificationsOpen: (open: boolean) => void; addNotification: (notification: NotificationItem) => void; markAllRead: () => void }
export const useUiStore = create<UiState>()(persist((set) => ({
  theme: 'system', sidebarCollapsed: false, searchOpen: false, notificationsOpen: false,
  notifications: [],
  setTheme: (theme) => set({ theme }), toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })), setSearchOpen: (searchOpen) => set({ searchOpen }), setNotificationsOpen: (notificationsOpen) => set({ notificationsOpen }), addNotification: (notification) => set((state) => ({ notifications: [notification, ...state.notifications] })), markAllRead: () => set((state) => ({ notifications: state.notifications.map((item) => ({ ...item, read: true })) }))
}), { name: 'classroomiq-ui' }))
