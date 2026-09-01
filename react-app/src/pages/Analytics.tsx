import { Box, Card, CardContent, Typography, Grid, CircularProgress, } from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const COLORS_RISK = ['#78BE20', '#ED8B00', '#D32F2F'];
const COLORS_STATUS = { Approved: '#22c55e', Rejected: '#ef4444', Pending: '#94a3b8' };
const COLORS_PASTEL = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3'];

export default function Analytics() {
  const { data: rawApps, isLoading, error } = useQuery({
    queryKey: ['applications-analytics'],
    queryFn: async () => { const r = await api.get('/api/applications'); return r.data; },
  });

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error">Error loading analytics data.</Typography>;

  // Flatten data
  const apps = (rawApps && Array.isArray(rawApps) ? rawApps : []).map((a: any) => {
    const pred = typeof a.prediction === 'object' && a.prediction ? a.prediction : {};
    const dec = typeof a.decision === 'object' && a.decision ? a.decision : {};
    return {
      ...a,
      best_model: pred.best_model || 'Unknown',
      recommended_rate: pred.recommended_rate ?? null,
      risk_score: pred.risk_score ?? null,
      Status: dec.approved === true ? 'Approved' : dec.approved === false ? 'Rejected' : 'Pending',
    };
  });

  const totalApps = apps.length;
  const approved = apps.filter((a: any) => a.Status === 'Approved').length;
  const approvalRate = totalApps > 0 ? (approved / totalApps * 100) : 0;
  const avgRate = apps.filter((a: any) => a.recommended_rate != null).reduce((s: number, a: any) => s + a.recommended_rate, 0) / (apps.filter((a: any) => a.recommended_rate != null).length || 1);
  const avgRisk = apps.filter((a: any) => a.risk_score != null).reduce((s: number, a: any) => s + a.risk_score, 0) / (apps.filter((a: any) => a.risk_score != null).length || 1);

  // Risk distribution
  const riskData = [
    { name: 'Low Risk', value: apps.filter((a: any) => a.risk_score != null && a.risk_score < 0.33).length },
    { name: 'Moderate Risk', value: apps.filter((a: any) => a.risk_score != null && a.risk_score >= 0.33 && a.risk_score < 0.66).length },
    { name: 'High Risk', value: apps.filter((a: any) => a.risk_score != null && a.risk_score >= 0.66).length },
  ].filter(d => d.value > 0);

  // Region pie
  const regionCounts: Record<string, number> = {};
  apps.forEach((a: any) => { if (a.region) regionCounts[a.region] = (regionCounts[a.region] || 0) + 1; });
  const regionData = Object.entries(regionCounts).map(([name, value]) => ({ name, value }));

  // Loan purpose by status
  const purposeMap: Record<string, Record<string, number>> = {};
  apps.forEach((a: any) => {
    const p = a.loan_purpose || 'Other';
    if (!purposeMap[p]) purposeMap[p] = { Approved: 0, Rejected: 0, Pending: 0 };
    purposeMap[p][a.Status]++;
  });
  const purposeData = Object.entries(purposeMap).map(([name, counts]) => ({ name, ...counts }));

  // Model preferences
  const modelCounts: Record<string, number> = {};
  apps.forEach((a: any) => { if (a.best_model && a.best_model !== 'Unknown') modelCounts[a.best_model] = (modelCounts[a.best_model] || 0) + 1; });
  const modelData = Object.entries(modelCounts).map(([name, value]) => ({ name, value }));

  // Income by status
  const incomeByStatus = ['Approved', 'Rejected', 'Pending'].map(status => {
    const vals = apps.filter((a: any) => a.Status === status && a.income != null).map((a: any) => a.income);
    const avg = vals.length > 0 ? vals.reduce((s: number, v: number) => s + v, 0) / vals.length : 0;
    const min = vals.length > 0 ? Math.min(...vals) : 0;
    const max = vals.length > 0 ? Math.max(...vals) : 0;
    return { status, avg: Math.round(avg), min, max, count: vals.length };
  });

  // Scatter data (risk vs loan amount)
  const scatterData = apps.filter((a: any) => a.risk_score != null && a.loan_amount != null).map((a: any) => ({
    x: a.loan_amount, y: a.risk_score, status: a.Status, income: a.income || 1000,
  }));

  if (totalApps === 0) {
    return (
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>📈 Enterprise Portfolio Analytics</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>No applications found. Process some loans first.</Typography>
      </Box>
    );
  }

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>📈 Enterprise Portfolio Analytics</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>Live portfolio data from {totalApps} applications</Typography>
      </Box>

      {/* KPI Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { title: 'Total Applications', value: totalApps },
          { title: 'Approval Rate', value: `${approvalRate.toFixed(1)}%` },
          { title: 'Avg Recommended Rate', value: avgRate > 0 ? `${avgRate.toFixed(2)}%` : 'N/A' },
          { title: 'Avg Portfolio Risk', value: avgRisk > 0 ? avgRisk.toFixed(2) : 'N/A' },
        ].map(kpi => (
          <Grid item xs={6} md={3} key={kpi.title}>
            <Card>
              <CardContent>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>{kpi.title}</Typography>
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>{kpi.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Row 1: Risk Distribution + Risk vs Loan Amount */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Risk & Portfolio Analysis</Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Risk Score Distribution</Typography>
              <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={riskData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                      {riskData.map((_, i) => <Cell key={i} fill={COLORS_RISK[i % COLORS_RISK.length]} />)}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Risk vs. Loan Amount</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" name="Loan Amount" type="number" />
                    <YAxis dataKey="y" name="Risk Score" type="number" domain={[0, 1]} />
                    <ZAxis dataKey="income" range={[30, 200]} name="Income" />
                    <RechartsTooltip />
                    <Legend />
                    {['Approved', 'Rejected', 'Pending'].map(status => (
                      <Scatter key={status} name={status} data={scatterData.filter(d => d.status === status)}
                        fill={(COLORS_STATUS as any)[status]} />
                    ))}
                  </ScatterChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 2: Region + Loan Purpose */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Demographic Insights</Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Application Volume by Region</Typography>
              <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={regionData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={5} dataKey="value">
                      {regionData.map((_, i) => <Cell key={i} fill={COLORS_PASTEL[i % COLORS_PASTEL.length]} />)}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Loan Purposes Breakdown</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={purposeData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="Approved" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Rejected" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Pending" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 3: Model Prefs + Income */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>AI Telemetry</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>AI Ensemble Model Preferences</Typography>
              {modelData.length > 0 ? (
                <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={modelData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label>
                        {modelData.map((_, i) => <Cell key={i} fill={COLORS_PASTEL[i % COLORS_PASTEL.length]} />)}
                      </Pie>
                      <RechartsTooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              ) : (
                <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'center', py: 8 }}>No model preference data yet.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Income Distribution by Status</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={incomeByStatus}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="status" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="avg" fill="#0066A1" name="Avg Income" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="max" fill="#78BE20" name="Max Income" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

