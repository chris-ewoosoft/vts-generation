import { NavLink, Route, Routes } from 'react-router-dom'

import ChunkManagerPage from './pages/ChunkManagerPage'
import GeneratePage from './pages/GeneratePage'

const navItems = [
  { to: '/', label: 'Generate Ticket' },
  { to: '/chunks', label: 'Manage RAG Chunks' }
]

export default function App() {
  return (
    <div className="min-h-screen px-4 py-6 sm:px-8">
      <div className="mx-auto max-w-6xl animate-rise">
        <header className="mb-6 card-panel px-6 py-5 sm:flex sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ember">RAG Workspace</p>
            <h1 className="font-display text-2xl text-ink sm:text-3xl">VTS Requirement Generator</h1>
          </div>
          <nav className="mt-4 flex flex-wrap gap-2 sm:mt-0">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive ? 'bg-ink text-surf' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="card-panel p-4 sm:p-6">
          <Routes>
            <Route path="/" element={<GeneratePage />} />
            <Route path="/chunks" element={<ChunkManagerPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
