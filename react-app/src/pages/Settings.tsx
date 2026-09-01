import { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Button, Select, MenuItem,
  FormControl, InputLabel, Alert, CircularProgress, } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const ROLE = 'Administrator';

export default function Settings() {
  const [selectedModel, setSelectedModel] = useState('gemma2:2b');
  const [selectedTheme, setSelectedTheme] = useState('light');
  const [availableModels, setAvailableModels] = useState<string[]>(['gemma2:2b', 'qwen', 'mistral', 'deepseek', 'phi']);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  // Fetch current settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings-page'],
    queryFn: async () => { const r = await api.get(`/api/settings/${ROLE}`); return r.data; },
  });

  useEffect(() => {
    if (settings) {
      setSelectedModel(settings.ollama_model || 'gemma2:2b');
      setSelectedTheme(settings.theme || 'light');
    }
  }, [settings]);

  // Auto-detect Ollama models
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(3000) });
        if (r.ok) {
          const data = await r.json();
          const models = (data.models || []).map((m: any) => m.name);
          if (models.length > 0) {
            setAvailableModels([...new Set([...models, 'gemma2:2b', 'qwen', 'mistral', 'deepseek', 'phi'])]);
            if (!models.includes(selectedModel)) setSelectedModel(models[0]);
          }
          setOllamaStatus('connected');
        } else {
          setOllamaStatus('disconnected');
        }
      } catch {
        setOllamaStatus('disconnected');
      }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      await api.post('/api/settings', { user_role: ROLE, ollama_model: selectedModel, theme: selectedTheme });
      setSaveMsg('Settings saved successfully!');
    } catch {
      setSaveMsg('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>⚙️ Platform Settings</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>Configure LLM models, themes, and view system status</Typography>
      </Box>

      <Grid container spacing={4}>
        {/* LLM Config */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>🦙 LLM Configuration</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                Select the local model used for Explainability and the AI Banking Assistant.
              </Typography>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>Active AI Model</InputLabel>
                <Select value={selectedModel} label="Active AI Model" onChange={e => setSelectedModel(e.target.value)}>
                  {availableModels.map((m: any) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
                </Select>
              </FormControl>

              <Alert severity={ollamaStatus === 'connected' ? 'success' : 'warning'} sx={{ mb: 2 }}>
                Ollama Status: <b>{ollamaStatus === 'connected' ? 'Connected ✅' : ollamaStatus === 'checking' ? 'Checking...' : 'Not Running ❌'}</b>
                {ollamaStatus === 'connected' && ` — ${availableModels.length} models available`}
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Theme */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>🎨 Interface Theme</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
                Choose the UI color scheme.
              </Typography>

              <FormControl fullWidth size="small" sx={{ mb: 3 }}>
                <InputLabel>UI Theme</InputLabel>
                <Select value={selectedTheme} label="UI Theme" onChange={e => setSelectedTheme(e.target.value)}>
                  {['light', 'dark', 'system'].map(t => <MenuItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</MenuItem>)}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Save */}
      <Box sx={{ mt: 3, mb: 4 }}>
        <Button variant="contained" size="large" onClick={handleSave} disabled={saving}
          startIcon={saving ? <CircularProgress size={18} color="inherit" /> : null}
          sx={{ fontWeight: 600, py: 1.5, px: 4 }}
        >
          💾 Save Settings
        </Button>
        {saveMsg && <Alert severity={saveMsg.includes('success') ? 'success' : 'error'} sx={{ mt: 2 }}>{saveMsg}</Alert>}
      </Box>

      {/* System Status */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🏥 System Status</Typography>
          <Grid container spacing={2}>
            {[
              { name: 'FastAPI Backend', status: 'Running', color: '#27AE60' },
              { name: 'ChromaDB Vector Store', status: 'Ready', color: '#27AE60' },
              { name: 'SQLite Database', status: 'Connected', color: '#27AE60' },
              { name: 'Ollama LLM', status: ollamaStatus === 'connected' ? 'Connected' : 'Disconnected', color: ollamaStatus === 'connected' ? '#27AE60' : '#E74C3C' },
            ].map(s => (
              <Grid item xs={6} md={3} key={s.name}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: s.color }} />
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{s.name}</Typography>
                    <Typography variant="caption" sx={{ color: s.color }}>{s.status}</Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}



