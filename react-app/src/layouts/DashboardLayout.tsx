import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Badge,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  MonetizationOn as LoansIcon,
  BarChart as AnalyticsIcon,
  ModelTraining as TrainingIcon,
  Gavel as FairnessIcon,
  CompareArrows as ABTestingIcon,
  Science as SimulatorIcon,
  SmartToy as AssistantIcon,
  Description as ReportsIcon,
  Settings as SettingsIcon,
  People as UsersIcon,
  Notifications as NotificationsIcon,
  AdminPanelSettings as RolesIcon,
} from '@mui/icons-material';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Loan Processing', icon: <LoansIcon />, path: '/loans' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Model Training', icon: <TrainingIcon />, path: '/training' },
  { text: 'A/B Testing', icon: <ABTestingIcon />, path: '/ab-testing' },
  { text: 'What-If Simulator', icon: <SimulatorIcon />, path: '/simulator' },
  { text: 'Ollama Assistant', icon: <AssistantIcon />, path: '/assistant' },
  { text: 'Reports', icon: <ReportsIcon />, path: '/reports' },
  { text: 'Fairness Report', icon: <FairnessIcon />, path: '/fairness' },
];

const adminItems = [
  { text: 'Users & Roles', icon: <UsersIcon />, path: '/admin/users' },
  { text: 'Model Registry', icon: <RolesIcon />, path: '/admin/models' },
  { text: 'System Settings', icon: <SettingsIcon />, path: '/admin/settings' },
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${drawerWidth}px)`,
          ml: `${drawerWidth}px`,
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: 'none',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'Dashboard'}
          </Typography>
          <IconButton size="large" aria-label="show new notifications" color="inherit">
            <Badge badgeContent={4} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          <Box sx={{ ml: 2, display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={handleMenu}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32, fontSize: '0.875rem' }}>LO</Avatar>
            <Typography variant="body2" sx={{ ml: 1, fontWeight: 500 }}>
              User ▾
            </Typography>
          </Box>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            keepMounted
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={handleClose}>Profile</MenuItem>
            <MenuItem onClick={handleClose}>My account</MenuItem>
            <MenuItem onClick={handleClose}>Logout</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            backgroundColor: 'primary.navy', // Requires extension or just use a hex code
            color: '#fff', // We will set custom styling for sidebar
          },
        }}
        variant="permanent"
        anchor="left"
        PaperProps={{
          sx: {
            backgroundColor: '#173F5F', // Navy from design spec
            color: '#FFFFFF',
          }
        }}
      >
        <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: 1, color: '#FFFFFF' }}>
            MIFOS <span style={{ color: '#78BE20' }}>AI</span>
          </Typography>
        </Toolbar>
        <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
        <List sx={{ pt: 2, pb: 2, flexGrow: 1 }}>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderLeft: '4px solid #78BE20',
                  },
                  '&.Mui-selected:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  },
                  pl: location.pathname === item.path ? 2.5 : 3,
                }}
              >
                <ListItemIcon sx={{ color: location.pathname === item.path ? '#78BE20' : '#98A2B3', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{ 
                    fontSize: '0.9rem',
                    fontWeight: location.pathname === item.path ? 600 : 400,
                    color: location.pathname === item.path ? '#FFFFFF' : '#98A2B3'
                  }} 
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
        <List>
          <ListItem disablePadding>
            <ListItemText 
              primary="Administration" 
              primaryTypographyProps={{ fontSize: '0.75rem', fontWeight: 600, color: '#98A2B3', textTransform: 'uppercase', px: 3, py: 1 }} 
            />
          </ListItem>
          {adminItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderLeft: '4px solid #78BE20',
                  },
                  pl: location.pathname === item.path ? 2.5 : 3,
                }}
              >
                <ListItemIcon sx={{ color: location.pathname === item.path ? '#78BE20' : '#98A2B3', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{ 
                    fontSize: '0.85rem',
                    color: location.pathname === item.path ? '#FFFFFF' : '#98A2B3'
                  }} 
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <Box sx={{ p: 3, display: 'flex', alignItems: 'center' }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#78BE20', mr: 2 }} />
          <Typography variant="caption" sx={{ color: '#98A2B3' }}>
            System Status ● Operational
          </Typography>
        </Box>
      </Drawer>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, backgroundColor: 'background.default', minHeight: '100vh', pt: 10 }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}


