import type { FormEvent } from "react";
import { useState } from "react";

type NamePromptModalProps = {
  isOpen: boolean;
  onStart: (name: string) => void;
};

export function NamePromptModal({ isOpen, onStart }: NamePromptModalProps) {
  const [name, setName] = useState("");

  if (!isOpen) return null;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;
    onStart(trimmedName);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl">
        <h2 className="text-2xl font-semibold tracking-tight text-neutral-900">
          Welcome
        </h2>
        <p className="mt-2 text-sm text-stone-500">
          Enter your name to start a new chat session.
        </p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-3">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Your name"
            className="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-base text-neutral-900 outline-none transition-colors focus:border-stone-400"
            autoFocus
          />
          <button
            type="submit"
            disabled={!name.trim()}
            className="w-full rounded-xl bg-neutral-900 px-3.5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-85 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Start Chat
          </button>
        </form>
      </div>
    </div>
  );
}
