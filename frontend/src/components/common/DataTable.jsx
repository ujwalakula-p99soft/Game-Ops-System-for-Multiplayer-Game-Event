/**
 * DataTable
 * Props:
 *   columns: [{ key, label, className? }]
 *   rows: any[]
 *   renderCell?: (row, column) => ReactNode   — custom cell renderer
 *   keyField: string  — unique key per row (default 'id')
 *   emptyMessage?: string
 */
import EmptyState from './EmptyState';

export default function DataTable({
  columns = [],
  rows = [],
  renderCell,
  keyField = 'id',
  emptyTitle,
  emptyMessage,
}) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900/60">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-zinc-500 ${col.headerClassName || ''}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={row[keyField] ?? idx}
              className="border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/30 transition-colors"
            >
              {columns.map((col) => (
                <td key={col.key} className={`px-4 py-3 text-zinc-300 ${col.className || ''}`}>
                  {renderCell ? renderCell(row, col) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
