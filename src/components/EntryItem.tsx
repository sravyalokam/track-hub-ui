import type { Entry } from '../types'
import { entryTypeStyles } from '../entryTypeStyles'

interface EntryItemProps {
  entry: Entry
  onDelete: (id: string) => void
}

export function EntryItem({ entry, onDelete }: EntryItemProps) {
  const styles = entryTypeStyles[entry.type]
  const date = new Date(entry.createdAt)

  return (
    <li className={`bg-white rounded-lg shadow-sm border border-slate-200 border-l-4 ${styles.border} p-4 flex items-start justify-between gap-3`}>
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${styles.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
            {entry.type}
          </span>
          <span className="text-xs text-slate-400">
            {date.toLocaleDateString()} {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <p className="text-sm text-slate-700 whitespace-pre-wrap break-words">{entry.content}</p>
      </div>
      <button
        onClick={() => onDelete(entry.id)}
        aria-label="Delete entry"
        className="shrink-0 text-slate-400 hover:text-red-500 transition-colors text-sm"
      >
        ✕
      </button>
    </li>
  )
}
