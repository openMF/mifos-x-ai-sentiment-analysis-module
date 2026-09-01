import { Box, Grid, Card, CardContent, Typography, Divider, Stack, CircularProgress, Chip } from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const pipelineSteps = [
  'Applicant Data',
  'Risk Assessment',
  'Sentiment Analysis',
  'RL Pricing Agent',
  'Fairness Check',
  'Human Review',
  'Final Decision',
];

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => { const r = await api.get('/api/dashboard'); return r.data; },
  });

  const { data: applications } = useQuery({
    queryKey: ['dashboard-applications'],
    queryFn: async () => { const r = await api.get('/api/applications'); return r.data; },
  });

  if (isLoading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  if (error) {
    return <Typography color="error">Error loading dashboard data.</Typography>;
  }

  const kpis = [
    { title: 'Total Applications', value: data?.total_applications?.toString() || '0' },
    { title: 'Approval Rate', value: `${((data?.approval_rate || 0) * 100).toFixed(1)}%` },
    { title: 'Portfolio Value', value: `₹${(data?.portfolio_value || 0).toLocaleString()}` },
    { title: 'Avg Interest Rate', value: `${(data?.average_interest_rate || 0).toFixed(1)}%` },
    { title: 'Default Rate', value: `${((data?.default_rate || 0) * 100).toFixed(1)}%` },
  ];

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            Welcome back, Loan Officer
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {kpis.map((kpi) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={kpi.title}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 1, fontWeight: 500 }}>
                  {kpi.title}
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {kpi.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <Card sx={{ height: '100%', border: '1px solid #78BE20', backgroundColor: '#EEF7E5' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ color: '#4F8F18', mb: 1, fontWeight: 600 }}>
                Model Health
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ color: '#78BE20', mr: 1 }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: '#4F8F18' }}>
                  Healthy
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
        AI Decision Pipeline
      </Typography>
      <Card sx={{ mb: 4, overflow: 'visible' }}>
        <CardContent sx={{ p: 4 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ position: 'relative' }}>
            <Divider sx={{ position: 'absolute', width: '100%', top: '50%', zIndex: 0, borderColor: 'primary.light', borderWidth: 2 }} />
            {pipelineSteps.map((step, index) => (
              <Box key={step} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1, width: 120 }}>
                <Box
                  sx={{
                    width: 24, height: 24, borderRadius: '50%',
                    backgroundColor: index === pipelineSteps.length - 1 ? 'secondary.main' : 'primary.main',
                    mb: 2, border: '4px solid #fff', boxShadow: '0 0 0 2px #0066A1'
                  }}
                />
                <Typography variant="caption" sx={{ textAlign: 'center', fontWeight: 500, color: 'text.primary' }}>
                  {step}
                </Typography>
              </Box>
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
        Recent Applications
      </Typography>
      <Card>
        <CardContent sx={{ p: 0 }}>
          {applications && Array.isArray(applications) && applications.length > 0 ? (
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E1E7EC', textAlign: 'left' }}>
                    {['ID', 'Age', 'Gender', 'Income', 'Loan Amt', 'Purpose', 'Region', 'Best Model', 'Rate', 'Status'].map(h => (
                      <th key={h} style={{ padding: '12px 16px', fontWeight: 600, color: '#667085' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {applications.slice(0, 10).map((a: any) => {
                    const pred = a.prediction || {};
                    const dec = a.decision;
                    const status = dec?.approved === true ? 'Approved' : dec?.approved === false ? 'Rejected' : 'Pending';
                    const color = status === 'Approved' ? '#27AE60' : status === 'Rejected' ? '#E74C3C' : '#ED8B00';
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
                        <td style={{ padding: '10px 16px' }}>
                          <Chip label={status} size="small" sx={{ bgcolor: color, color: '#fff', fontWeight: 600, fontSize: '0.75rem' }} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Box>
          ) : (
            <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              No applications yet. Process a loan to see data here.
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

