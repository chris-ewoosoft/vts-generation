import { useState } from 'react'

import { generateRequirement, type VTSOutput as VTSOutputType } from '../api/client'
import VTSOutput from '../components/VTSOutput'
import RequirementForm from '../components/RequirementForm'

export default function GeneratePage() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState<VTSOutputType | null>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!input.trim()) {
      return
    }
    setLoading(true)
    try {
      const result = await generateRequirement(input)
      setOutput(result)
    } catch {
      alert('Lỗi khi generate. Kiểm tra backend và Ollama đang chạy.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <RequirementForm value={input} loading={loading} onChange={setInput} onSubmit={handleGenerate} />
      {output && <VTSOutput data={output} />}
    </div>
  )
}
