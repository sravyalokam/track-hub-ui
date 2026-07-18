import type { EntryType } from '../types'
import { ENTRY_TYPES } from '../entryTypeStyles'

export type FilterValue = 'All' | EntryType

interface FilterTabsProps {
  value: FilterValue
  onChange: (value: FilterValue) => void
}

export function FilterTabs({ value, onChange }: FilterTabsProps) {
  const options: FilterValue[] = ['All', ...ENTRY_TYPES]

  return (
    <div className="flex gap-2 border-b border-slate-200">
      {options.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            value === option
              ? 'border-slate-800 text-slate-900'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  )
}
