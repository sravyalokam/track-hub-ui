import type { Entry } from '../types'
import { EntryItem } from './EntryItem'

interface EntryListProps {
  entries: Entry[]
  onDelete: (id: string) => void
}

export function EntryList({ entries, onDelete }: EntryListProps) {
  if (entries.length === 0) {
    return <p className="text-sm text-slate-400 text-center py-8">No entries yet.</p>
  }

  return (
    <ul className="space-y-2">
      {entries.map((entry) => (
        <EntryItem key={entry.id} entry={entry} onDelete={onDelete} />
      ))}
    </ul>
  )
}
