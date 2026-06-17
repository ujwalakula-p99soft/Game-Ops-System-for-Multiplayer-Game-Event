import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchGlobalLeaderboard,
  fetchRegionLeaderboard,
  fetchModeLeaderboard,
  fetchRegionModeLeaderboard,
  setRegionFilter,
  setModeFilter,
  setPage,
} from '../features/leaderboard/leaderboardSlice';
import {
  LEADERBOARD_REGION_FILTERS,
  LEADERBOARD_MODE_FILTERS,
} from '../utils/constants';
import PageHeader from '../components/common/PageHeader';
import DataTable from '../components/common/DataTable';
import Pagination from '../components/common/Pagination';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';

const COLUMNS = [
  { key: 'rank',          label: '#',       headerClassName: 'w-12' },
  { key: 'player_id',     label: 'Player'   },
  { key: 'ranking_score', label: 'Score'    },
  { key: 'region',        label: 'Region'   },
];

function fetchForFilters(dispatch, regionFilter, modeFilter, page, pageSize) {
  const isGlobal = regionFilter === 'global';
  const isAllModes = modeFilter === 'all';

  if (isGlobal && isAllModes) {
    dispatch(fetchGlobalLeaderboard({ page, pageSize }));
  } else if (!isGlobal && isAllModes) {
    dispatch(fetchRegionLeaderboard({ region: regionFilter, page, pageSize }));
  } else if (isGlobal && !isAllModes) {
    dispatch(fetchModeLeaderboard({ gameMode: modeFilter, page, pageSize }));
  } else {
    dispatch(fetchRegionModeLeaderboard({
      region: regionFilter,
      gameMode: modeFilter,
      page,
      pageSize,
    }));
  }
}

function FilterGroup({ label, options, activeKey, onChange }) {
  return (
    <div>
      <p className="text-zinc-500 text-xs font-semibold uppercase tracking-widest mb-2">
        {label}
      </p>
      <div
        role="group"
        aria-label={label}
        className="flex gap-1 flex-wrap"
      >
        {options.map((option) => {
          const isActive = activeKey === option.key;
          return (
            <button
              key={option.key}
              type="button"
              aria-pressed={isActive}
              onClick={() => onChange(option.key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function Leaderboard() {
  const dispatch = useDispatch();
  const { regionFilter, modeFilter, page, pageSize, entries, total, loading, error } =
    useSelector((s) => s.leaderboard);

  useEffect(() => {
    fetchForFilters(dispatch, regionFilter, modeFilter, page, pageSize);
  }, [dispatch, regionFilter, modeFilter, page, pageSize]);

  function renderCell(row, col) {
    if (col.key === 'rank') {
      const styles = ['text-yellow-400 font-bold', 'text-zinc-400 font-semibold', 'text-amber-700'];
      const cls = styles[row.rank - 1] || 'text-zinc-500';
      return <span className={cls}>{row.rank}</span>;
    }
    if (col.key === 'ranking_score') {
      return <span className="font-mono text-indigo-300">{row.ranking_score?.toLocaleString()}</span>;
    }
    if (col.key === 'player_id') {
      return <span className="font-medium text-white">{row.player_id}</span>;
    }
    if (col.key === 'region') {
      return <span className="text-zinc-400 text-xs">{row.region}</span>;
    }
    return row[col.key] ?? '—';
  }

  return (
    <div>
      <PageHeader
        title="Leaderboard"
        subtitle="Ranked by cumulative score across matches"
      />

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 mb-6 space-y-5">
        <FilterGroup
          label="Region Filter"
          options={LEADERBOARD_REGION_FILTERS}
          activeKey={regionFilter}
          onChange={(key) => dispatch(setRegionFilter(key))}
        />
        <div className="border-t border-zinc-800/80 pt-5">
          <FilterGroup
            label="Mode Filter"
            options={LEADERBOARD_MODE_FILTERS}
            activeKey={modeFilter}
            onChange={(key) => dispatch(setModeFilter(key))}
          />
        </div>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {loading ? (
        <LoadingSpinner message="Fetching leaderboard…" />
      ) : (
        <>
          <DataTable
            columns={COLUMNS}
            rows={entries}
            keyField="player_id"
            renderCell={renderCell}
            emptyTitle="No entries"
            emptyMessage="No players found for this leaderboard view."
          />
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={(newPage) => dispatch(setPage(newPage))}
          />
        </>
      )}
    </div>
  );
}
