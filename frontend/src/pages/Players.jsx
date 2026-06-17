import { useState } from 'react';
import { createPlayer, getPlayer } from '../services/playerApi';
import { REGIONS, DEVICE_TYPES } from '../utils/constants';
import PageHeader from '../components/common/PageHeader';
import ErrorBanner from '../components/common/ErrorBanner';

const EMPTY_CREATE = { player_id: '', region: 'India', device: 'PC' };

// ── Created/fetched player card ────────────────────────────────────────────
function PlayerCard({ player, label }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-zinc-500 text-xs uppercase tracking-wider">{label}</p>
        <span className="text-emerald-400 text-xs bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded">
          Found
        </span>
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Player ID</dt>
          <dd className="text-white font-semibold">{player.player_id}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Region</dt>
          <dd className="text-zinc-300">{player.region}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Device</dt>
          <dd className="text-zinc-300">{player.device}</dd>
        </div>
        <div>
          <dt className="text-zinc-600 text-xs mb-0.5">Created</dt>
          <dd className="text-zinc-400 text-xs">
            {new Date(player.created_at).toLocaleString()}
          </dd>
        </div>
      </dl>
    </div>
  );
}

const inputCls =
  'w-full bg-zinc-800/60 border border-zinc-700 rounded px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition-colors';
const labelCls =
  'block text-zinc-500 text-xs font-medium uppercase tracking-wider mb-1.5';

export default function Players() {
  // ── Create section ──────────────────────────────────────────────
  const [createForm, setCreateForm] = useState(EMPTY_CREATE);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [createdPlayer, setCreatedPlayer] = useState(null);

  function handleCreateChange(e) {
    setCreateForm((f) => ({ ...f, [e.target.name]: e.target.value }));
    setCreateError('');
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!createForm.player_id.trim()) {
      setCreateError('Player ID is required.');
      return;
    }
    setCreating(true);
    setCreateError('');
    setCreatedPlayer(null);
    try {
      const data = await createPlayer({
        player_id: createForm.player_id.trim(),
        region: createForm.region,
        device: createForm.device,
      });
      setCreatedPlayer(data);
      setCreateForm(EMPTY_CREATE);
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  }

  // ── Lookup section ──────────────────────────────────────────────
  const [lookupId, setLookupId] = useState('');
  const [looking, setLooking] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [foundPlayer, setFoundPlayer] = useState(null);

  async function handleLookup(e) {
    e.preventDefault();
    if (!lookupId.trim()) { setLookupError('Enter a Player ID.'); return; }
    setLooking(true);
    setLookupError('');
    setFoundPlayer(null);
    try {
      const data = await getPlayer(lookupId.trim());
      setFoundPlayer(data);
    } catch (err) {
      setLookupError(err.message);
    } finally {
      setLooking(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Players"
        subtitle="Register a new player or look up an existing one"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ── Create Player ── */}
        <div className="space-y-4">
          <h2 className="text-zinc-300 text-sm font-semibold">Create Player</h2>
          <form
            onSubmit={handleCreate}
            className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4"
          >
            <div>
              <label htmlFor="create-player-id" className={labelCls}>Player ID</label>
              <input
                id="create-player-id"
                name="player_id"
                value={createForm.player_id}
                onChange={handleCreateChange}
                placeholder="e.g. P001"
                className={inputCls}
              />
            </div>

            <div>
              <label htmlFor="create-region" className={labelCls}>Region</label>
              <select
                id="create-region"
                name="region"
                value={createForm.region}
                onChange={handleCreateChange}
                className={inputCls}
              >
                {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            <div>
              <label htmlFor="create-device" className={labelCls}>Device</label>
              <select
                id="create-device"
                name="device"
                value={createForm.device}
                onChange={handleCreateChange}
                className={inputCls}
              >
                {DEVICE_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

            {createError && (
              <ErrorBanner message={createError} onDismiss={() => setCreateError('')} />
            )}

            <button
              type="submit"
              disabled={creating}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
            >
              {creating ? 'Creating…' : 'Create Player'}
            </button>
          </form>

          {createdPlayer && (
            <PlayerCard player={createdPlayer} label="Player Created" />
          )}
        </div>

        {/* ── Lookup Player ── */}
        <div className="space-y-4">
          <h2 className="text-zinc-300 text-sm font-semibold">Look Up Player</h2>
          <form
            onSubmit={handleLookup}
            className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4"
          >
            <div>
              <label htmlFor="lookup-player-id" className={labelCls}>Player ID</label>
              <input
                id="lookup-player-id"
                value={lookupId}
                onChange={(e) => { setLookupId(e.target.value); setLookupError(''); }}
                placeholder="e.g. P001"
                className={inputCls}
              />
            </div>

            {lookupError && (
              <ErrorBanner message={lookupError} onDismiss={() => setLookupError('')} />
            )}

            <button
              type="submit"
              disabled={looking}
              className="w-full py-2.5 bg-zinc-700 hover:bg-zinc-600 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
            >
              {looking ? 'Searching…' : 'Find Player'}
            </button>
          </form>

          {foundPlayer && (
            <PlayerCard player={foundPlayer} label="Player Found" />
          )}
        </div>
      </div>
    </div>
  );
}
