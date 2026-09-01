import { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Card, CardContent, Typography, Grid, Slider, CircularProgress, Alert } from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer
} from 'recharts';
import api from '../services/api';

export default function Simulator() {
  const [age, setAge] = useState(30);
  const [income, setIncome] = useState(5000);
  const [creditScore, setCreditScore] = useState(0.7);
  const [loanAmount, setLoanAmount] = useState(10000);
  const [existingDebt, setExistingDebt] = useState(1000);
  const [repaymentHistory, setRepaymentHistory] = useState(0.8);

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchPrediction = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        age, gender: 'Male', employment: 'Salaried', income, credit_score: creditScore,
        loan_amount: loanAmount, existing_debt: existingDebt, loan_tenure: 24,
        repayment_history: repaymentHistory, loan_purpose: 'Personal', region: 'Urban',
        collateral: 'None', existing_loans: 0, education: "Bachelor's",
      };
      const r = await api.post('/api/predict', payload);
      setResult(r.data);
    } catch (e: any) {
      setError(`Cannot reach backend: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [age, income, creditScore, loanAmount, existingDebt, repaymentHistory]);

  // Debounced fetch on slider change
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(fetchPrediction, 600);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [fetchPrediction]);

  const rec = result?.recommended_pricing || {};
  const risk = result?.risk_analysis || {};
  const rl = result?.rl_predictions || {};
  const rate = rec.recommended_interest_rate;
  const decision = rate != null ? `Approve @ ${rate}%` : 'Reject';
  const color = rate != null ? '#27AE60' : '#E74C3C';

  // Bar chart data: extract rates from RL predictions
  const modelRates = Object.entries(rl).map(([model, value]) => {
    let rateVal = 0;
    const str = String(value);
    if (str.includes('@')) {
      try { rateVal = parseFloat(str.split('@')[1].replace('%', '').trim()); } catch {}
    }
    return { Model: model, Rate: rateVal };
  });

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
          🎛️ AI What-If Simulator
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Adjust the sliders to see how the RL Ensemble's prediction changes in real-time
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Left: Sliders */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>🔧 Applicant Variables</Typography>

              {[
                { label: 'Age', value: age, set: setAge, min: 18, max: 100, step: 1, format: (v: number) => `${v}` },
                { label: 'Monthly Income ($)', value: income, set: setIncome, min: 0, max: 20000, step: 500, format: (v: number) => `$${v.toLocaleString()}` },
                { label: 'Credit Score (0-1)', value: creditScore, set: setCreditScore, min: 0, max: 1, step: 0.01, format: (v: number) => v.toFixed(2) },
                { label: 'Loan Amount ($)', value: loanAmount, set: setLoanAmount, min: 500, max: 50000, step: 500, format: (v: number) => `$${v.toLocaleString()}` },
                { label: 'Existing Debt ($)', value: existingDebt, set: setExistingDebt, min: 0, max: 20000, step: 500, format: (v: number) => `$${v.toLocaleString()}` },
                { label: 'Repayment History', value: repaymentHistory, set: setRepaymentHistory, min: 0, max: 1, step: 0.01, format: (v: number) => v.toFixed(2) },
              ].map(s => (
                <Box key={s.label} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{s.label}</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>{s.format(s.value)}</Typography>
                  </Box>
                  <Slider value={s.value} onChange={(_, v) => s.set(v as number)}
                    min={s.min} max={s.max} step={s.step} valueLabelDisplay="auto"
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Right: Live Inference */}
        <Grid item xs={12} md={8}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {error && <Alert severity="error">{error}</Alert>}

            {/* Decision Banner */}
            <Card sx={{ borderTop: `4px solid ${result ? color : '#ccc'}` }}>
              <CardContent sx={{ textAlign: 'center', py: 3, position: 'relative' }}>
                {loading && (
                  <Box sx={{ position: 'absolute', top: 8, right: 12 }}>
                    <CircularProgress size={20} />
                  </Box>
                )}
                <Typography variant="subtitle1" sx={{ color: 'text.secondary' }}>Ensemble Recommendation</Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, color: result ? color : 'text.secondary', my: 1 }}>
                  {result ? decision : 'Waiting...'}
                </Typography>
                {result && (
                  <Typography variant="body1">
                    Risk Score: <b>{risk.risk_score}</b> &nbsp;|&nbsp; Confidence: <b>{((risk.confidence || 0) * 100).toFixed(1)}%</b>
                  </Typography>
                )}
              </CardContent>
            </Card>

            {/* Model Comparison Chart */}
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Interest Rate by Model</Typography>
                {result ? (
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={modelRates}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="Model" />
                        <YAxis label={{ value: 'Rate %', angle: -90, position: 'insideLeft' }} />
                        <RechartsTooltip formatter={(v: any) => `${v}%`} />
                        <Bar dataKey="Rate" radius={[4, 4, 0, 0]}>
                          {modelRates.map((_, i) => {
                            const fills = ['#1F4E79', '#2F80ED', '#56CCF2', '#27AE60'];
                            return <rect key={i} fill={fills[i % fills.length]} />;
                          })}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                ) : (
                  <Typography variant="body2" sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
                    Move a slider to trigger inference...
                  </Typography>
                )}
              </CardContent>
            </Card>

            {/* Rate Change Summary */}
            {result && (
              <Card sx={{ bgcolor: '#173F5F', color: '#fff' }}>
                <CardContent sx={{ py: 2, textAlign: 'center' }}>
                  <Typography variant="body1">
                    Recommended Rate: <b>{rate != null ? `${rate}%` : 'Rejected'}</b> &nbsp;|&nbsp;
                    Risk Level: <b>{risk.risk_level || 'N/A'}</b> &nbsp;|&nbsp;
                    Best Model: <b>{rec.best_model || 'N/A'}</b>
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}


