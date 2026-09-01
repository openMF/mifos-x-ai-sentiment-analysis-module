import { useState, useCallback } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, Divider, Chip, TextField,
  Select, MenuItem, FormControl, InputLabel, Slider, CircularProgress,
  Alert, Stepper, Step, StepLabel, Tab, Tabs
} from '@mui/material';
import {
  Send as SendIcon, Refresh as RefreshIcon
} from '@mui/icons-material';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend
} from 'recharts';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const progressSteps = [
  'Validating Data',
  'Feature Engineering',
  'RL Ensemble Inference',
  'AI Explanation',
  'Complete',
];

export default function Loans() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(0);

  // ─── Form State ────────────────────────────────────────────
  const [form, setForm] = useState({
    age: 30, gender: 'Male', employment: 'Salaried', income: 5000, region: 'Urban',
    credit_score: 0.7, existing_debt: 1000, loan_amount: 10000, loan_tenure: 24,
    loan_purpose: 'Personal', collateral: 'None', existing_loans: 1, education: "Bachelor's",
    repayment_history: 0.8, interview_notes: '',
  });

  // ─── Prediction State ──────────────────────────────────────
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // ─── Negotiation State ─────────────────────────────────────
  const [negAmount, setNegAmount] = useState(10000);
  const [negTenure, setNegTenure] = useState(24);
  const [negDebt, setNegDebt] = useState(1000);

  // ─── Decision State ────────────────────────────────────────
  const [remarks, setRemarks] = useState('');

  // ─── Applications list ─────────────────────────────────────
  const { data: applications } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => { const r = await api.get('/api/applications'); return r.data; },
  });

  const updateField = (field: string, value: any) => {
    setForm((prev: any) => ({ ...prev, [field]: value }));
  };

  // ─── Submit to AI Engine ───────────────────────────────────
  const handleSubmit = useCallback(async (payload?: any) => {
    const data = payload || form;
    setLoading(true);
    setError(null);
    setResult(null);
    setSuccessMsg(null);

    try {
      // Animated progress steps
      for (let i = 0; i < progressSteps.length - 1; i++) {
        setActiveStep(i);
        await new Promise(r => setTimeout(r, 500));
      }

      const response = await api.post('/api/predict', {
        ...data,
        interview_notes: data.interview_notes || undefined,
      });
      setActiveStep(progressSteps.length - 1);
      setResult(response.data);
      setNegAmount(data.loan_amount);
      setNegTenure(data.loan_tenure);
      setNegDebt(data.existing_debt);
      setSuccessMsg('✅ Application successfully processed by the AI Engine.');
    } catch (e: any) {
      const msg = e.response?.status === 401
        ? '🔒 Session expired. Please re-login.'
        : `API Error: ${e.response?.data?.detail || e.message}`;
      setError(msg);
    } finally {
      setLoading(false);
      setTimeout(() => setActiveStep(-1), 1500);
    }
  }, [form]);

  // ─── Re-Evaluate with negotiation params ───────────────────
  const handleReEvaluate = () => {
    handleSubmit({ ...form, loan_amount: negAmount, loan_tenure: negTenure, existing_debt: negDebt });
  };

  // ─── Push Decision ─────────────────────────────────────────
  const handleDecision = async () => {
    if (!remarks.trim()) { setError('Please provide officer remarks.'); return; }
    try {
      const rec = result?.recommended_pricing || {};
      await api.post('/api/loan-decisions', {
        application_id: result.application_id,
        officer_name: 'Loan Officer',
        remarks,
        approved: rec.recommended_interest_rate != null,
        rejected: rec.recommended_interest_rate == null,
      });
      setSuccessMsg('🎉 Application finalized and pushed to Core System!');
      setResult(null);
      setRemarks('');
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    } catch (e: any) {
      setError(`Failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  // ─── Radar chart data ──────────────────────────────────────
  const buildRadarData = () => {
    const credit = form.credit_score;
    const repayment = form.repayment_history;
    const incomeNorm = Math.min(form.income / 10000, 1.0);
    const debtInv = Math.max(0, 1.0 - form.existing_debt / Math.max(form.income, 1));
    return [
      { metric: 'Credit Score', applicant: credit, average: 0.75 },
      { metric: 'Repayment', applicant: repayment, average: 0.80 },
      { metric: 'Income (Norm)', applicant: incomeNorm, average: 0.50 },
      { metric: 'Debt Ratio (Inv)', applicant: debtInv, average: 0.70 },
    ];
  };

  const rec = result?.recommended_pricing || {};
  const risk = result?.risk_analysis || {};
  const rl = result?.rl_predictions || {};
  const explanation = result?.ollama_explanation || {};
  const rate = rec.recommended_interest_rate;
  const statusColor = rate != null ? '#27AE60' : '#E74C3C';
  const decisionText = rate != null ? `APPROVED @ ${rate}%` : 'REJECTED';

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
          📝 Loan Origination & Processing
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Submit applicant data to the AI Engine for RL-powered pricing
        </Typography>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="New Application" />
        <Tab label="Application History" />
      </Tabs>

      {/* ═══ TAB 0: New Application ═══ */}
      {tab === 0 && (
        <>
          {successMsg && <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMsg(null)}>{successMsg}</Alert>}
          {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}

          {/* ─── Application Form ─────────────────────── */}
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>👤 Applicant Profile</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Age" type="number" fullWidth size="small" value={form.age}
                    onChange={e => updateField('age', parseInt(e.target.value) || 18)}
                    inputProps={{ min: 18, max: 100 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Gender</InputLabel>
                    <Select value={form.gender} label="Gender" onChange={e => updateField('gender', e.target.value)}>
                      <MenuItem value="Male">Male</MenuItem>
                      <MenuItem value="Female">Female</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Education</InputLabel>
                    <Select value={form.education} label="Education" onChange={e => updateField('education', e.target.value)}>
                      {["High School", "Bachelor's", "Master's", "PhD"].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Employment</InputLabel>
                    <Select value={form.employment} label="Employment" onChange={e => updateField('employment', e.target.value)}>
                      {['Salaried', 'Self-Employed', 'Unemployed'].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Monthly Income ($)" type="number" fullWidth size="small"
                    value={form.income} onChange={e => updateField('income', parseFloat(e.target.value) || 0)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Region</InputLabel>
                    <Select value={form.region} label="Region" onChange={e => updateField('region', e.target.value)}>
                      {['Urban', 'Semiurban', 'Rural'].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Credit Score (0-1)" type="number" fullWidth size="small"
                    value={form.credit_score} onChange={e => updateField('credit_score', parseFloat(e.target.value) || 0)}
                    inputProps={{ step: 0.05, min: 0, max: 1 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Existing Debt ($)" type="number" fullWidth size="small"
                    value={form.existing_debt} onChange={e => updateField('existing_debt', parseFloat(e.target.value) || 0)}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Loan Amount ($)" type="number" fullWidth size="small"
                    value={form.loan_amount} onChange={e => updateField('loan_amount', parseFloat(e.target.value) || 100)}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Loan Tenure (Months)" type="number" fullWidth size="small"
                    value={form.loan_tenure} onChange={e => updateField('loan_tenure', parseInt(e.target.value) || 1)}
                    inputProps={{ min: 1, max: 360 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Loan Purpose</InputLabel>
                    <Select value={form.loan_purpose} label="Loan Purpose" onChange={e => updateField('loan_purpose', e.target.value)}>
                      {['Personal', 'Business', 'Education', 'Home'].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Collateral</InputLabel>
                    <Select value={form.collateral} label="Collateral" onChange={e => updateField('collateral', e.target.value)}>
                      {['None', 'Vehicle', 'Property', 'Gold'].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Repayment History (0-1)" type="number" fullWidth size="small"
                    value={form.repayment_history} onChange={e => updateField('repayment_history', parseFloat(e.target.value) || 0)}
                    inputProps={{ step: 0.05, min: 0, max: 1 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField label="Active Loans Count" type="number" fullWidth size="small"
                    value={form.existing_loans} onChange={e => updateField('existing_loans', parseInt(e.target.value) || 0)}
                    inputProps={{ min: 0 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, mt: 1 }}>💬 Alternative Data</Typography>
                  <TextField label="Loan Officer Interview Notes (Optional)" fullWidth multiline rows={3} size="small"
                    value={form.interview_notes} onChange={e => updateField('interview_notes', e.target.value)}
                    helperText="Sentiment analysis will be run on these notes to calculate a Behavioral Reliability Score."
                  />
                </Grid>
              </Grid>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button variant="contained" size="large" onClick={() => handleSubmit()} disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                  sx={{ py: 1.5, px: 4, fontWeight: 600 }}
                >
                  🚀 Submit to AI Engine
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* ─── Progress Stepper ─────────────────────── */}
          {activeStep >= 0 && (
            <Card sx={{ mb: 4 }}>
              <CardContent>
                <Stepper activeStep={activeStep} alternativeLabel>
                  {progressSteps.map(label => (
                    <Step key={label}><StepLabel>{label}</StepLabel></Step>
                  ))}
                </Stepper>
              </CardContent>
            </Card>
          )}

          {/* ═══ RESULTS ═══ */}
          {result && (
            <Box className="fade-in">
              {/* ─── Decision Banner ──────────────────── */}
              <Card sx={{ mb: 4, borderTop: `5px solid ${statusColor}`, textAlign: 'center' }}>
                <CardContent sx={{ py: 4 }}>
                  <Typography variant="subtitle1" sx={{ color: 'text.secondary' }}>AI Recommendation</Typography>
                  <Typography variant="h2" sx={{ fontWeight: 700, color: statusColor, my: 1 }}>{decisionText}</Typography>
                  <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                    Confidence: <b>{(risk.confidence * 100).toFixed(1)}%</b> &nbsp;|&nbsp; Primary Engine: <b>{rec.best_model}</b>
                  </Typography>
                </CardContent>
              </Card>

              {/* ─── XAI Explanations ─────────────────── */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🦙 AI-Generated Rationale</Typography>
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={6}>
                  <Alert severity="info" sx={{ height: '100%' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Customer-Friendly Explanation</Typography>
                    <Typography variant="body2">{explanation.customer_friendly_explanation || 'N/A'}</Typography>
                  </Alert>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Alert severity="warning" sx={{ height: '100%' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Officer Technical Explanation</Typography>
                    <Typography variant="body2">{explanation.officer_technical_explanation || 'N/A'}</Typography>
                  </Alert>
                </Grid>
              </Grid>

              {/* ─── Risk Analysis + Radar ────────────── */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={6}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🔍 Risk Analysis</Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={4}>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Risk Score</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>{risk.risk_score ?? 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Risk Level</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>{risk.risk_level ?? 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Expected Profit</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>${rec.expected_profit ?? 0}</Typography>
                        </Grid>
                      </Grid>

                      {risk.behavioral_score != null && risk.behavioral_score !== 'NILL' && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Behavioral Score (NLP)</Typography>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>
                            {typeof risk.behavioral_score === 'number' ? risk.behavioral_score.toFixed(2) : risk.behavioral_score}
                          </Typography>
                        </Box>
                      )}

                      <Divider sx={{ my: 2 }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>📊 Ensemble Breakdown</Typography>
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        {['PPO', 'DQN', 'DDQN', 'SAC'].map(m => (
                          <Chip key={m} label={`${m}: ${rl[m] ?? 'N/A'}`} variant="outlined" />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>🕸️ Peer Benchmarking</Typography>
                      <Box sx={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart data={buildRadarData()}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="metric" />
                            <PolarRadiusAxis domain={[0, 1]} />
                            <Radar name="Avg Approved" dataKey="average" stroke="#0066A1" fill="#0066A1" fillOpacity={0.2} />
                            <Radar name="Current Applicant" dataKey="applicant" stroke="#78BE20" fill="#78BE20" fillOpacity={0.4} />
                            <Legend />
                          </RadarChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* ─── Negotiation Mode ─────────────────── */}
              <Card sx={{ mb: 4 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>🎚️ Interactive Negotiation Mode</Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                    Adjust key variables to instantly see how it affects the AI decision.
                  </Typography>
                  <Grid container spacing={4}>
                    <Grid item xs={12} md={4}>
                      <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>Loan Amount: ${negAmount.toLocaleString()}</Typography>
                      <Slider value={negAmount} onChange={(_, v) => setNegAmount(v as number)} min={100} max={50000} step={500} valueLabelDisplay="auto" />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>Loan Tenure: {negTenure} months</Typography>
                      <Slider value={negTenure} onChange={(_, v) => setNegTenure(v as number)} min={1} max={360} step={1} valueLabelDisplay="auto" />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>Existing Debt: ${negDebt.toLocaleString()}</Typography>
                      <Slider value={negDebt} onChange={(_, v) => setNegDebt(v as number)} min={0} max={50000} step={500} valueLabelDisplay="auto" />
                    </Grid>
                  </Grid>
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleReEvaluate} disabled={loading}>
                      🔄 Re-Evaluate Application
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              {/* ─── Finalize Decision ────────────────── */}
              <Card sx={{ mb: 4 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🚀 Finalize Decision</Typography>
                  <TextField label="Officer Remarks (Required)" fullWidth size="small" sx={{ mb: 2 }}
                    value={remarks} onChange={e => setRemarks(e.target.value)}
                  />
                  <Button variant="contained" size="large" onClick={handleDecision} disabled={!remarks.trim()}
                    sx={{ py: 1.5, fontWeight: 600 }}
                  >
                    Submit to Core System
                  </Button>
                </CardContent>
              </Card>
            </Box>
          )}
        </>
      )}

      {/* ═══ TAB 1: History ═══ */}
      {tab === 1 && (
        <Card>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E1E7EC', textAlign: 'left' }}>
                    {['ID', 'Age', 'Gender', 'Income', 'Loan Amt', 'Purpose', 'Region', 'Best Model', 'Rate', 'Risk', 'Status'].map(h => (
                      <th key={h} style={{ padding: '12px 16px', fontWeight: 600, color: '#667085' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {applications && Array.isArray(applications) ? applications.slice(0, 50).map((a: any) => {
                    const pred = a.prediction || {};
                    const dec = a.decision;
                    const status = dec?.approved === true ? 'Approved' : dec?.approved === false ? 'Rejected' : 'Pending';
                    const statusColor2 = status === 'Approved' ? '#27AE60' : status === 'Rejected' ? '#E74C3C' : '#ED8B00';
                    return (
                      <tr key={a.id} style={{ borderBottom: '1px solid #E1E7EC' }}>
                        <td style={{ padding: '10px 16px', fontWeight: 500 }}>#{a.id}</td>
                        <td style={{ padding: '10px 16px' }}>{a.age}</td>
                        <td style={{ padding: '10px 16px' }}>{a.gender}</td>
                        <td style={{ padding: '10px 16px' }}>${a.income?.toLocaleString()}</td>
                        <td style={{ padding: '10px 16px' }}>${a.loan_amount?.toLocaleString()}</td>
                        <td style={{ padding: '10px 16px' }}>{a.loan_purpose}</td>
                        <td style={{ padding: '10px 16px' }}>{a.region}</td>
                        <td style={{ padding: '10px 16px' }}>{pred.best_model || '—'}</td>
                        <td style={{ padding: '10px 16px' }}>{pred.recommended_rate != null ? `${pred.recommended_rate}%` : '—'}</td>
                        <td style={{ padding: '10px 16px' }}>{pred.risk_score ?? '—'}</td>
                        <td style={{ padding: '10px 16px' }}>
                          <Chip label={status} size="small" sx={{ bgcolor: statusColor2, color: '#fff', fontWeight: 600, fontSize: '0.75rem' }} />
                        </td>
                      </tr>
                    );
                  }) : (
                    <tr><td colSpan={11} style={{ padding: '40px', textAlign: 'center', color: '#667085' }}>No applications found. Submit one above!</td></tr>
                  )}
                </tbody>
              </table>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}



