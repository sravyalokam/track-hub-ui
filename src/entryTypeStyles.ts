import type { EntryType } from './types'

export const ENTRY_TYPES: EntryType[] = ['Work', 'Learning', 'Appreciation']

export const entryTypeStyles: Record<EntryType, { badge: string; border: string; dot: string }> = {
  Work: {
    badge: 'bg-blue-100 text-blue-700',
    border: 'border-l-blue-400',
    dot: 'bg-blue-500',
  },
  Learning: {
    badge: 'bg-amber-100 text-amber-700',
    border: 'border-l-amber-400',
    dot: 'bg-amber-500',
  },
  Appreciation: {
    badge: 'bg-emerald-100 text-emerald-700',
    border: 'border-l-emerald-400',
    dot: 'bg-emerald-500',
  },
}
