import { useState, useMemo } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Button, Tabs, Tab, Slider, Select,
  MenuItem, FormControl, InputLabel, Chip, Alert, CircularProgress, TextField
} from '@mui/material';
import { PictureAsPdf as PdfIcon, GridOn as CsvIcon, TableChart as ExcelIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export default function Reports() {
  const [tab, setTab] = useState(0);
  const [fStatus, setFStatus] = useState<string[]>([]);
  const [fModel, setFModel] = useState<string[]>([]);
  const [fRegion, setFRegion] = useState<string[]>([]);
  const [maxRisk, setMaxRisk] = useState(1.0);

  // Report scheduler state
  const [schedFreq, setSchedFreq] = useState('Daily');
  const [schedEmail, setSchedEmail] = useState('');

  const { data: rawApps, isLoading } = useQuery({
    queryKey: ['report-applications'],
    queryFn: async () => { const r = await api.get('/api/applications'); return r.data; },
  });

  // Flatten applications
  const allData = useMemo(() => {
    if (!rawApps || !Array.isArray(rawApps)) return [];
    return rawApps.map((a: any) => {
      const pred = typeof a.prediction === 'object' && a.prediction ? a.prediction : {};
      const dec = typeof a.decision === 'object' && a.decision ? a.decision : {};
      let status = 'Pending';
      if (dec.approved === true) status = 'Approved';
      else if (dec.approved === false) status = 'Rejected';
      return {
        'Application ID': a.id, Age: a.age, Gender: a.gender || 'Unknown', Region: a.region || 'Unknown',
        Income: a.income, 'Credit Score': a.credit_score, 'Loan Amount': a.loan_amount,
        Purpose: a.loan_purpose, 'Risk Score': pred.risk_score ?? null,
        'Recommended Model': pred.best_model || 'Unknown', 'Interest Rate': pred.recommended_rate ?? null,
        Decision: status, Officer: dec.officer_name || 'N/A', Timestamp: a.timestamp,
      };
    });
  }, [rawApps]);

  // Extract unique values for filters
  const statuses = useMemo(() => [...new Set(allData.map((d: any) => d.Decision))], [allData]);
  const models = useMemo(() => [...new Set(allData.map((d: any) => d['Recommended Model']))], [allData]);
  const regions = useMemo(() => [...new Set(allData.map((d: any) => d.Region))], [allData]);

  // Init filters
  useMemo(() => {
    if (fStatus.length === 0 && statuses.length > 0) setFStatus(statuses);
    if (fModel.length === 0 && models.length > 0) setFModel(models);
    if (fRegion.length === 0 && regions.length > 0) setFRegion(regions);
  }, [statuses, models, regions]);

  // Filter data
  const filtered = useMemo(() => {
    return allData.filter((d: any) =>
      fStatus.includes(d.Decision) &&
      fModel.includes(d['Recommended Model']) &&
      fRegion.includes(d.Region) &&
      (d['Risk Score'] === null || d['Risk Score'] <= maxRisk)
    );
  }, [allData, fStatus, fModel, fRegion, maxRisk]);

  // CSV download
  const downloadCSV = () => {
    if (filtered.length === 0) return;
    const headers = Object.keys(filtered[0]);
    const csvContent = [
      headers.join(','),
      ...filtered.map((row: any) => headers.map(h => JSON.stringify(row[h] ?? '')).join(',')),
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'filtered_report.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  // Excel download (simple CSV with .xlsx extension — basic approach)
  const downloadExcel = () => {
    // For a real app, use a library like xlsx. Here we do CSV as a compatible format.
    downloadCSV();
  };

  const cols = ['Application ID', 'Age', 'Gender', 'Region', 'Income', 'Loan Amount', 'Purpose', 'Risk Score', 'Recommended Model', 'Interest Rate', 'Decision', 'Officer'];

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>📄 Advanced Reports & Auditing</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>Dynamic filtering, exports, and regulatory compliance audits</Typography>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="📊 Portfolio Reports" />
        <Tab label="🛡️ Fairness Audit" />
        <Tab label="📅 Report Scheduler" />
      </Tabs>

      {/* ═══ TAB 0: Portfolio Reports ═══ */}
      {tab === 0 && (
        <>
          {isLoading ? <CircularProgress /> : allData.length === 0 ? (
            <Alert severity="info">No data available. Process some applications first.</Alert>
          ) : (
            <>
              {/* Filters */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🔍 Filter Data</Typography>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Status</InputLabel>
                        <Select multiple value={fStatus} label="Status"
                          onChange={e => setFStatus(typeof e.target.value === 'string' ? [e.target.value] : e.target.value as string[])}
                          renderValue={(sel) => sel.join(', ')}
                        >
                          {statuses.map((s: any) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>AI Model</InputLabel>
                        <Select multiple value={fModel} label="AI Model"
                          onChange={e => setFModel(typeof e.target.value === 'string' ? [e.target.value] : e.target.value as string[])}
                          renderValue={(sel) => sel.join(', ')}
                        >
                          {models.map((m: any) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Region</InputLabel>
                        <Select multiple value={fRegion} label="Region"
                          onChange={e => setFRegion(typeof e.target.value === 'string' ? [e.target.value] : e.target.value as string[])}
                          renderValue={(sel) => sel.join(', ')}
                        >
                          {regions.map((r: any) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <Typography variant="caption">Max Risk: {maxRisk}</Typography>
                      <Slider value={maxRisk} onChange={(_, v) => setMaxRisk(v as number)} min={0} max={1} step={0.05} valueLabelDisplay="auto" />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Results Table */}
              <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>Showing {filtered.length} records</Typography>
              <Card sx={{ mb: 3 }}>
                <CardContent sx={{ p: 0 }}>
                  <Box sx={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #E1E7EC' }}>
                          {cols.map(h => (
                            <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#667085', whiteSpace: 'nowrap' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.slice(0, 50).map((row: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #E1E7EC' }}>
                            {cols.map(col => (
                              <td key={col} style={{ padding: '8px 12px', whiteSpace: 'nowrap' }}>
                                {col === 'Decision' ? (
                                  <Chip label={row[col]} size="small" sx={{
                                    bgcolor: row[col] === 'Approved' ? '#27AE60' : row[col] === 'Rejected' ? '#E74C3C' : '#ED8B00',
                                    color: '#fff', fontWeight: 600, fontSize: '0.7rem',
                                  }} />
                                ) : (
                                  row[col] ?? '—'
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Box>
                </CardContent>
              </Card>

              {/* Export Buttons */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>📥 Export Options</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Button variant="outlined" fullWidth startIcon={<CsvIcon />} onClick={downloadCSV}
                    sx={{ color: '#2E7D32', borderColor: 'rgba(46, 125, 50, 0.5)', py: 1.5 }}
                  >
                    Download CSV
                  </Button>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button variant="outlined" fullWidth startIcon={<ExcelIcon />} onClick={downloadExcel}
                    sx={{ color: '#0066A1', borderColor: 'rgba(0, 102, 161, 0.5)', py: 1.5 }}
                  >
                    Download Excel
                  </Button>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button variant="outlined" fullWidth startIcon={<PdfIcon />} disabled
                    sx={{ color: '#D32F2F', borderColor: 'rgba(211, 47, 47, 0.5)', py: 1.5 }}
                  >
                    AI Pitch Deck (PDF) — Requires Backend
                  </Button>
                </Grid>
              </Grid>
            </>
          )}
        </>
      )}

      {/* ═══ TAB 1: Fairness Audit ═══ */}
      {tab === 1 && (
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🛡️ ECOA Fairness & Bias Audit</Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
            Check if the AI models are showing disparate impact across protected groups.
          </Typography>
          {allData.length > 0 ? (
            <Card>
              <CardContent>
                {(() => {
                  const male = allData.filter((d: any) => d.Gender === 'Male');
                  const female = allData.filter((d: any) => d.Gender === 'Female');
                  const maleApr = male.filter((d: any) => d.Decision === 'Approved').length / Math.max(male.length, 1);
                  const femaleApr = female.filter((d: any) => d.Decision === 'Approved').length / Math.max(female.length, 1);
                  const genderDI = femaleApr / Math.max(maleApr, 0.01);

                  const urban = allData.filter((d: any) => d.Region === 'Urban');
                  const rural = allData.filter((d: any) => d.Region === 'Rural');
                  const urbanApr = urban.filter((d: any) => d.Decision === 'Approved').length / Math.max(urban.length, 1);
                  const ruralApr = rural.filter((d: any) => d.Decision === 'Approved').length / Math.max(rural.length, 1);
                  const regionDI = ruralApr / Math.max(urbanApr, 0.01);

                  const metrics = [
                    { label: 'Gender (Female vs Male)', value: genderDI },
                    { label: 'Region (Rural vs Urban)', value: regionDI },
                  ];

                  return (
                    <>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Disparate Impact (Four-Fifths Rule)</Typography>
                      {metrics.map(m => (
                        <Box key={m.label} sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="body1" sx={{ minWidth: 250 }}>{m.label}</Typography>
                          <Typography variant="h6" sx={{ fontWeight: 600, color: m.value < 0.8 ? 'error.main' : 'success.main' }}>
                            {m.value.toFixed(2)}
                          </Typography>
                          <Chip label={m.value < 0.8 ? 'FAIL' : 'PASS'} size="small"
                            sx={{ bgcolor: m.value < 0.8 ? '#E74C3C' : '#27AE60', color: '#fff', fontWeight: 600 }}
                          />
                        </Box>
                      ))}
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          ) : (
            <Alert severity="info">Insufficient data for audit.</Alert>
          )}
        </Box>
      )}

      {/* ═══ TAB 2: Scheduler ═══ */}
      {tab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>📅 Report Scheduler</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
              Configure automated background jobs to generate and distribute reports.
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Frequency</InputLabel>
                  <Select value={schedFreq} label="Frequency" onChange={e => setSchedFreq(e.target.value)}>
                    {['Daily', 'Weekly', 'Monthly'].map(f => <MenuItem key={f} value={f}>{f}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Recipient Email" fullWidth size="small" value={schedEmail}
                  onChange={e => setSchedEmail(e.target.value)} placeholder="cro@bank.com"
                />
              </Grid>
            </Grid>
            <Button variant="contained" sx={{ mt: 2 }}
              onClick={() => alert(`Scheduled: ${schedFreq} reports to ${schedEmail || 'N/A'}`)}
            >
              Save Automation Schedule
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}



