import { useState } from 'react'
import type { EntryType } from '../types'
import { ENTRY_TYPES } from '../entryTypeStyles'

interface EntryFormProps {
  onAdd: (type: EntryType, content: string) => void
}

export function EntryForm({ onAdd }: EntryFormProps) {
  const [type, setType] = useState<EntryType>('Work')
  const [content, setContent] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = content.trim()
    if (!trimmed) return
    onAdd(type, trimmed)
    setContent('')
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 space-y-3">
      <div className="flex gap-2">
        {ENTRY_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setType(t)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              type === t
                ? 'bg-slate-800 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="What happened?"
        rows={3}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 resize-none"
      />
      <button
        type="submit"
        className="w-full sm:w-auto px-4 py-2 rounded-md bg-slate-800 text-white text-sm font-medium hover:bg-slate-700 transition-colors"
      >
        Add entry
      </button>
    </form>
  )
}
