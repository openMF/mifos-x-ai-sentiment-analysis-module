import { Box, Card, CardContent, Typography, LinearProgress, Stack, CircularProgress } from '@mui/material';
import { CheckCircle as CheckCircleIcon, Warning as WarningIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export default function Fairness() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['fairness'],
    queryFn: async () => {
      const response = await api.get('/api/analytics/fairness-audit');
      return response.data;
    }
  });

  if (isLoading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  if (error || !data) {
    return <Typography color="error">Error loading fairness data.</Typography>;
  }

  const overallStatus = data.overall_status;
  
  const metrics = [
    {
      category: 'Disparate Impact',
      items: [
        { name: 'Gender', value: data.disparate_impact?.gender, pass: data.disparate_impact?.gender >= 0.8 },
        { name: 'Region', value: data.disparate_impact?.region, pass: data.disparate_impact?.region >= 0.8 },
      ]
    },
    {
      category: 'Equal Opportunity Difference',
      items: [
        { name: 'Gender', value: data.equal_opportunity_difference?.gender, pass: Math.abs(data.equal_opportunity_difference?.gender) <= 0.2 },
        { name: 'Region', value: data.equal_opportunity_difference?.region, pass: Math.abs(data.equal_opportunity_difference?.region) <= 0.2 },
      ]
    }
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
          Fairness Monitor
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Compliance and bias tracking for the RL Model
        </Typography>
      </Box>

      <Card sx={{ mb: 4, border: overallStatus === 'PASS' ? '1px solid #78BE20' : '1px solid #D32F2F' }}>
        <CardContent sx={{ p: 3, display: 'flex', alignItems: 'center' }}>
          {overallStatus === 'PASS' ? (
            <CheckCircleIcon sx={{ color: 'secondary.main', fontSize: 40, mr: 2 }} />
          ) : (
            <WarningIcon sx={{ color: 'error.main', fontSize: 40, mr: 2 }} />
          )}
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Overall Status: {overallStatus}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              All fairness metrics are currently above the minimum acceptable threshold (0.80).
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <Stack spacing={4}>
        {metrics.map((section) => (
          <Card key={section.category}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                {section.category}
              </Typography>
              
              {section.items.map((item) => (
                <Box key={item.name} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {item.name}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body1" sx={{ fontWeight: 600, mr: 1, color: item.pass ? 'text.primary' : 'error.main' }}>
                        {item.value}
                      </Typography>
                      {item.pass ? <CheckCircleIcon color="success" fontSize="small" /> : <WarningIcon color="error" fontSize="small" />}
                    </Box>
                  </Box>
                  
                  <Box sx={{ position: 'relative', width: '100%', mb: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={item.value * 100 > 100 ? 100 : item.value * 100} 
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        bgcolor: 'background.default',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: item.pass ? 'primary.main' : 'error.main',
                        }
                      }} 
                    />
                    {/* Threshold Marker */}
                    <Box 
                      sx={{ 
                        position: 'absolute', 
                        top: -4, 
                        bottom: -4, 
                        left: '80%', 
                        width: 2, 
                        bgcolor: 'error.main',
                        zIndex: 1
                      }} 
                    />
                  </Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', justifyContent: 'flex-end', pr: '20%' }}>
                    ↑ Minimum threshold (0.80)
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}

