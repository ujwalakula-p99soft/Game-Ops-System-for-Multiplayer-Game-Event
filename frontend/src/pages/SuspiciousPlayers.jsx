import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchSuspiciousPlayers } from '../features/suspicious/suspiciousSlice';
import PageHeader from '../components/common/PageHeader';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';

const COLUMNS = [
  { key: 'player_id',           label: 'Player'           },
  { key: 'anomaly_score',       label: 'Anomaly Score'    },
  { key: 'avg_kill_efficiency', label: 'Kill Eff.'        },
  { key: 'avg_score_efficiency',label: 'Score Eff.'       },
  { key: 'avg_kd_ratio',        label: 'KD Ratio'         },
  { key: 'matches_evaluated',   label: 'Matches'          },
  { key: 'flagged_at',          label: 'Flagged At'       },
];

function anomalyColor(score) {
  if (score >= 4)  return 'text-red-400';
  if (score >= 3)  return 'text-orange-400';
  if (score >= 2)  return 'text-yellow-400';
  return 'text-zinc-400';
}

function renderCell(row, col) {
  if (col.key === 'player_id') {
    return <span className="font-medium text-white">{row.player_id}</span>;
  }
  if (col.key === 'anomaly_score') {
    return (
      <span className={`font-mono font-bold ${anomalyColor(row.anomaly_score)}`}>
        {row.anomaly_score.toFixed(3)}
      </span>
    );
  }
  if (col.key === 'avg_kill_efficiency' || col.key === 'avg_score_efficiency') {
    return <span className="font-mono text-zinc-400">{row[col.key]?.toFixed(4)}</span>;
  }
  if (col.key === 'avg_kd_ratio') {
    return <span className="font-mono text-zinc-400">{row.avg_kd_ratio?.toFixed(2)}</span>;
  }
  if (col.key === 'flagged_at') {
    return (
      <span className="text-zinc-500 text-xs">
        {new Date(row.flagged_at).toLocaleString()}
      </span>
    );
  }
  return row[col.key] ?? '—';
}

export default function SuspiciousPlayers() {
  const dispatch = useDispatch();
  const { entries, total, loading, error } = useSelector((s) => s.suspicious);

  useEffect(() => {
    dispatch(fetchSuspiciousPlayers());
  }, [dispatch]);

  return (
    <div>
      <PageHeader
        title="Suspicious Players"
        subtitle="Population-relative anomaly detection — flagged for review, not auto-banned"
        action={
          <button
            onClick={() => dispatch(fetchSuspiciousPlayers())}
            disabled={loading}
            aria-label="Refresh suspicious players list"
            className="flex items-center gap-2 px-4 py-2 text-sm bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-zinc-300 transition-colors disabled:opacity-50"
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        }
      />

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {/* Summary */}
      {!loading && !error && (
        <div className="mb-4 flex items-center gap-2">
          <span className="text-zinc-600 text-sm">
            {total > 0 ? (
              <>
                <span className="text-red-400 font-semibold">{total}</span>{' '}
                player{total !== 1 ? 's' : ''} flagged
              </>
            ) : (
              <span className="text-emerald-500">No flagged players</span>
            )}
          </span>
        </div>
      )}

      {loading ? (
        <LoadingSpinner message="Loading suspicious players…" />
      ) : (
        <DataTable
          columns={COLUMNS}
          rows={entries}
          keyField="player_id"
          renderCell={renderCell}
          emptyTitle="No suspicious players"
          emptyMessage="No players have been flagged by the anomaly detection system."
        />
      )}
    </div>
  );
}
