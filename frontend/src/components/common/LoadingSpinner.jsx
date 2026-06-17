export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div
      className="flex flex-col items-center justify-center py-20 gap-4"
      role="status"
      aria-label={message}
    >
      <div className="w-10 h-10 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" aria-hidden="true" />
      <span className="text-zinc-500 text-sm tracking-wide">{message}</span>
    </div>
  );
}
