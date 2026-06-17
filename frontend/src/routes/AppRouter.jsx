import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import Dashboard from '../pages/Dashboard';
import Players from '../pages/Players';
import Matches from '../pages/Matches';
import Leaderboard from '../pages/Leaderboard';
import SuspiciousPlayers from '../pages/SuspiciousPlayers';
import Matchmaking from '../pages/Matchmaking';
import NotFound from '../pages/NotFound';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index              element={<Dashboard />} />
          <Route path="players"     element={<Players />} />
          <Route path="matches"     element={<Matches />} />
          <Route path="leaderboard" element={<Leaderboard />} />
          <Route path="suspicious"  element={<SuspiciousPlayers />} />
          <Route path="matchmaking" element={<Matchmaking />} />
          <Route path="*"           element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
