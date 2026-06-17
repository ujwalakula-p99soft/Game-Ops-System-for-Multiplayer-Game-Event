import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  submitJoinQueue,
  submitLeaveQueue,
  fetchQueueStatus,
  clearMatchmaking,
} from '../features/matchmaking/matchmakingSlice';
import { GAME_MODES } from '../utils/constants';
import PageHeader from '../components/common/PageHeader';
import ErrorBanner from '../components/common/ErrorBanner';
import LoadingSpinner from '../components/common/LoadingSpinner';
import RankBadge from '../components/cards/RankBadge';

// ── Queue Status card ──────────────────────────────────────────────────────
function QueueStatusCard({ data, onLeave, leaving }) {
  const wait = Math.round(data.wait_seconds ?? 0);
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-4 max-w-md">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold text-sm">In Queue</h3>
        <span className="inline-flex items-center gap-1.5 text-xs text-yellow-400 bg-yellow-400/10 border border-yellow-400/20 rounded px-2 py-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
          Searching…
        </span>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Player</dt>
          <dd className="text-white font-medium">{data.player_id}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Mode</dt>
          <dd className="text-indigo-400 font-medium">{data.game_mode}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Rank</dt>
          <dd><RankBadge rank={data.rank} /></dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Skill Rating</dt>
          <dd className="font-mono text-zinc-300">{data.skill_rating?.toFixed(1)}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Region</dt>
          <dd className="text-zinc-400">{data.region}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Device</dt>
          <dd className="text-zinc-400">{data.device}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Ping</dt>
          <dd className="font-mono text-zinc-300">{data.ping} ms</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Wait Time</dt>
          <dd className="font-mono text-zinc-300">{wait}s</dd>
        </div>
      </dl>

      <button
        onClick={onLeave}
        disabled={leaving}
        className="w-full py-2 text-sm font-medium bg-red-950/60 hover:bg-red-900/60 border border-red-800/60 text-red-400 rounded transition-colors disabled:opacity-50"
      >
        {leaving ? 'Leaving…' : 'Leave Queue'}
      </button>
    </div>
  );
}

