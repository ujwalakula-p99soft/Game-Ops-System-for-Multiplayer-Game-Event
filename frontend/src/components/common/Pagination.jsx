export default function Pagination({ page, pageSize, total, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  const isPrev = page > 1;
  const isNext = page < totalPages;

  // Build a compact page window: prev, current-1, current, current+1, next
  const pages = [];
  const delta = 1;
  for (let i = Math.max(1, page - delta); i <= Math.min(totalPages, page + delta); i++) {
    pages.push(i);
  }

  const btnBase =
    'h-8 min-w-[2rem] px-2 rounded text-sm font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-indigo-500';
  const activeCls = 'bg-indigo-600 text-white';
  const inactiveCls = 'text-zinc-400 hover:text-white hover:bg-zinc-800';
  const disabledCls = 'text-zinc-700 cursor-not-allowed';

  return (
    <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800">
      <p className="text-zinc-600 text-xs">
        Page <span className="text-zinc-400">{page}</span> of{' '}
        <span className="text-zinc-400">{totalPages}</span>
        <span className="ml-2">({total.toLocaleString()} total)</span>
      </p>

      <div className="flex items-center gap-1">
        {/* Prev */}
        <button
          className={`${btnBase} ${isPrev ? inactiveCls : disabledCls}`}
          onClick={() => isPrev && onPageChange(page - 1)}
          disabled={!isPrev}
          aria-label="Previous page"
        >
          ‹
        </button>

        {/* First page shortcut */}
        {pages[0] > 1 && (
          <>
            <button className={`${btnBase} ${inactiveCls}`} onClick={() => onPageChange(1)}>1</button>
            {pages[0] > 2 && <span className="text-zinc-700 px-1 text-xs">…</span>}
          </>
        )}

        {pages.map((p) => (
          <button
            key={p}
            className={`${btnBase} ${p === page ? activeCls : inactiveCls}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}

        {/* Last page shortcut */}
        {pages[pages.length - 1] < totalPages && (
          <>
            {pages[pages.length - 1] < totalPages - 1 && (
              <span className="text-zinc-700 px-1 text-xs">…</span>
            )}
            <button className={`${btnBase} ${inactiveCls}`} onClick={() => onPageChange(totalPages)}>
              {totalPages}
            </button>
          </>
        )}

        {/* Next */}
        <button
          className={`${btnBase} ${isNext ? inactiveCls : disabledCls}`}
          onClick={() => isNext && onPageChange(page + 1)}
          disabled={!isNext}
          aria-label="Next page"
        >
          ›
        </button>
      </div>
    </div>
  );
}
