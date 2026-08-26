import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type AssistantMessage = { id: string; role: 'user' | 'assistant'; content: string; createdAt: string }
type AssistantState = { open: boolean; messages: AssistantMessage[]; setOpen: (open: boolean) => void; addMessage: (message: AssistantMessage) => void }
export const useAssistantStore = create<AssistantState>()(persist((set) => ({ open: false, messages: [], setOpen: (open) => set({ open }), addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })) }), { name: 'classroomiq-assistant' }))
