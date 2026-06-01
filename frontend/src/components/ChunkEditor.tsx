import { useMemo, useState } from 'react'

import type { ChunkPayload, ChunkRecord } from '../api/client'

type ChunkEditorProps = {
  chunk: ChunkRecord | null
  sections: string[]
  onSave: (payload: ChunkPayload) => Promise<void>
  onClose: () => void
}

export default function ChunkEditor({ chunk, sections, onSave, onClose }: ChunkEditorProps) {
  const initial = useMemo(
    () => ({
      id: chunk?.id,
      title: chunk?.title ?? '',
      content: chunk?.content ?? '',
      section: chunk?.section ?? 'general',
      metadata: chunk?.metadata ? JSON.stringify(chunk.metadata, null, 2) : '{}'
    }),
    [chunk]
  )

  const [title, setTitle] = useState(initial.title)
  const [content, setContent] = useState(initial.content)
  const [section, setSection] = useState(initial.section)
  const [metadata, setMetadata] = useState(initial.metadata)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) {
      alert('Title và content là bắt buộc.')
      return
    }

    let metadataObj: Record<string, unknown> = {}
    try {
      metadataObj = metadata.trim() ? (JSON.parse(metadata) as Record<string, unknown>) : {}
    } catch {
      alert('Metadata phải là JSON hợp lệ.')
      return
    }

    setSaving(true)
    try {
      await onSave({
        id: initial.id,
        title,
        content,
        section,
        metadata: metadataObj
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-900/45 p-4">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-5 shadow-2xl animate-rise">
        <h2 className="font-display text-xl text-ink">{chunk ? 'Edit Chunk' : 'Add Chunk'}</h2>

        <div className="mt-4 grid gap-3">
          <input
            className="rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-ember"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <select
            className="rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-ember"
            value={section}
            onChange={(e) => setSection(e.target.value)}
          >
            {sections.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <textarea
            className="h-44 rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-ember"
            placeholder="Chunk content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />

          <textarea
            className="h-28 rounded-xl border border-slate-300 p-3 font-mono text-xs outline-none focus:border-ember"
            placeholder="Metadata JSON"
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
          />
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
