export default function EmptyState({ title = 'No data', message = 'Nothing to display here yet.' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
      <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
        <svg className="w-6 h-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0H4" />
        </svg>
      </div>
      <p className="text-zinc-300 font-medium text-sm">{title}</p>
      <p className="text-zinc-600 text-xs max-w-xs">{message}</p>
    </div>
  );
}
