import { useState, useRef } from 'react';
import { createMatch } from '../services/matchApi';
import { GAME_MODES, LOBBY_SIZE } from '../utils/constants';
import PageHeader from '../components/common/PageHeader';
import ErrorBanner from '../components/common/ErrorBanner';

const EMPTY_RESULT = { player_id: '', ping: '', score: '', kills: '', deaths: '' };

let _rowId = 0;
function newRow() {
  return { ...EMPTY_RESULT, _id: ++_rowId };
}

function emptyResults(count) {
  return Array.from({ length: count }, () => newRow());
}

const inputCls =
  'w-full bg-zinc-800/60 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white placeholder-zinc-700 focus:outline-none focus:border-indigo-500 transition-colors';
const labelCls =
  'block text-zinc-500 text-xs font-medium uppercase tracking-wider mb-1.5';
const fieldCls = 'bg-zinc-800/60 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white placeholder-zinc-700 focus:outline-none focus:border-indigo-500 transition-colors w-full';

// ── Match result row ──────────────────────────────────────────────────────
function ResultRow({ index, row, onChange, onRemove, canRemove }) {
  function handle(e) {
    onChange(index, e.target.name, e.target.value);
  }
  return (
    <div className="grid grid-cols-12 gap-2 items-start">
      {/* Player ID — wider */}
      <div className="col-span-3">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1">Player ID</p>}
        <input name="player_id" value={row.player_id} onChange={handle} placeholder="P001" className={fieldCls} />
      </div>
      <div className="col-span-2">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1">Ping</p>}
        <input name="ping" type="number" min="0" value={row.ping} onChange={handle} placeholder="30" className={fieldCls} />
      </div>
      <div className="col-span-2">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1">Score</p>}
        <input name="score" type="number" min="0" value={row.score} onChange={handle} placeholder="500" className={fieldCls} />
      </div>
      <div className="col-span-2">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1">Kills</p>}
        <input name="kills" type="number" min="0" value={row.kills} onChange={handle} placeholder="10" className={fieldCls} />
      </div>
      <div className="col-span-2">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1">Deaths</p>}
        <input name="deaths" type="number" min="0" value={row.deaths} onChange={handle} placeholder="2" className={fieldCls} />
      </div>
      <div className="col-span-1 flex items-end pb-0.5">
        {index === 0 && <p className="text-zinc-600 text-xs mb-1 invisible">×</p>}
        <button
          type="button"
          onClick={() => onRemove(index)}
          disabled={!canRemove}
          className="w-full h-8 flex items-center justify-center text-zinc-600 hover:text-red-400 disabled:opacity-20 transition-colors"
          aria-label="Remove row"
        >
          ×
        </button>
      </div>
    </div>
  );
}

