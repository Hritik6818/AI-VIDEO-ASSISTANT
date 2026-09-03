import { useState, useEffect, useRef } from "react";
import Loader from "./components/Loader.jsx";
import ResultView from "./components/ResultView.jsx";
import ChatPanel from "./components/ChatPanel.jsx";

const LANGUAGES = [
  { id: "english", label: "English" },
  { id: "hindi", label: "Hindi" },
  { id: "hinglish", label: "Hinglish" },
];

function WaveformMark() {
  return (
    <div className="flex items-end gap-[3px] h-6">
      {[10, 18, 24, 14, 20, 9].map((h, i) => (
        <span
          key={i}
          className="wave-bar w-[3px] bg-amber rounded-full"
          style={{ height: `${h}px`, animationDelay: `${i * 0.08}s` }}
        />
      ))}
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState("url"); // 'url' | 'file'
  const [url, setUrl] = useState("");
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState("english");

  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null); // null | queued | downloading | ... | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const pollRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setResult(null);

    let source = url.trim();

    try {
      if (mode === "file") {
        if (!file) {
          setError("Choose a file first.");
          return;
        }
        const formData = new FormData();
        formData.append("file", file);
        setStatus("queued");
        const uploadRes = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });
        if (!uploadRes.ok) throw new Error("Upload failed");
        const uploadData = await uploadRes.json();
        source = uploadData.path;
      } else {
        if (!source) {
          setError("Paste a YouTube URL first.");
          return;
        }
      }

      setStatus("queued");
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, language }),
      });
      if (!res.ok) throw new Error("Failed to start processing");
      const data = await res.json();
      setJobId(data.job_id);
      startPolling(data.job_id);
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setStatus(null);
    }
  }

  function startPolling(id) {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${id}`);
        const data = await res.json();
        setStatus(data.status);

        if (data.status === "done") {
          clearInterval(pollRef.current);
          const resultRes = await fetch(`/api/result/${id}`);
          const resultData = await resultRes.json();
          setResult(resultData);
        } else if (data.status === "error") {
          clearInterval(pollRef.current);
          setError(data.error || "Processing failed.");
        }
      } catch {
        clearInterval(pollRef.current);
        setError("Lost connection to the server.");
      }
    }, 1800);
  }

  function reset() {
    setJobId(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setUrl("");
    setFile(null);
  }

  const isBusy = status && status !== "done" && status !== "error";

  return (
    <div className="min-h-screen bg-ink">
      {/* Top bar */}
      <header className="border-b border-line">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <button onClick={reset} className="flex items-center gap-3">
            <WaveformMark />
            <span className="font-display text-lg text-text">Meridian</span>
          </button>
          <span className="text-muted text-xs">
            Local transcription · Private by default
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-14 md:py-20">
        {!jobId && (
          <section className="fade-in">
            <p className="text-amber text-sm tracking-wide mb-4">
              AI Meeting Assistant
            </p>
            <h1 className="font-display text-4xl md:text-6xl leading-[1.05] text-text max-w-2xl mb-6">
              Every meeting, distilled to what mattered.
            </h1>
            <p className="text-muted text-lg max-w-lg mb-12">
              Drop in a YouTube link or a recording. Get a transcript, a
              summary, the decisions that were made, and a chat window to ask it
              anything — in English, Hindi, or Hinglish.
            </p>

            <form
              onSubmit={handleSubmit}
              className="bg-surface border border-line rounded-xl p-6 md:p-8 max-w-2xl"
            >
              <div className="flex gap-1 mb-6 bg-ink rounded-md p-1 w-fit">
                <button
                  type="button"
                  onClick={() => setMode("url")}
                  className={`px-4 py-1.5 rounded text-sm transition-colors ${
                    mode === "url" ? "bg-surfaceAlt text-text" : "text-muted"
                  }`}
                >
                  YouTube URL
                </button>
                <button
                  type="button"
                  onClick={() => setMode("file")}
                  className={`px-4 py-1.5 rounded text-sm transition-colors ${
                    mode === "file" ? "bg-surfaceAlt text-text" : "text-muted"
                  }`}
                >
                  Upload File
                </button>
              </div>

              {mode === "url" ? (
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=…"
                  className="w-full bg-ink border border-line rounded-md px-4 py-3 text-text placeholder-muted focus:border-amber transition-colors"
                />
              ) : (
                <label className="flex items-center justify-center w-full border border-dashed border-line rounded-md px-4 py-8 text-muted hover:border-amber hover:text-text cursor-pointer transition-colors">
                  <input
                    type="file"
                    accept="audio/*,video/*"
                    className="hidden"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  {file ? file.name : "Click to choose an audio or video file"}
                </label>
              )}

              <div className="flex items-center gap-3 mt-5 mb-6">
                <span className="text-muted text-sm">Language</span>
                <div className="flex gap-1">
                  {LANGUAGES.map((l) => (
                    <button
                      type="button"
                      key={l.id}
                      onClick={() => setLanguage(l.id)}
                      className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
                        language === l.id
                          ? "border-amber text-amber"
                          : "border-line text-muted hover:text-text"
                      }`}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              </div>

              {error && <p className="text-coral text-sm mb-4">{error}</p>}

              <button
                type="submit"
                className="w-full bg-amber text-ink font-medium py-3 rounded-md hover:bg-amberDim transition-colors"
              >
                Process Meeting
              </button>
            </form>
          </section>
        )}

        {isBusy && <Loader status={status} />}

        {status === "error" && !result && (
          <div className="fade-in text-center py-16">
            <p className="text-coral font-display text-2xl mb-3">
              That didn't go through.
            </p>
            <p className="text-muted mb-6">{error}</p>
            <button
              onClick={reset}
              className="px-5 py-2.5 rounded-md border border-line text-text hover:border-amber hover:text-amber transition-colors"
            >
              Try another meeting
            </button>
          </div>
        )}

        {result && (
          <>
            <ResultView result={result} jobId={jobId} />
            <ChatPanel jobId={jobId} />
            <div className="mt-10 text-center">
              <button
                onClick={reset}
                className="text-muted text-sm hover:text-amber transition-colors"
              >
                Process another meeting →
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

// python -m uvicorn api.main:app --reload --port 8000
