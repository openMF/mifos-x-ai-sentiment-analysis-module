import { Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';

import Dashboard from './pages/Dashboard';
import Loans from './pages/Loans';
import Fairness from './pages/Fairness';
import Assistant from './pages/Assistant';
import Training from './pages/Training';
import Analytics from './pages/Analytics';
import ABTesting from './pages/ABTesting';
import Simulator from './pages/Simulator';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

const Users = () => <div style={{ padding: 40, textAlign: 'center', color: '#667085' }}>Users & Roles — Coming Soon</div>;
const Models = () => <div style={{ padding: 40, textAlign: 'center', color: '#667085' }}>Model Registry — Coming Soon</div>;

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="loans" element={<Loans />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="training" element={<Training />} />
        <Route path="ab-testing" element={<ABTesting />} />
        <Route path="simulator" element={<Simulator />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="reports" element={<Reports />} />
        <Route path="fairness" element={<Fairness />} />
        <Route path="admin/users" element={<Users />} />
        <Route path="admin/models" element={<Models />} />
        <Route path="admin/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;

