import { useState } from 'react'

const TABS = [
  { id: 'summary', label: 'Summary', dot: 'bg-amber' },
  { id: 'action_items', label: 'Action Items', dot: 'bg-teal' },
  { id: 'key_decisions', label: 'Key Decisions', dot: 'bg-coral' },
  { id: 'open_questions', label: 'Open Questions', dot: 'bg-muted' },
  { id: 'transcript', label: 'Full Transcript', dot: 'bg-line' },
]

function Content({ text }) {
  if (!text) return <p className="text-muted italic">Nothing here yet.</p>
  return (
    <div className="whitespace-pre-wrap leading-relaxed text-text/90 text-[15px]">
      {text}
    </div>
  )
}

export default function ResultView({ result, jobId }) {
  const [active, setActive] = useState('summary')

  const exportUrl = (type) => `/api/export/${jobId}/${type}`

  return (
    <div className="fade-in">
      <div className="flex items-start justify-between gap-6 mb-8 flex-wrap">
        <div>
          <p className="text-amber text-xs tracking-wide font-medium mb-2">Ready</p>
          <h2 className="font-display text-3xl md:text-4xl text-text leading-tight max-w-2xl">
            {result.title}
          </h2>
        </div>
        <div className="flex gap-2 shrink-0">
          <a
            href={exportUrl('pdf')}
            className="px-4 py-2 rounded-md border border-line text-sm text-text hover:border-amber hover:text-amber transition-colors"
          >
            Export PDF
          </a>
          <a
            href={exportUrl('txt')}
            className="px-4 py-2 rounded-md border border-line text-sm text-text hover:border-amber hover:text-amber transition-colors"
          >
            Export TXT
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-6">
        {/* Tab rail — channel-strip style */}
        <div className="flex md:flex-col gap-1 overflow-x-auto md:overflow-visible border-b md:border-b-0 md:border-r border-line pb-2 md:pb-0 md:pr-4">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActive(tab.id)}
              className={`flex items-center gap-2 text-left px-3 py-2.5 rounded-md text-sm whitespace-nowrap transition-colors ${
                active === tab.id
                  ? 'bg-surfaceAlt text-text'
                  : 'text-muted hover:text-text hover:bg-surfaceAlt/50'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${tab.dot}`} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Active pane */}
        <div className="bg-surface border border-line rounded-lg p-6 md:p-8 min-h-[280px] max-h-[520px] overflow-y-auto">
          <Content text={result[active]} />
        </div>
      </div>
    </div>
  )
}
