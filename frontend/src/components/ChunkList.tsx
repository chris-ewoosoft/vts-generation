import type { ChunkRecord } from '../api/client'

type ChunkListProps = {
  chunks: ChunkRecord[]
  onEdit: (chunk: ChunkRecord) => void
  onDelete: (id: string) => void
}

export default function ChunkList({ chunks, onEdit, onDelete }: ChunkListProps) {
  if (chunks.length === 0) {
    return <p className="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-slate-500">No chunks found.</p>
  }

  return (
    <div className="space-y-3">
      {chunks.map((chunk, idx) => (
        <div
          key={chunk.id}
          className="animate-rise rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          style={{ animationDelay: `${idx * 40}ms` }}
        >
          <div className="mb-2 flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-800">{chunk.title}</h3>
              <p className="mt-1 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                {chunk.section || 'general'}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onEdit(chunk)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-moss"
              >
                Edit
              </button>
              <button
                onClick={() => onDelete(chunk.id)}
                className="rounded-lg border border-red-300 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          </div>
          <p className="line-clamp-4 whitespace-pre-wrap text-sm text-slate-600">{chunk.content}</p>
        </div>
      ))}
    </div>
  )
}
