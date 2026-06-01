export type VTSOutput = {
  background: string
  purpose: string
  process: string
  considerable_factors: string
  resulting_image: string
}

export type ChunkRecord = {
  id: string
  title: string
  content: string
  section: string
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type ChunkPayload = {
  id?: string
  title: string
  content: string
  section?: string
  metadata?: Record<string, unknown>
}

const envBase = import.meta.env.VITE_API_URL as string | undefined

function resolveBaseUrl(): string {
  const host = window.location.hostname
  const protocol = window.location.protocol

  if (!envBase) {
    return `${protocol}//${host}:8001`
  }

  const isRemoteHost = host !== 'localhost' && host !== '127.0.0.1'
  if (!isRemoteHost) {
    return envBase
  }

  // If VITE_API_URL still points to loopback, rewrite it to the current host for LAN access.
  return envBase
    .replace('://localhost', `://${host}`)
    .replace('://127.0.0.1', `://${host}`)
}

const BASE = resolveBaseUrl()

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return (await res.json()) as T
}

export function generateRequirement(user_input: string) {
  return request<VTSOutput>('/api/generate', {
    method: 'POST',
    body: JSON.stringify({ user_input })
  })
}

export function getChunks(section?: string) {
  const query = section ? `?section=${encodeURIComponent(section)}` : ''
  return request<ChunkRecord[]>(`/api/chunks/${query}`)
}

export function createChunk(data: ChunkPayload) {
  return request<{ id: string; message: string }>('/api/chunks/', {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export function updateChunk(id: string, data: ChunkPayload) {
  return request<{ message: string }>(`/api/chunks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  })
}

export function deleteChunk(id: string) {
  return request<{ message: string }>(`/api/chunks/${id}`, {
    method: 'DELETE'
  })
}
