import { useEffect, useState } from 'react'

import {
  createChunk,
  deleteChunk,
  getChunks,
  updateChunk,
  type ChunkPayload,
  type ChunkRecord
} from '../api/client'
import ChunkEditor from '../components/ChunkEditor'
import ChunkList from '../components/ChunkList'

const SECTIONS = ['general', 'background', 'purpose', 'process', 'considerable_factors', 'resulting_image']

export default function ChunkManagerPage() {
  const [chunks, setChunks] = useState<ChunkRecord[]>([])
  const [filter, setFilter] = useState('')
  const [editing, setEditing] = useState<ChunkRecord | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setError('')
      const result = await getChunks(filter || undefined)
      setChunks(Array.isArray(result) ? result : [])
    } catch (err) {
      setChunks([])
      setError(err instanceof Error ? err.message : 'Không thể tải danh sách chunks.')
    }
  }

  useEffect(() => {
    load()
  }, [filter])

  const handleSave = async (payload: ChunkPayload) => {
    try {
      if (payload.id) {
        await updateChunk(payload.id, payload)
      } else {
        await createChunk(payload)
      }
      setShowEditor(false)
      setEditing(null)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Lưu chunk thất bại.')
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Xóa chunk này?')) {
      return
    }
    try {
      await deleteChunk(id)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Xóa chunk thất bại.')
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-2xl text-ink">RAG Chunk Manager</h2>
        <button
          onClick={() => {
            setEditing(null)
            setShowEditor(true)
          }}
          className="rounded-xl bg-moss px-4 py-2 text-sm font-bold text-white hover:bg-[#24897d]"
        >
          + Add Chunk
        </button>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {['', ...SECTIONS].map((section) => (
          <button
            key={section || 'all'}
            onClick={() => setFilter(section)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide transition ${
              filter === section
                ? 'border-ink bg-ink text-white'
                : 'border-slate-300 bg-white text-slate-600 hover:border-ember'
            }`}
          >
            {section || 'all'}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Không tải được dữ liệu chunks: {error}
        </div>
      )}

      <ChunkList
        chunks={chunks}
        onEdit={(chunk) => {
          setEditing(chunk)
          setShowEditor(true)
        }}
        onDelete={handleDelete}
      />

      {showEditor && <ChunkEditor chunk={editing} sections={SECTIONS} onSave={handleSave} onClose={() => setShowEditor(false)} />}
    </div>
  )
}
