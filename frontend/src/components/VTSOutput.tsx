import type { VTSOutput as VTSOutputType } from '../api/client'

const SECTIONS = [
  { key: 'background', label: 'Background' },
  { key: 'purpose', label: 'Purpose' },
  { key: 'process', label: 'Process\n(including request items)' },
  { key: 'considerable_factors', label: 'Considerable factors' },
  { key: 'resulting_image', label: 'Resulting Image' }
] as const

export default function VTSOutput({ data }: { data: VTSOutputType }) {
  const copyAll = async () => {
    const text = SECTIONS.map((section) => `### ${section.label}\n${data[section.key] ?? ''}`).join('\n\n')
    await navigator.clipboard.writeText(text)
  }

  return (
    <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft animate-rise">
      <header className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h2 className="font-display text-lg text-ink">Generated VTS Requirement</h2>
        <button onClick={copyAll} className="text-sm font-semibold text-moss hover:underline">
          Copy all
        </button>
      </header>

      {SECTIONS.map((section) => (
        <article key={section.key} className="flex border-b border-slate-100 last:border-none">
          <aside className="w-44 shrink-0 bg-ink p-4 text-xs font-semibold uppercase tracking-wide text-slate-100">
            <span className="whitespace-pre-line">{section.label}</span>
          </aside>
          <div className="flex-1 whitespace-pre-wrap p-4 text-sm leading-6 text-slate-700">
            {data[section.key] || 'NA'}
          </div>
        </article>
      ))}
    </section>
  )
}
