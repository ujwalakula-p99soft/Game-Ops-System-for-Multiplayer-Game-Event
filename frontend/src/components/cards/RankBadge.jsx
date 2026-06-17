import { RANK_CONFIG } from '../../utils/constants';

export default function RankBadge({ rank }) {
  const cfg = RANK_CONFIG[rank] || RANK_CONFIG.Bronze;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${cfg.color} ${cfg.bg} ${cfg.border}`}
    >
      {rank}
    </span>
  );
}
