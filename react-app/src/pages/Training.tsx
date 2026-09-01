import { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Button, Select, MenuItem, FormControl,
  InputLabel, TextField, LinearProgress, CircularProgress, Tabs, Tab, Alert, Chip, Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon, Stop as StopIcon,
  Refresh as RefreshIcon, } from '@mui/icons-material';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export default function Training() {
  const queryClient = useQueryClient();
  const [mainTab, setMainTab] = useState(0);

  // Quick Train state
  const [quickModel, setQuickModel] = useState('PPO');
  const [quickTimesteps, setQuickTimesteps] = useState(10000);
  const [quickTraining, setQuickTraining] = useState(false);
  const [quickMsg, setQuickMsg] = useState<string | null>(null);

  // Hyperparams & launch state
  const [algorithm, setAlgorithm] = useState('PPO');
  const [learningRate, setLearningRate] = useState(0.0003);
  const [batchSize, setBatchSize] = useState(64);
  const [bufferSize, setBufferSize] = useState(100000);
  const [totalTimesteps, setTotalTimesteps] = useState(10000);
  const [gamma, setGamma] = useState(0.99);
  const [entCoef, setEntCoef] = useState(0.01);

  // Live dashboard state
  const [activeExpId, setActiveExpId] = useState<number | null>(null);
  const [liveStatus, setLiveStatus] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);

  // ─── Queries ──────────────────────────────────────────────
  const { data: modelStatus } = useQuery({
    queryKey: ['models-status'],
    queryFn: async () => { const r = await api.get('/api/models'); return r.data; },
  });

  const { data: trainingHistory } = useQuery({
    queryKey: ['training-history'],
    queryFn: async () => { const r = await api.get('/api/history'); return r.data; },
  });

  const { data: modelComparison } = useQuery({
    queryKey: ['model-comparison'],
    queryFn: async () => { const r = await api.get('/api/model-comparison'); return r.data; },
  });

  const { data: hardwareInfo } = useQuery({
    queryKey: ['hardware'],
    queryFn: async () => { const r = await api.get('/api/hardware'); return r.data; },
  });

  const { data: projects } = useQuery({
    queryKey: ['training-projects'],
    queryFn: async () => { const r = await api.get('/api/training/projects'); return r.data; },
  });

  const { data: experiments } = useQuery({
    queryKey: ['experiments'],
    queryFn: async () => { const r = await api.get('/api/training/experiments'); return r.data; },
  });

  // Apply recommended profile when hardware loaded
  useEffect(() => {
    if (hardwareInfo?.recommended_profile) {
      const p = hardwareInfo.recommended_profile;
      setLearningRate(p.learning_rate || 0.0003);
      setBatchSize(p.batch_size || 64);
      setBufferSize(p.buffer_size || 100000);
    }
  }, [hardwareInfo]);

  // Poll live training status
  useEffect(() => {
    if (!activeExpId) return;
    const interval = setInterval(async () => {
      try {
        const r = await api.get(`/api/training/experiments/${activeExpId}/status`);
        setLiveStatus(r.data);
        if (r.data.status !== 'Running') { clearInterval(interval); }
      } catch { /* ignore */ }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeExpId]);

  // ─── Quick Train ──────────────────────────────────────────
  const handleQuickTrain = async () => {
    setQuickTraining(true);
    setQuickMsg(null);
    try {
      await api.post(`/api/train?model_type=${quickModel}&total_timesteps=${quickTimesteps}`);
      setQuickMsg(`✅ Training started for ${quickModel} (${quickTimesteps} timesteps). Refresh after completion.`);
    } catch (e: any) {
      setQuickMsg(`❌ Error: ${e.response?.data?.detail || e.message}`);
    } finally {
      setQuickTraining(false);
    }
  };

  // ─── Reload Models ────────────────────────────────────────
  const handleReloadAll = async () => {
    try {
      await api.post('/api/models/reload-all');
      queryClient.invalidateQueries({ queryKey: ['models-status'] });
    } catch { /* ignore */ }
  };

  // ─── Deploy ───────────────────────────────────────────────
  const handleDeploy = async (expId: number) => {
    try {
      await api.post(`/api/training/experiments/${expId}/deploy`);
      alert('Model deployed to production!');
      queryClient.invalidateQueries({ queryKey: ['models-status'] });
    } catch (e: any) {
      alert(`Deploy failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  // ─── AI Analyze ───────────────────────────────────────────
  const handleAnalyze = async (expId: number) => {
    setAnalysisResult(null);
    try {
      const r = await api.get(`/api/training/experiments/${expId}/analyze`);
      setAnalysisResult(r.data.analysis);
    } catch (e: any) {
      setAnalysisResult(`Error: ${e.response?.data?.detail || e.message}`);
    }
  };

  // ─── Model status cards helper ────────────────────────────
  const modelNames = ['PPO', 'DQN', 'DDQN', 'SAC'];
  const statusIcons: Record<string, string> = { loaded: '🟢', on_disk: '🟡', not_trained: '🔴' };
  const statusLabels: Record<string, string> = { loaded: 'Loaded & Ready', on_disk: 'Saved (Not Loaded)', not_trained: 'Not Trained' };
  const borderColors: Record<string, string> = { loaded: '#27AE60', on_disk: '#F2C94C', not_trained: '#E74C3C' };

  const hw = hardwareInfo?.hardware;
  const profile = hardwareInfo?.recommended_profile;

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
          🧠 Intelligent Adaptive Training Studio
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Automatically configures RL models based on your hardware and tracks all experiments
        </Typography>
      </Box>

      {/* ─── Model Registry Status ─────────────────────── */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🗄️ Loaded Prediction Models</Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        {modelNames.map(name => {
          const info = modelStatus?.[name];
          const isNill = info === 'NILL' || !info;
          const s = isNill ? 'not_trained' : (info?.status || 'not_trained');
          const size = isNill ? 'N/A' : (info?.size_mb && info.size_mb !== 'NILL' ? `${info.size_mb} MB` : 'N/A');
          return (
            <Grid item xs={6} md={3} key={name}>
              <Card sx={{ borderTop: `4px solid ${borderColors[s] || '#ccc'}`, textAlign: 'center' }}>
                <CardContent sx={{ py: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#1F4E79' }}>{statusIcons[s] || '⚪'} {name}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: borderColors[s] }}>{statusLabels[s] || 'Unknown'}</Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>Size: {size}</Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
      <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleReloadAll} sx={{ mb: 4 }}>
        🔄 Reload All Models
      </Button>

      <Divider sx={{ mb: 3 }} />

      {/* ─── Tabs ──────────────────────────────────────── */}
      <Tabs value={mainTab} onChange={(_, v) => setMainTab(v)} sx={{ mb: 3 }} variant="scrollable" scrollButtons="auto">
        <Tab label="🚀 Quick Train" />
        <Tab label="💻 Hardware" />
        <Tab label="⚙️ Hyperparameters" />
        <Tab label="📈 Live Dashboard" />
        <Tab label="🔬 Experiments" />
      </Tabs>

      {/* ═══ TAB 0: Quick Train ═══ */}
      {mainTab === 0 && (
        <Box>
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Train on Built-in Dataset</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                Quickly train any RL algorithm using the project's default loan dataset.
              </Typography>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Model</InputLabel>
                    <Select value={quickModel} label="Model" onChange={e => setQuickModel(e.target.value)}>
                      {modelNames.map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField label="Total Timesteps" type="number" fullWidth size="small"
                    value={quickTimesteps} onChange={e => setQuickTimesteps(parseInt(e.target.value) || 1000)}
                    inputProps={{ min: 1000, max: 1000000, step: 1000 }}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button variant="contained" fullWidth startIcon={quickTraining ? <CircularProgress size={18} color="inherit" /> : <PlayIcon />}
                    onClick={handleQuickTrain} disabled={quickTraining} sx={{ py: 1.2 }}
                  >
                    ▶ Start Training
                  </Button>
                </Grid>
              </Grid>
              {quickMsg && <Alert severity={quickMsg.startsWith('✅') ? 'success' : 'error'} sx={{ mt: 2 }}>{quickMsg}</Alert>}
            </CardContent>
          </Card>

          {/* Training History Chart */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={7}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>📊 Training History</Typography>
                  {trainingHistory && Array.isArray(trainingHistory) && trainingHistory.length > 0 ? (
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trainingHistory}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E1E7EC" />
                          <XAxis dataKey="episode" />
                          <YAxis />
                          <RechartsTooltip />
                          <Legend />
                          <Line type="monotone" dataKey="reward" stroke="#0066A1" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary', py: 4, textAlign: 'center' }}>
                      No training history yet. Train a model to see results.
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🏆 Model Comparison</Typography>
                  {modelComparison && Array.isArray(modelComparison) && modelComparison.length > 0 ? (
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={modelComparison}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="model" />
                          <YAxis />
                          <RechartsTooltip />
                          <Legend />
                          <Bar dataKey="avg_reward" fill="#2F80ED" name="Avg Reward" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="max_reward" fill="#27AE60" name="Max Reward" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary', py: 4, textAlign: 'center' }}>
                      No comparison data yet.
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* ═══ TAB 1: Hardware ═══ */}
      {mainTab === 1 && (
        <Box>
          {hw ? (
            <>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>System Architecture</Typography>
              <Grid container spacing={2} sx={{ mb: 4 }}>
                {[
                  { title: 'OS', value: `${hw.os} ${hw.os_version}`, color: '#00A67E' },
                  { title: 'Processor', value: `${hw.cpu_threads} Threads`, sub: hw.cpu_brand, color: '#3b82f6' },
                  { title: 'Memory (RAM)', value: hw.ram_total, sub: `${hw.ram_percent}% Used`, color: '#f59e0b' },
                  { title: 'GPU', value: hw.gpus?.[0]?.name || 'CPU Only', sub: `CUDA: ${hw.cuda_available} | MPS: ${hw.mps_available}`, color: '#ef4444' },
                ].map(card => (
                  <Grid item xs={6} md={3} key={card.title}>
                    <Card sx={{ bgcolor: '#1E1E1E', borderLeft: `5px solid ${card.color}` }}>
                      <CardContent>
                        <Typography variant="caption" sx={{ color: '#A0A0A0', textTransform: 'uppercase', fontWeight: 600 }}>{card.title}</Typography>
                        <Typography variant="h6" sx={{ color: '#fff', fontWeight: 700 }}>{card.value}</Typography>
                        {card.sub && <Typography variant="caption" sx={{ color: '#bbb' }}>{card.sub}</Typography>}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              {profile && (
                <>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🤖 Recommended Training Profile</Typography>
                  <Alert severity="info" sx={{ mb: 2 }}><b>{profile.name}</b>: {profile.notes}</Alert>
                  <Grid container spacing={2}>
                    {[
                      { label: 'Target Device', val: (profile.device || 'cpu').toUpperCase() },
                      { label: 'Batch Size', val: profile.batch_size },
                      { label: 'Buffer Size', val: profile.buffer_size },
                      { label: 'Parallel Envs', val: profile.n_envs },
                    ].map(m => (
                      <Grid item xs={6} md={3} key={m.label}>
                        <Card>
                          <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>{m.label}</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 600 }}>{m.val}</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}
            </>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
          )}
        </Box>
      )}

      {/* ═══ TAB 2: Hyperparameters ═══ */}
      {mainTab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>Algorithm & Hyperparameters</Typography>
            {profile && <Alert severity="info" sx={{ mb: 2 }}>Applied Profile: <b>{profile.name}</b></Alert>}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>RL Algorithm</InputLabel>
                  <Select value={algorithm} label="RL Algorithm" onChange={e => setAlgorithm(e.target.value)}>
                    {modelNames.map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField label="Learning Rate" type="number" fullWidth size="small" value={learningRate}
                  onChange={e => setLearningRate(parseFloat(e.target.value))} inputProps={{ step: 0.00001 }} sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField label="Batch Size" type="number" fullWidth size="small" value={batchSize}
                  onChange={e => setBatchSize(parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField label="Buffer Size" type="number" fullWidth size="small" value={bufferSize}
                  onChange={e => setBufferSize(parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField label="Total Timesteps" type="number" fullWidth size="small" value={totalTimesteps}
                  onChange={e => setTotalTimesteps(parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" sx={{ mb: 1 }}>Gamma (Discount Factor): {gamma}</Typography>
                <Box sx={{ px: 1 }}>
                  <input type="range" min={0.8} max={0.999} step={0.001} value={gamma}
                    onChange={e => setGamma(parseFloat(e.target.value))} style={{ width: '100%' }}
                  />
                </Box>
              </Grid>
              {(algorithm === 'PPO' || algorithm === 'SAC') && (
                <Grid item xs={12} md={6}>
                  <TextField label="Entropy Coefficient" type="number" fullWidth size="small" value={entCoef}
                    onChange={e => setEntCoef(parseFloat(e.target.value))} inputProps={{ step: 0.001 }}
                  />
                </Grid>
              )}
            </Grid>
            <Box sx={{ mt: 3 }}>
              <Button variant="contained" size="large" fullWidth startIcon={<PlayIcon />}
                onClick={async () => {
                  try {
                    const payload = {
                      project_id: projects?.[0]?.id || 1,
                      dataset_id: 1,
                      algorithm,
                      profile_name: profile?.name || 'default',
                      hyperparameters: JSON.stringify({ learning_rate: learningRate, batch_size: batchSize, buffer_size: bufferSize, total_timesteps: totalTimesteps, gamma, ent_coef: entCoef }),
                    };
                    const r = await api.post('/api/training/experiments', payload);
                    setActiveExpId(r.data.id);
                    setMainTab(3); // Switch to Live Dashboard
                  } catch (e: any) {
                    alert(`Launch failed: ${e.response?.data?.detail || e.message}`);
                  }
                }}
                sx={{ py: 1.5, fontWeight: 600 }}
              >
                🚀 Launch Training Job
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ═══ TAB 3: Live Dashboard ═══ */}
      {mainTab === 3 && (
        <Box>
          {activeExpId && liveStatus ? (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Live Training Telemetry — Status: <b>{liveStatus.status}</b>
                </Typography>
                <LinearProgress variant="determinate" value={(liveStatus.progress || 0) * 100} sx={{ height: 10, borderRadius: 5, mb: 3 }} />
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={4}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Episode</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>{liveStatus.current_episode}</Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Best Reward</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
                      {liveStatus.rewards?.length > 0 ? Math.max(...liveStatus.rewards).toFixed(4) : 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Speed</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>{liveStatus.speed} steps/s</Typography>
                  </Grid>
                </Grid>

                {liveStatus.rewards?.length > 0 && (
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={liveStatus.rewards.map((r: number, i: number) => ({ ep: i, reward: r, loss: liveStatus.losses?.[i] || 0 }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="ep" />
                        <YAxis yAxisId="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <RechartsTooltip />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="reward" stroke="#00A67E" strokeWidth={2} dot={false} name="Reward" />
                        <Line yAxisId="right" type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={1} strokeDasharray="5 5" dot={false} name="Loss" />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                )}

                {liveStatus.status === 'Running' && (
                  <Button variant="outlined" color="error" startIcon={<StopIcon />} sx={{ mt: 2 }}
                    onClick={async () => { await api.post(`/api/training/experiments/${activeExpId}/cancel`); }}
                  >
                    ⏹ Stop Training
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <Alert severity="info">No active training job. Launch one from the Hyperparameters tab.</Alert>
          )}
        </Box>
      )}

      {/* ═══ TAB 4: Experiments ═══ */}
      {mainTab === 4 && (
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Experiment Tracking & History</Typography>
          {experiments && Array.isArray(experiments) && experiments.length > 0 ? (
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E1E7EC', textAlign: 'left' }}>
                    {['ID', 'Algorithm', 'Status', 'Best Reward', 'Started', 'Actions'].map(h => (
                      <th key={h} style={{ padding: '12px 16px', fontWeight: 600, color: '#667085' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {experiments.map((exp: any) => (
                    <tr key={exp.id} style={{ borderBottom: '1px solid #E1E7EC' }}>
                      <td style={{ padding: '10px 16px', fontWeight: 500 }}>#{exp.id}</td>
                      <td style={{ padding: '10px 16px' }}>{exp.algorithm}</td>
                      <td style={{ padding: '10px 16px' }}>
                        <Chip label={exp.status} size="small" color={exp.status === 'Completed' ? 'success' : exp.status === 'Running' ? 'warning' : 'default'} />
                      </td>
                      <td style={{ padding: '10px 16px' }}>{exp.best_reward ?? '—'}</td>
                      <td style={{ padding: '10px 16px' }}>{exp.start_time?.substring(0, 19)}</td>
                      <td style={{ padding: '10px 16px' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button size="small" variant="contained" onClick={() => handleDeploy(exp.id)} disabled={exp.status !== 'Completed'}>
                            Deploy
                          </Button>
                          <Button size="small" variant="outlined" onClick={() => handleAnalyze(exp.id)}>
                            Analyze
                          </Button>
                        </Box>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          ) : (
            <Alert severity="info">No experiments recorded yet.</Alert>
          )}

          {analysisResult && (
            <Card sx={{ mt: 3, bgcolor: '#2D3748', color: '#fff', borderLeft: '5px solid #00A67E' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>🤖 AI Analysis</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{analysisResult}</Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
}


