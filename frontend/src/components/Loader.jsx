const STAGE_LABELS = {
  queued: 'Queued',
  downloading: 'Pulling audio',
  transcribing: 'Transcribing speech',
  summarizing: 'Drafting summary',
  extracting: 'Finding decisions & action items',
  indexing: 'Indexing for chat',
}

const STAGE_ORDER = ['queued', 'downloading', 'transcribing', 'summarizing', 'extracting', 'indexing']

export default function Loader({ status }) {
  const currentIndex = STAGE_ORDER.indexOf(status)
  const label = STAGE_LABELS[status] || 'Working'

  return (
    <div className="flex flex-col items-center justify-center py-20 fade-in">
      <div className="flex items-end gap-[3px] h-14 mb-8">
        {Array.from({ length: 24 }).map((_, i) => (
          <span
            key={i}
            className="wave-bar w-[3px] bg-amber rounded-full"
            style={{
              height: `${18 + (i % 5) * 8}px`,
              animationDelay: `${i * 0.045}s`,
            }}
          />
        ))}
      </div>

      <p className="font-display text-2xl text-text mb-6">{label}&hellip;</p>

      <div className="flex items-center gap-2">
        {STAGE_ORDER.slice(1).map((stage, i) => {
          const idx = i + 1
          const reached = currentIndex >= idx
          return (
            <div
              key={stage}
              className={`h-1.5 w-10 rounded-full transition-colors duration-500 ${
                reached ? 'bg-amber' : 'bg-line'
              }`}
            />
          )
        })}
      </div>

      <p className="text-muted text-sm mt-6 max-w-xs text-center">
        Longer meetings take a few minutes — transcription and indexing run locally.
      </p>
    </div>
  )
}