// ── Lobby card ─────────────────────────────────────────────────────────────
function LobbyCard({ data, onReset }) {
  return (
    <div className="bg-zinc-900 border border-emerald-700/40 rounded-lg p-6 space-y-4 max-w-md">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold text-sm">Lobby Formed</h3>
        <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded px-2 py-0.5">
          ✓ Ready
        </span>
      </div>

      <div className="flex gap-4 text-sm">
        <div>
          <p className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Mode</p>
          <p className="text-indigo-400 font-medium">{data.game_mode}</p>
        </div>
        <div>
          <p className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Region</p>
          <p className="text-zinc-300">{data.region}</p>
        </div>
        <div>
          <p className="text-zinc-600 text-xs uppercase tracking-wider mb-0.5">Players</p>
          <p className="text-zinc-300">{data.players?.length}</p>
        </div>
      </div>

      <div className="space-y-2">
        {data.players?.map((p, i) => (
          <div
            key={p.player_id}
            className="flex items-center justify-between bg-zinc-800/60 rounded px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span className="text-zinc-600 text-xs w-4">{i + 1}</span>
              <span className="text-white text-sm font-medium">{p.player_id}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-zinc-500 text-xs">{p.skill_rating?.toFixed(1)} SR</span>
              <span className="font-mono text-zinc-500 text-xs">{p.ping} ms</span>
              <RankBadge rank={p.rank} />
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={onReset}
        className="w-full py-2 text-sm font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 rounded transition-colors"
      >
        New Search
      </button>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────
const EMPTY_FORM = { player_id: '', game_mode: 'SOLO', ping: '' };

export default function Matchmaking() {
  const dispatch = useDispatch();
  const { result, resultType, loading, error } = useSelector((s) => s.matchmaking);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');

  // Status poll form
  const [pollId, setPollId] = useState('');

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
    setFormError('');
  }

  function validate() {
    if (!form.player_id.trim()) return 'Player ID is required.';
    const ping = Number(form.ping);
    if (form.ping === '' || isNaN(ping) || ping < 0 || !Number.isInteger(ping))
      return 'Ping must be a non-negative integer.';
    return '';
  }

  function handleJoin(e) {
    e.preventDefault();
    const err = validate();
    if (err) { setFormError(err); return; }
    dispatch(submitJoinQueue({
      player_id: form.player_id.trim(),
      game_mode: form.game_mode,
      ping: Number(form.ping),
    }));
  }

  function handleLeave() {
    if (result?.player_id) dispatch(submitLeaveQueue(result.player_id));
  }

  function handleReset() {
    dispatch(clearMatchmaking());
    setForm(EMPTY_FORM);
  }

  function handlePoll(e) {
    e.preventDefault();
    if (pollId.trim()) dispatch(fetchQueueStatus(pollId.trim()));
  }

  const inputCls =
    'w-full bg-zinc-800/60 border border-zinc-700 rounded px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition-colors';
  const labelCls = 'block text-zinc-500 text-xs font-medium uppercase tracking-wider mb-1.5';

  return (
    <div>
      <PageHeader
        title="Matchmaking"
        subtitle="Join the matchmaking queue or check queue status"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ── Left: Join / Result ── */}
        <div className="space-y-4">
          <h2 className="text-zinc-300 text-sm font-semibold">Join Queue</h2>

          {/* Show result if available */}
          {resultType === 'queue' && result && (
            <QueueStatusCard data={result} onLeave={handleLeave} leaving={loading} />
          )}
          {resultType === 'lobby' && result && (
            <LobbyCard data={result} onReset={handleReset} />
          )}

          {/* Show form only when idle */}
          {resultType === 'idle' && (
            <form onSubmit={handleJoin} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
              <div>
                <label htmlFor="mm-player-id" className={labelCls}>Player ID</label>
                <input
                  id="mm-player-id"
                  name="player_id"
                  value={form.player_id}
                  onChange={handleChange}
                  placeholder="e.g. P001"
                  className={inputCls}
                />
              </div>

              <div>
                <label htmlFor="mm-game-mode" className={labelCls}>Game Mode</label>
                <select
                  id="mm-game-mode"
                  name="game_mode"
                  value={form.game_mode}
                  onChange={handleChange}
                  className={inputCls}
                >
                  {GAME_MODES.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="mm-ping" className={labelCls}>Ping (ms)</label>
                <input
                  id="mm-ping"
                  name="ping"
                  type="number"
                  min="0"
                  value={form.ping}
                  onChange={handleChange}
                  placeholder="e.g. 30"
                  className={inputCls}
                />
              </div>

              {(formError || error) && (
                <ErrorBanner message={formError || error} onDismiss={() => setFormError('')} />
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
              >
                {loading ? 'Joining…' : 'Join Queue'}
              </button>
            </form>
          )}

          {/* Error when result visible */}
          {resultType !== 'idle' && error && (
            <ErrorBanner message={error} />
          )}
        </div>

        {/* ── Right: Status Poll ── */}
        <div className="space-y-4">
          <h2 className="text-zinc-300 text-sm font-semibold">Check Queue Status</h2>
          <form
            onSubmit={handlePoll}
            className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4"
          >
            <div>
              <label htmlFor="poll-player-id" className={labelCls}>Player ID</label>
              <input
                id="poll-player-id"
                value={pollId}
                onChange={(e) => setPollId(e.target.value)}
                placeholder="e.g. P001"
                className={inputCls}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !pollId.trim()}
              className="w-full py-2.5 bg-zinc-700 hover:bg-zinc-600 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
            >
              {loading ? 'Loading…' : 'Check Status'}
            </button>
          </form>

          {/* Inline result for status poll */}
          {resultType === 'queue' && result && pollId && result.player_id === pollId.trim() && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-sm space-y-2">
              <p className="text-zinc-500 text-xs uppercase tracking-wider mb-3">Queue Status</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ['Player', result.player_id],
                  ['Mode', result.game_mode],
                  ['Region', result.region],
                  ['Device', result.device],
                  ['Ping', `${result.ping} ms`],
                  ['SR', result.skill_rating?.toFixed(1)],
                  ['Wait', `${Math.round(result.wait_seconds ?? 0)}s`],
                ].map(([k, v]) => (
                  <div key={k}>
                    <span className="text-zinc-600 text-xs">{k}: </span>
                    <span className="text-zinc-300 text-xs font-medium">{v}</span>
                  </div>
                ))}
                <div className="col-span-2">
                  <span className="text-zinc-600 text-xs">Rank: </span>
                  <RankBadge rank={result.rank} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
