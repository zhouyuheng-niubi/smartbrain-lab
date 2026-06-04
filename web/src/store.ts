import { create } from 'zustand'

export interface Toast { id: number; text: string; kind: 'info' | 'error' | 'good' }

interface UIState {
  toasts: Toast[]
  notify: (text: string, kind?: Toast['kind']) => void
  dismiss: (id: number) => void
}

let _id = 0

export const useUI = create<UIState>((set) => ({
  toasts: [],
  notify: (text, kind = 'info') => {
    const id = ++_id
    set((s) => ({ toasts: [...s.toasts, { id, text, kind }] }))
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 3500)
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
