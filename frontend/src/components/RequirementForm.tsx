type RequirementFormProps = {
  value: string
  loading: boolean
  onChange: (value: string) => void
  onSubmit: () => void
}

export default function RequirementForm({ value, loading, onChange, onSubmit }: RequirementFormProps) {
  return (
    <section className="space-y-3 animate-rise">
      <label className="block">
        <span className="text-sm font-semibold text-slate-600">Natural-language requirement</span>
        <textarea
          className="mt-2 h-40 w-full rounded-xl border border-slate-300 bg-white p-4 text-sm outline-none transition focus:border-ember focus:ring-4 focus:ring-ember/15"
          placeholder="Ví dụ: Cần xây dựng dashboard theo dõi tiến độ học 3D theo từng team, có phân quyền manager và export báo cáo tuần."
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>

      <button
        onClick={onSubmit}
        disabled={loading || !value.trim()}
        className="rounded-xl bg-ember px-5 py-2.5 text-sm font-bold text-white transition hover:bg-[#cf5b11] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? 'Generating...' : 'Generate VTS Requirement'}
      </button>
    </section>
  )
}
