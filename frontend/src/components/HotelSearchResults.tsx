export type HotelResultItem = {
  name: string;
  url: string;
  price: number;
  description: string;
  rating: number;
};

type HotelSearchResultsProps = {
  results: HotelResultItem[];
};

export function HotelSearchResults({ results }: HotelSearchResultsProps) {
  if (!results.length) return null;

  return (
    <aside className="hidden h-full w-full max-w-sm flex-col border-l border-stone-200 bg-stone-50/80 p-4 lg:flex">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">
        Stays for you
      </h2>
      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {results.map((item) => (
          <button
            key={item.url}
            type="button"
            onClick={() => window.open(item.url, "_blank")}
            className="group flex w-full flex-col items-start gap-1.5 rounded-2xl border border-stone-200 bg-white px-3.5 py-3 text-left shadow-sm transition-all hover:-translate-y-px hover:border-stone-300 hover:shadow-md"
          >
            <div className="flex w-full items-start justify-between gap-2">
              <p className="line-clamp-2 text-sm font-semibold text-neutral-900">
                {item.name}
              </p>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {item.rating.toFixed(1)}
              </span>
            </div>
            <p className="line-clamp-2 text-xs text-stone-500">
              {item.description}
            </p>
            <p className="mt-1 text-sm font-semibold text-neutral-900">
              {item.price.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}{" "}
              <span className="text-xs font-normal text-stone-500">
                / night approx.
              </span>
            </p>
          </button>
        ))}
      </div>
    </aside>
  );
}

export function HotelSearchResultsSkeleton() {
  const placeholders = Array.from({ length: 4 });

  return (
    <aside className="hidden h-full w-full max-w-sm flex-col border-l border-stone-200 bg-stone-50/80 p-4 lg:flex">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-stone-400">
        Finding stays…
      </h2>
      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {placeholders.map((_, idx) => (
          <div
            // eslint-disable-next-line react/no-array-index-key
            key={idx}
            className="animate-pulse rounded-2xl border border-stone-200 bg-white px-3.5 py-3"
          >
            <div className="mb-2 flex items-start justify-between gap-2">
              <div className="h-4 w-40 rounded bg-stone-200" />
              <div className="h-5 w-10 rounded-full bg-emerald-100" />
            </div>
            <div className="mb-2 h-3 w-56 rounded bg-stone-200" />
            <div className="mb-1 h-3 w-44 rounded bg-stone-100" />
            <div className="h-3 w-28 rounded bg-stone-200" />
          </div>
        ))}
      </div>
    </aside>
  );
}


