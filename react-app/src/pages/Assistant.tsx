import { useState, useEffect, useRef } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Avatar, Stack, Chip,
  List, ListItemButton, ListItemText, Divider, CircularProgress, IconButton
} from '@mui/material';
import {
  Send as SendIcon, SmartToy as AiIcon, Person as UserIcon,
  Add as AddIcon, Delete as DeleteIcon
} from '@mui/icons-material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const OLLAMA_URL = 'http://localhost:11434/api/generate';
const ROLE = 'Administrator'; // Default role

const quickActions = [
  { label: 'Explain Prediction', prompt: 'Explain the most recent RL prediction in detail.' },
  { label: 'Compare PPO vs SAC', prompt: 'Compare the PPO and SAC algorithms in our banking environment.' },
  { label: 'System Architecture', prompt: 'Explain the system architecture.' },
  { label: 'Risk Analysis', prompt: 'What factors are driving the current risk score?' },
];

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Assistant() {
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [streaming, setStreaming] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Conversations list
  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => { const r = await api.get(`/api/chat/conversations?user_role=${ROLE}`); return r.data; },
  });

  // Latest application context
  const { data: latestApp } = useQuery({
    queryKey: ['latest-app'],
    queryFn: async () => {
      const r = await api.get('/api/applications');
      const apps = r.data;
      return Array.isArray(apps) && apps.length > 0 ? apps[0] : null;
    },
  });

  // Fetch settings
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => { const r = await api.get(`/api/settings/${ROLE}`); return r.data; },
  });

  const ollamaModel = settings?.ollama_model || 'gemma2:2b';

  // Load messages when conversation changes
  useEffect(() => {
    if (!activeConvId) return;
    (async () => {
      try {
        const r = await api.get(`/api/chat/messages/${activeConvId}`);
        setMessages(Array.isArray(r.data) ? r.data.map((m: any) => ({ role: m.role, content: m.content })) : []);
      } catch { setMessages([]); }
    })();
  }, [activeConvId]);

  // Auto-select first conversation
  useEffect(() => {
    if (!activeConvId && conversations && Array.isArray(conversations) && conversations.length > 0) {
      setActiveConvId(conversations[0].id);
    }
  }, [conversations, activeConvId]);

  // Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleNewChat = async () => {
    try {
      const r = await api.post('/api/chat/conversations', { title: 'New Chat', user_role: ROLE });
      setActiveConvId(r.data.id);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    } catch { /* ignore */ }
  };

  const handleDeleteChat = async (convId: number) => {
    try {
      await api.delete(`/api/chat/conversations/${convId}`);
      if (activeConvId === convId) { setActiveConvId(null); setMessages([]); }
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    } catch { /* ignore */ }
  };

  const handleSend = async (promptOverride?: string) => {
    const text = promptOverride || input.trim();
    if (!text || streaming) return;
    setInput('');

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev: any) => [...prev, userMsg]);

    // Save user message to DB
    if (activeConvId) {
      try { await api.post(`/api/chat/messages/${activeConvId}`, { role: 'user', content: text }); } catch {}
    }

    // Build system prompt
    let sysMsg = 'You are a technical AI Administrator for a banking platform. Answer with critical depth about RL algorithms, FastAPI, and system architecture.';
    if (latestApp) {
      sysMsg += `\n\nCURRENT APPLICANT CONTEXT:\n${JSON.stringify(latestApp, null, 2)}\nAnalyze this context in your response.`;
    }
    const fullPrompt = `${sysMsg}\n\nUser: ${text}\nAssistant:`;

    // Stream from Ollama
    setStreaming(true);
    const assistantMsg: Message = { role: 'assistant', content: '' };
    setMessages((prev: any) => [...prev, assistantMsg]);

    try {
      const response = await fetch(OLLAMA_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: ollamaModel, prompt: fullPrompt, stream: true }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Ollama not available');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.response) {
              fullText += parsed.response;
              setMessages((prev: any) => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: fullText };
                return updated;
              });
            }
          } catch { /* skip */ }
        }
      }

      // Save assistant message to DB
      if (activeConvId && fullText) {
        try { await api.post(`/api/chat/messages/${activeConvId}`, { role: 'assistant', content: fullText }); } catch {}
      }
    } catch {
      const fallback = `[FALLBACK] Unable to connect to local AI engine (port 11434). Model: ${ollamaModel}. Make sure Ollama is running.`;
      setMessages((prev: any) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: 'assistant', content: fallback };
        return updated;
      });
      if (activeConvId) {
        try { await api.post(`/api/chat/messages/${activeConvId}`, { role: 'assistant', content: fallback }); } catch {}
      }
    } finally {
      setStreaming(false);
    }
  };

  const pred = latestApp?.prediction || {};

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }} className="fade-in">
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>💬 Copilot Workspace</Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>AI-powered assistant with live applicant context — Model: {ollamaModel}</Typography>
      </Box>

      <Box sx={{ display: 'flex', flexGrow: 1, gap: 2, overflow: 'hidden' }}>
        {/* Left Sidebar: Conversations */}
        <Card sx={{ width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ pb: 1 }}>
            <Button fullWidth variant="contained" size="small" startIcon={<AddIcon />} onClick={handleNewChat} sx={{ mb: 1 }}>
              New Chat
            </Button>
          </CardContent>
          <Divider />
          <List sx={{ flexGrow: 1, overflowY: 'auto', py: 0 }}>
            {conversations && Array.isArray(conversations) && conversations.map((c: any) => (
              <ListItemButton key={c.id} selected={activeConvId === c.id} onClick={() => setActiveConvId(c.id)}
                sx={{ py: 1, '&.Mui-selected': { bgcolor: 'primary.light' } }}
              >
                <ListItemText primary={c.title} primaryTypographyProps={{ fontSize: '0.85rem', noWrap: true }} />
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleDeleteChat(c.id); }}>
                  <DeleteIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                </IconButton>
              </ListItemButton>
            ))}
          </List>
        </Card>

        {/* Center: Chat */}
        <Card sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Box sx={{ flexGrow: 1, p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {messages.length === 0 && (
              <Typography variant="body1" sx={{ color: 'text.secondary', textAlign: 'center', mt: 4 }}>
                Start a conversation below, or use a quick action.
              </Typography>
            )}
            {messages.map((msg: any, i: number) => (
              <Box key={i} sx={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                {msg.role === 'assistant' && (
                  <Avatar sx={{ bgcolor: 'primary.light', color: 'primary.main', mr: 1.5, width: 32, height: 32 }}><AiIcon fontSize="small" /></Avatar>
                )}
                <Box sx={{
                  maxWidth: '75%', bgcolor: msg.role === 'user' ? 'primary.main' : 'background.default',
                  color: msg.role === 'user' ? '#fff' : 'text.primary',
                  p: 2, borderRadius: 2, border: msg.role === 'assistant' ? '1px solid' : 'none', borderColor: 'divider',
                }}>
                  {msg.role === 'assistant' && <Typography variant="caption" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5, display: 'block' }}>AI ANALYSIS</Typography>}
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{msg.content || (streaming && i === messages.length - 1 ? '...' : '')}</Typography>
                </Box>
                {msg.role === 'user' && (
                  <Avatar sx={{ bgcolor: 'secondary.main', ml: 1.5, width: 32, height: 32 }}><UserIcon fontSize="small" /></Avatar>
                )}
              </Box>
            ))}
            <div ref={chatEndRef} />
          </Box>

          <Box sx={{ p: 2, bgcolor: 'background.default', borderTop: '1px solid', borderColor: 'divider' }}>
            <Stack direction="row" spacing={1} sx={{ mb: 1.5, overflowX: 'auto', pb: 0.5 }}>
              {quickActions.map(qa => (
                <Chip key={qa.label} label={qa.label} onClick={() => handleSend(qa.prompt)} size="small"
                  sx={{ cursor: 'pointer', bgcolor: 'primary.light', color: 'primary.dark', '&:hover': { bgcolor: 'primary.main', color: '#fff' } }}
                />
              ))}
            </Stack>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField fullWidth variant="outlined" size="small" placeholder="Ask the AI Assistant..."
                value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                disabled={streaming}
              />
              <Button variant="contained" onClick={() => handleSend()} disabled={!input.trim() || streaming} sx={{ px: 3 }}>
                {streaming ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              </Button>
            </Box>
          </Box>
        </Card>

        {/* Right: Context */}
        <Card sx={{ width: 250, flexShrink: 0, overflow: 'auto' }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>📋 Live Context</Typography>
            {latestApp ? (
              <>
                <Typography variant="body2" sx={{ mb: 1 }}><b>App ID:</b> {latestApp.id}</Typography>
                <Typography variant="body2" sx={{ mb: 1 }}><b>Income:</b> ${latestApp.income}</Typography>
                <Typography variant="body2" sx={{ mb: 1 }}><b>Debt:</b> ${latestApp.existing_debt}</Typography>
                <Typography variant="body2" sx={{ mb: 1 }}><b>Score:</b> {latestApp.credit_score}</Typography>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>RL Output</Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}><b>Rate:</b> {pred.recommended_rate ?? 'N/A'}%</Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}><b>Risk:</b> {pred.risk_score ?? 'N/A'}</Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}><b>Engine:</b> {pred.best_model ?? 'N/A'}</Typography>
              </>
            ) : (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>No live applicant context available.</Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}