// ── Match result card ─────────────────────────────────────────────────────
function MatchResultCard({ match }) {
  return (
    <div className="bg-zinc-900 border border-emerald-700/40 rounded-lg p-5 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-zinc-400 text-xs uppercase tracking-wider">Match Submitted</p>
        <span className="text-emerald-400 text-xs bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded">✓ Success</span>
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Match ID</dt>
          <dd className="text-white font-semibold font-mono">{match.match_id}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Mode</dt>
          <dd className="text-indigo-400 font-medium">{match.game_mode}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Duration</dt>
          <dd className="text-zinc-300">{match.match_duration_seconds}s</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Players</dt>
          <dd className="text-zinc-300">{match.results?.length}</dd>
        </div>
      </dl>
      {/* Results table */}
      <div className="overflow-x-auto rounded border border-zinc-800">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-zinc-800/60 text-zinc-500 uppercase tracking-wider">
              {['Player', 'Ping', 'Score', 'Kills', 'Deaths'].map((h) => (
                <th key={h} className="px-3 py-2 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {match.results?.map((r) => (
              <tr key={r.player_id} className="border-t border-zinc-800/50 hover:bg-zinc-800/20">
                <td className="px-3 py-2 text-white font-medium">{r.player_id}</td>
                <td className="px-3 py-2 text-zinc-400 font-mono">{r.ping}</td>
                <td className="px-3 py-2 text-indigo-300 font-mono">{r.score}</td>
                <td className="px-3 py-2 text-zinc-300 font-mono">{r.kills}</td>
                <td className="px-3 py-2 text-zinc-400 font-mono">{r.deaths}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function Matches() {
  const [matchId, setMatchId] = useState('');
  const [gameMode, setGameMode] = useState('SOLO');
  const [duration, setDuration] = useState('');
  const [results, setResults] = useState(emptyResults(1));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(null);

  // Sync result row count to game mode lobby size hint
  function handleModeChange(e) {
    const mode = e.target.value;
    setGameMode(mode);
  }

  function handleResultChange(idx, field, value) {
    setResults((rows) =>
      rows.map((r, i) => (i === idx ? { ...r, [field]: value } : r))
    );
  }

  function addRow() {
    if (results.length >= 100) return;
    setResults((rows) => [...rows, newRow()]);
  }

  function removeRow(idx) {
    if (results.length <= 1) return;
    setResults((rows) => rows.filter((_, i) => i !== idx));
  }

  function validate() {
    if (!matchId.trim()) return 'Match ID is required.';
    const d = Number(duration);
    if (!duration || isNaN(d) || d <= 0 || !Number.isInteger(d))
      return 'Duration must be a positive integer (seconds).';
    for (let i = 0; i < results.length; i++) {
      const r = results[i];
      if (!r.player_id.trim()) return `Row ${i + 1}: Player ID is required.`;
      if (r.ping === '' || isNaN(Number(r.ping)) || Number(r.ping) < 0)
        return `Row ${i + 1}: Ping must be ≥ 0.`;
      if (r.score === '' || isNaN(Number(r.score)) || Number(r.score) < 0)
        return `Row ${i + 1}: Score must be ≥ 0.`;
      if (r.kills === '' || isNaN(Number(r.kills)) || Number(r.kills) < 0)
        return `Row ${i + 1}: Kills must be ≥ 0.`;
      if (r.deaths === '' || isNaN(Number(r.deaths)) || Number(r.deaths) < 0)
        return `Row ${i + 1}: Deaths must be ≥ 0.`;
    }
    return '';
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }
    setSubmitting(true);
    setError('');
    setSubmitted(null);
    try {
      const payload = {
        match_id: matchId.trim(),
        game_mode: gameMode,
        match_duration_seconds: Number(duration),
        results: results.map((r) => ({
          player_id: r.player_id.trim(),
          ping:   Number(r.ping),
          score:  Number(r.score),
          kills:  Number(r.kills),
          deaths: Number(r.deaths),
        })),
      };
      const data = await createMatch(payload);
      setSubmitted(data);
      setMatchId('');
      setDuration('');
      setResults(emptyResults(1));
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Submit Match"
        subtitle="Record match results — triggers leaderboard update and anomaly detection"
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* ── Form ── */}
        <div>
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Match metadata */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
              <p className="text-zinc-400 text-xs font-semibold uppercase tracking-widest">Match Details</p>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="match-id" className={labelCls}>Match ID</label>
                  <input
                    id="match-id"
                    value={matchId}
                    onChange={(e) => setMatchId(e.target.value)}
                    placeholder="e.g. M001"
                    className={inputCls}
                  />
                </div>
                <div>
                  <label htmlFor="game-mode" className={labelCls}>Game Mode</label>
                  <select id="game-mode" value={gameMode} onChange={handleModeChange} className={inputCls}>
                    {GAME_MODES.map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="match-duration" className={labelCls}>Duration (seconds)</label>
                <input
                  id="match-duration"
                  type="number"
                  min="1"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  placeholder="e.g. 300"
                  className={inputCls}
                />
              </div>

              {/* Lobby size hint */}
              <p className="text-zinc-700 text-xs">
                Typical lobby for {gameMode}:{' '}
                <span className="text-zinc-500">{LOBBY_SIZE[gameMode]} player{LOBBY_SIZE[gameMode] > 1 ? 's' : ''}</span>
                {' '}· Max 100 players per match
              </p>
            </div>

            {/* Results rows */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-zinc-400 text-xs font-semibold uppercase tracking-widest">
                  Player Results
                  <span className="ml-2 text-zinc-600 normal-case font-normal">({results.length}/100)</span>
                </p>
                <button
                  type="button"
                  onClick={addRow}
                  disabled={results.length >= 100}
                  className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-30 transition-colors"
                >
                  + Add Row
                </button>
              </div>

              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {results.map((row, i) => (
                  <ResultRow
                    key={row._id}
                    index={i}
                    row={row}
                    onChange={handleResultChange}
                    onRemove={removeRow}
                    canRemove={results.length > 1}
                  />
                ))}
              </div>
            </div>

            {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
            >
              {submitting ? 'Submitting…' : 'Submit Match'}
            </button>
          </form>
        </div>

        {/* ── Result ── */}
        <div>
          {submitted ? (
            <MatchResultCard match={submitted} />
          ) : (
            <div className="bg-zinc-900/40 border border-zinc-800/50 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center h-64">
              <svg className="w-8 h-8 text-zinc-700 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-zinc-600 text-sm">Match result will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
