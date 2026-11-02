import React from 'react';
import { moderateImage, moderateText, moderateVideo, ModerationResult } from './lib/api';
import { ModerationResultCard } from './components/ModerationResultCard';
import { motion } from 'framer-motion';
import { AlertCircle, FileImage, FileVideo, Loader2, ShieldCheck, Type } from 'lucide-react';

type Mode = 'image' | 'text' | 'video';

const modes: { id: Mode; label: string; icon: typeof FileImage }[] = [
  { id: 'image', label: 'Image', icon: FileImage },
  { id: 'text', label: 'Text', icon: Type },
  { id: 'video', label: 'Video', icon: FileVideo },
];

export default function App() {
  const [mode, setMode] = React.useState<Mode>('image');
  const [result, setResult] = React.useState<ModerationResult | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [preview, setPreview] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [caption, setCaption] = React.useState('');
  const [text, setText] = React.useState('');
  const [file, setFile] = React.useState<File | null>(null);

  const selectMode = (nextMode: Mode) => {
    setMode(nextMode);
    setResult(null);
    setError(null);
    setPreview(null);
    setFile(null);
  };

  const runModeration = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      if (mode === 'text') setResult(await moderateText(text));
      if (mode === 'image' && file) setResult(await moderateImage(file, caption));
      if (mode === 'video' && file) setResult(await moderateVideo(file, caption));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Moderation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFile = (nextFile?: File) => {
    setResult(null);
    setError(null);
    setFile(nextFile || null);
    setPreview(nextFile && mode === 'image' ? URL.createObjectURL(nextFile) : null);
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center overflow-hidden bg-[#07080c] px-5 py-10 text-neutral-100 sm:px-8">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(79,70,229,0.18),transparent_48%)]" />
      <header className="relative mb-10 mt-4 max-w-2xl text-center sm:mb-12">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/5 px-3 py-1.5 text-xs font-medium text-indigo-200">
          <ShieldCheck size={15} /> Guardian AI · Multimodal safety
        </div>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          Content <span className="bg-gradient-to-r from-indigo-300 to-violet-400 bg-clip-text text-transparent">moderation</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-neutral-400 sm:text-base">
          Review images, text, and video with explainable, context-aware safety signals.
        </p>
      </header>

      <section className="relative w-full max-w-2xl rounded-3xl border border-white/10 bg-neutral-950/75 p-4 shadow-2xl shadow-black/30 sm:p-7">
        <div role="tablist" aria-label="Content type" className="mb-6 grid grid-cols-3 rounded-2xl border border-white/5 bg-black/40 p-1">
          {modes.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" role="tab" aria-selected={mode === id} onClick={() => selectMode(id)}
              className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition ${mode === id ? 'bg-neutral-800 text-white shadow' : 'text-neutral-500 hover:text-neutral-200'}`}>
              <Icon size={16} />{label}
            </button>
          ))}
        </div>

        <form onSubmit={runModeration} className="space-y-5">
          {mode === 'text' ? (
            <label className="block text-sm font-medium text-neutral-300">
              Text to review
              <textarea value={text} onChange={(event) => setText(event.target.value)} required rows={6} maxLength={10000}
                placeholder="Paste a comment, message, or caption…"
                className="mt-2 w-full resize-y rounded-2xl border border-neutral-800 bg-black/40 p-4 text-sm leading-6 text-neutral-100 outline-none transition placeholder:text-neutral-600 focus:border-indigo-500" />
              <span className="mt-1 block text-right text-xs text-neutral-600">{text.length}/10,000</span>
            </label>
          ) : (
            <>
              <label className="flex min-h-48 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-neutral-700 bg-black/30 p-6 text-center transition hover:border-indigo-400/70 hover:bg-indigo-400/[0.03]">
                {preview ? <img src={preview} alt="Selected image preview" className="mb-4 max-h-40 rounded-xl object-contain" /> : mode === 'image' ? <FileImage size={28} className="mb-3 text-neutral-500" /> : <FileVideo size={28} className="mb-3 text-neutral-500" />}
                <span className="text-sm font-medium text-neutral-200">{file?.name || `Choose ${mode === 'image' ? 'an' : 'a'} ${mode} to analyze`}</span>
                <span className="mt-1 text-xs text-neutral-500">{mode === 'video' ? 'MP4, MOV, AVI · sampled frames' : 'PNG, JPG, WEBP'}</span>
                <input className="sr-only" type="file" accept={mode === 'image' ? 'image/*' : 'video/*'} required onChange={(event) => handleFile(event.target.files?.[0])} />
              </label>
              <label className="block text-sm font-medium text-neutral-300">
                Context <span className="font-normal text-neutral-600">(optional)</span>
                <input value={caption} onChange={(event) => setCaption(event.target.value)} maxLength={500}
                  placeholder="Add a caption or describe the context"
                  className="mt-2 w-full rounded-xl border border-neutral-800 bg-black/40 px-4 py-3 text-sm text-neutral-100 outline-none transition placeholder:text-neutral-600 focus:border-indigo-500" />
              </label>
            </>
          )}
          <button type="submit" disabled={loading || (mode === 'text' && !text.trim()) || (mode !== 'text' && !file)}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-50">
            {loading ? <><Loader2 size={17} className="animate-spin" /> Analyzing…</> : <><ShieldCheck size={17} /> Analyze {mode}</>}
          </button>
        </form>

        {error && <div role="alert" className="mt-5 flex gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-200"><AlertCircle size={18} className="mt-0.5 shrink-0" />{error}</div>}
        {result && <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-7"><ModerationResultCard result={result} /></motion.div>}
      </section>

      <footer className="relative mt-auto pt-10 text-center text-xs text-neutral-600">Guardian AI · Decision support for human review</footer>
    </main>
  );
}
