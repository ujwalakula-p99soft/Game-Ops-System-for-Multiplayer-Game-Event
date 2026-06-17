import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
      <p className="text-7xl font-black text-zinc-800 leading-none">404</p>
      <p className="text-zinc-300 font-semibold text-lg">Page not found</p>
      <p className="text-zinc-600 text-sm max-w-xs">
        The route you navigated to doesn't exist in this application.
      </p>
      <Link
        to="/"
        className="mt-4 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded transition-colors"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
