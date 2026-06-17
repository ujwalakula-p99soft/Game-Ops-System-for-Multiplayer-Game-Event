export default function StatCard({ label, value, icon, accent = 'indigo' }) {
  const accentMap = {
    indigo: 'text-indigo-400 bg-indigo-400/10',
    red:    'text-red-400 bg-red-400/10',
    yellow: 'text-yellow-400 bg-yellow-400/10',
    green:  'text-emerald-400 bg-emerald-400/10',
    cyan:   'text-cyan-400 bg-cyan-400/10',
  };
  const accentClass = accentMap[accent] || accentMap.indigo;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 flex items-center gap-4">
      {icon && (
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${accentClass}`}>
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-zinc-500 text-xs font-medium uppercase tracking-widest truncate">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5 leading-none">{value ?? '—'}</p>
      </div>
    </div>
  );
}
