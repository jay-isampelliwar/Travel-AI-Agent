type SessionInfoBadgeProps = {
  userId: string;
  sessionId: string;
  threadId: string;
};

export function SessionInfoBadge({
  userId,
  sessionId,
  threadId,
}: SessionInfoBadgeProps) {
  return (
    <aside className="fixed top-4 right-4 z-40 max-w-xs rounded-xl border border-stone-200 bg-white/95 p-3 text-xs shadow-lg backdrop-blur">
      <p className="font-semibold uppercase tracking-wide text-stone-500">
        Session Info
      </p>
      <p className="mt-1 text-stone-700">
        <span className="font-medium text-neutral-900">User:</span> {userId}
      </p>
      <p className="mt-1 break-all text-stone-700">
        <span className="font-medium text-neutral-900">Session:</span>{" "}
        {sessionId}
      </p>
      <p className="mt-1 break-all text-stone-700">
        <span className="font-medium text-neutral-900">Thread:</span> {threadId}
      </p>
    </aside>
  );
}
