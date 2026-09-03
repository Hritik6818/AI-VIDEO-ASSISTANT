import { useState, useRef, useEffect } from 'react'

export default function ChatPanel({ jobId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  async function send() {
    const question = input.trim()
    if (!question || thinking) return

    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    setThinking(true)

    try {
      const res = await fetch(`/api/chat/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) throw new Error('Chat request failed')
      const data = await res.json()
      setMessages((m) => [...m, { role: 'assistant', text: data.answer }])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: 'Something went wrong reaching the assistant. Try again.' },
      ])
    } finally {
      setThinking(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="mt-10 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1.5 h-1.5 rounded-full bg-amber" />
        <h3 className="font-display text-xl text-text">Ask the meeting</h3>
      </div>

      <div className="bg-surface border border-line rounded-lg overflow-hidden">
        <div ref={scrollRef} className="max-h-80 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <p className="text-muted text-sm">
              Ask anything — "What did we decide about the budget?" or "Summarize what Priya said."
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-amber text-ink font-medium'
                    : 'bg-surfaceAlt text-text/90 border border-line'
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {thinking && (
            <div className="flex justify-start">
              <div className="bg-surfaceAlt border border-line rounded-lg px-4 py-2.5 flex gap-1 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse [animation-delay:300ms]" />
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-line flex items-end gap-2 p-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask a question about this meeting…"
            className="flex-1 resize-none bg-transparent text-text placeholder-muted text-sm px-2 py-2 focus:outline-none"
          />
          <button
            onClick={send}
            disabled={thinking || !input.trim()}
            className="px-4 py-2 rounded-md bg-amber text-ink text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-amberDim transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
