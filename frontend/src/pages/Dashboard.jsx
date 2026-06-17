/**
 * Dashboard
 *
 * Only uses endpoints that actually exist:
 *   GET /leaderboard/global   → top 5 entries + total player count proxy
 *   GET /suspicious-players   → flagged count
 *
 * Does NOT show: total players, active queue count
 * (no backend endpoints exist for those)
 */
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchGlobalLeaderboard } from '../features/leaderboard/leaderboardSlice';
import { fetchSuspiciousPlayers } from '../features/suspicious/suspiciousSlice';
import { Link } from 'react-router-dom';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';
import RankBadge from '../components/cards/RankBadge';

// ── Icons ──────────────────────────────────────────────────────────────────
const TrophyIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
  </svg>
);
const AlertIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
  </svg>
);
const ListIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);

// ── Mini top-5 table ──────────────────────────────────────────────────────
function TopPlayersTable({ entries, loading, error }) {
  const rankStyle = (rank) => {
    if (rank === 1) return 'text-yellow-400 font-bold';
    if (rank === 2) return 'text-zinc-400 font-semibold';
    if (rank === 3) return 'text-amber-700 font-semibold';
    return 'text-zinc-600';
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-300">Top Ranked Players</h2>
        <Link
          to="/leaderboard"
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          View all →
        </Link>
      </div>

      {loading && <LoadingSpinner message="Loading leaderboard…" />}
      {error && <div className="p-4"><ErrorBanner message={error} /></div>}

      {!loading && !error && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-zinc-600 text-xs uppercase tracking-wider border-b border-zinc-800/50">
              <th className="px-5 py-2.5 text-left w-10">#</th>
              <th className="px-5 py-2.5 text-left">Player</th>
              <th className="px-5 py-2.5 text-left">Region</th>
              <th className="px-5 py-2.5 text-right">Score</th>
            </tr>
          </thead>
          <tbody>
            {entries.slice(0, 5).map((e) => (
              <tr
                key={e.player_id}
                className="border-b border-zinc-800/40 last:border-0 hover:bg-zinc-800/20 transition-colors"
              >
                <td className={`px-5 py-3 ${rankStyle(e.rank)}`}>{e.rank}</td>
                <td className="px-5 py-3 text-white font-medium">{e.player_id}</td>
                <td className="px-5 py-3 text-zinc-500 text-xs">{e.region}</td>
                <td className="px-5 py-3 text-right font-mono text-indigo-300">
                  {e.ranking_score?.toLocaleString()}
                </td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-zinc-600 text-sm">
                  No leaderboard data yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const dispatch = useDispatch();
  const { entries, total: lbTotal, loading: lbLoading, error: lbError } =
    useSelector((s) => s.leaderboard);
  const { total: suspTotal, loading: suspLoading } =
    useSelector((s) => s.suspicious);

  useEffect(() => {
    dispatch(fetchGlobalLeaderboard({ page: 1, pageSize: 20 }));
    dispatch(fetchSuspiciousPlayers());
  }, [dispatch]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">Game Operations System — overview</p>
      </div>

      {/* Stat cards — only sourced from real endpoints */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Ranked Players"
          value={lbLoading ? '…' : lbTotal?.toLocaleString()}
          icon={TrophyIcon}
          accent="indigo"
        />
        <StatCard
          label="Flagged Players"
          value={suspLoading ? '…' : suspTotal?.toLocaleString()}
          icon={AlertIcon}
          accent="red"
        />
        <StatCard
          label="Top Score (Global)"
          value={lbLoading ? '…' : (entries[0]?.ranking_score?.toLocaleString() ?? '—')}
          icon={ListIcon}
          accent="yellow"
        />
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { to: '/players',     label: 'Register Player',  desc: 'Create or look up a player' },
          { to: '/matches',     label: 'Submit Match',      desc: 'Record match results' },
          { to: '/matchmaking', label: 'Matchmaking',       desc: 'Join or check queue' },
        ].map(({ to, label, desc }) => (
          <Link
            key={to}
            to={to}
            className="bg-zinc-900 border border-zinc-800 hover:border-indigo-600/50 rounded-lg p-4 transition-colors group"
          >
            <p className="text-white text-sm font-medium group-hover:text-indigo-400 transition-colors">
              {label}
            </p>
            <p className="text-zinc-600 text-xs mt-1">{desc}</p>
          </Link>
        ))}
      </div>

      {/* Top players */}
      <TopPlayersTable entries={entries} loading={lbLoading} error={lbError} />
    </div>
  );
}
