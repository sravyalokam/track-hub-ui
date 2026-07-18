import { useMemo, useState } from 'react'
import type { Entry, EntryType } from './types'
import { useLocalStorage } from './hooks/useLocalStorage'
import { EntryForm } from './components/EntryForm'
import { EntryList } from './components/EntryList'
import { FilterTabs, type FilterValue } from './components/FilterTabs'

function App() {
  const [entries, setEntries] = useLocalStorage<Entry[]>('track-hub:entries', [])
  const [filter, setFilter] = useState<FilterValue>('All')

  function handleAdd(type: EntryType, content: string) {
    const entry: Entry = {
      id: crypto.randomUUID(),
      type,
      content,
      createdAt: new Date().toISOString(),
    }
    setEntries((prev) => [entry, ...prev])
  }

  function handleDelete(id: string) {
    setEntries((prev) => prev.filter((entry) => entry.id !== id))
  }

  const filteredEntries = useMemo(
    () => (filter === 'All' ? entries : entries.filter((entry) => entry.type === filter)),
    [entries, filter],
  )

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <header>
          <h1 className="text-xl font-semibold text-slate-900">Track Hub</h1>
          <p className="text-sm text-slate-500">Log your work, learnings, and kudos.</p>
        </header>

        <EntryForm onAdd={handleAdd} />

        <div className="space-y-3">
          <FilterTabs value={filter} onChange={setFilter} />
          <EntryList entries={filteredEntries} onDelete={handleDelete} />
        </div>
      </div>
    </div>
  )
}

export default App
