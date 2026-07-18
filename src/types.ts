export type EntryType = 'Work' | 'Learning' | 'Appreciation'

export interface Entry {
  id: string
  type: EntryType
  content: string
  createdAt: string
}
