import { useState, useMemo } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Button, TextField, Select, MenuItem,
  FormControl, InputLabel, Slider, Chip, Divider, Alert, CircularProgress
} from '@mui/material';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend
} from 'recharts';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

// Seeded pseudo-random for consistent simulated data
function seededRandom(seed: number) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

export default function ABTesting() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [modelA, setModelA] = useState('PPO');
  const [modelB, setModelB] = useState('SAC');
  const [splitA, setSplitA] = useState(50);
  const [showForm, setShowForm] = useState(false);

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['ab-campaigns'],
    queryFn: async () => { const r = await api.get('/api/ab-test/campaigns'); return r.data; },
  });

  const handleCreate = async () => {
    if (!name.trim()) return;
    if (modelA === modelB) { alert('Models must be different'); return; }
    try {
      await api.post('/api/ab-test/campaigns', { campaign_name: name, model_a: modelA, model_b: modelB, split_a: splitA });
      setName(''); setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ['ab-campaigns'] });
    } catch (e: any) { alert(`Error: ${e.response?.data?.detail || e.message}`); }
  };

  const handleToggle = async (id: number) => {
    await api.post(`/api/ab-test/campaigns/${id}/toggle`);
    queryClient.invalidateQueries({ queryKey: ['ab-campaigns'] });
  };

  // Find active campaign models or defaults
  const activeCampaign = (campaigns || []).find((c: any) => c.is_active);
  const simModelA = activeCampaign?.model_a || 'PPO';
  const simModelB = activeCampaign?.model_b || 'DDQN';

  // Simulated analytics data (consistent with seeded random)
  const simData = useMemo(() => {
    const rng = seededRandom(42);
    const approvalA = 0.68 + rng() * 0.10;
    const approvalB = 0.60 + rng() * 0.12;
    const defaultA = 0.05 + rng() * 0.07;
    const defaultB = 0.08 + rng() * 0.10;
    const profitA = 18000 + rng() * 14000;
    const profitB = 12000 + rng() * 13000;

    const summary = [
      { model: simModelA, total_applications: 200, approval_rate: approvalA, default_rate: defaultA, expected_profit: profitA },
      { model: simModelB, total_applications: 200, approval_rate: approvalB, default_rate: defaultB, expected_profit: profitB },
    ];

    // Timeline
    const rng2 = seededRandom(7);
    const timeline: any[] = [];
    let cumA = 0, cumB = 0;
    for (let i = 0; i < 30; i++) {
      cumA += 500 + (rng2() - 0.3) * 600;
      cumB += 300 + (rng2() - 0.3) * 700;
      timeline.push({ day: i + 1, [simModelA]: Math.max(0, Math.round(cumA)), [simModelB]: Math.max(0, Math.round(cumB)) });
    }

    return { summary, timeline };
  }, [simModelA, simModelB]);

  const totalApps = simData.summary.reduce((s: any, d: any) => s + d.total_applications, 0);
  const leader = simData.summary.reduce((a: any, b: any) => a.expected_profit > b.expected_profit ? a : b).model;
  const bestApproval = Math.max(...simData.summary.map((d: any) => d.approval_rate));
  const lowestDefault = Math.min(...simData.summary.map((d: any) => d.default_rate));

  const models = ['PPO', 'DQN', 'DDQN', 'SAC'];

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>⚖️ Live A/B Testing</Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>Deploy different models to subsets and track real-world metrics</Typography>
        </Box>
        <Button variant="contained" onClick={() => setShowForm(!showForm)}>➕ New Campaign</Button>
      </Box>

      {/* Create Campaign */}
      {showForm && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Create A/B Test Campaign</Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={3}>
                <TextField label="Campaign Name" fullWidth size="small" value={name} onChange={e => setName(e.target.value)} />
              </Grid>
              <Grid item xs={12} sm={2}>
                <FormControl fullWidth size="small"><InputLabel>Model A</InputLabel>
                  <Select value={modelA} label="Model A" onChange={e => setModelA(e.target.value)}>{models.map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}</Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={2}>
                <FormControl fullWidth size="small"><InputLabel>Model B</InputLabel>
                  <Select value={modelB} label="Model B" onChange={e => setModelB(e.target.value)}>{models.map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}</Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="caption">Traffic to A: {splitA}%</Typography>
                <Slider value={splitA} onChange={(_, v) => setSplitA(v as number)} min={0} max={100} />
              </Grid>
              <Grid item xs={12} sm={2}>
                <Button variant="contained" fullWidth onClick={handleCreate}>Create</Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Campaign List */}
      {isLoading ? <CircularProgress /> : (campaigns && Array.isArray(campaigns) && campaigns.length > 0) ? (
        <Box sx={{ mb: 4 }}>
          {campaigns.map((c: any) => (
            <Card key={c.id} sx={{ mb: 1 }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 2, '&:last-child': { pb: 2 } }}>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{c.campaign_name}</Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>Created: {c.timestamp?.substring(0, 10)}</Typography>
                </Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  <b>{c.model_a}</b> ({c.split_a}%) vs <b>{c.model_b}</b> ({100 - c.split_a}%)
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip label={c.is_active ? 'Active' : 'Inactive'} color={c.is_active ? 'success' : 'default'} size="small" />
                  <Button size="small" variant="outlined" onClick={() => handleToggle(c.id)}>
                    {c.is_active ? 'Stop' : 'Start'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      ) : (
        <Alert severity="info" sx={{ mb: 4 }}>No campaigns yet. Create one above.</Alert>
      )}

      <Divider sx={{ mb: 3 }} />

      {/* Analytics */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Live A/B Testing Analytics</Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        💡 Showing <b>simulated</b> results to demonstrate the dashboard. Process real loans with an active campaign to see live data.
      </Alert>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { label: 'Total A/B Applications', value: totalApps.toLocaleString() },
          { label: 'Leading Model', value: leader },
          { label: 'Best Approval Rate', value: `${(bestApproval * 100).toFixed(1)}%` },
          { label: 'Lowest Default Rate', value: `${(lowestDefault * 100).toFixed(1)}%` },
        ].map(k => (
          <Grid item xs={6} md={3} key={k.label}>
            <Card><CardContent>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>{k.label}</Typography>
              <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>{k.value}</Typography>
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>💰 Expected Profit by Model</Typography>
            <Box sx={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={simData.summary}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="model" />
                  <YAxis />
                  <RechartsTooltip formatter={(v: any) => `$${v.toFixed(0)}`} />
                  <Bar dataKey="expected_profit" fill="#636EFA" name="Expected Profit" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>📊 Approval vs Default Rate</Typography>
            <Box sx={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={simData.summary}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="model" />
                  <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <RechartsTooltip formatter={(v: any) => `${(v * 100).toFixed(1)}%`} />
                  <Legend />
                  <Bar dataKey="approval_rate" fill="#2ca02c" name="Approval Rate" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="default_rate" fill="#d62728" name="Default Rate" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* Timeline Chart */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>📈 Cumulative Profit Over Time</Typography>
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simData.timeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" label={{ value: 'Day', position: 'insideBottomRight', offset: -5 }} />
                <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <RechartsTooltip formatter={(v: any) => `$${v.toLocaleString()}`} />
                <Legend />
                <Line type="monotone" dataKey={simModelA} stroke="#636EFA" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey={simModelB} stroke="#EF553B" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

      {/* Metrics Table */}
      <Card>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>📋 Detailed Metrics Summary</Typography>
          <Box sx={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #E1E7EC' }}>
                  {['Model', 'Applications', 'Approval Rate', 'Default Rate', 'Expected Profit'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#667085' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {simData.summary.map((d: any) => (
                  <tr key={d.model} style={{ borderBottom: '1px solid #E1E7EC' }}>
                    <td style={{ padding: '10px 16px', fontWeight: 600 }}>{d.model}</td>
                    <td style={{ padding: '10px 16px' }}>{d.total_applications}</td>
                    <td style={{ padding: '10px 16px' }}>{(d.approval_rate * 100).toFixed(2)}%</td>
                    <td style={{ padding: '10px 16px' }}>{(d.default_rate * 100).toFixed(2)}%</td>
                    <td style={{ padding: '10px 16px' }}>${d.expected_profit.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}



