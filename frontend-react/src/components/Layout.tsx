import { useState, useEffect } from 'react';
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
  CssBaseline,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Upload as UploadIcon,
  Chat as ChatIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { checkHealth, getStats } from '../services/api';
import type { Stats } from '../types';
import type { ReactNode } from 'react';

const drawerWidth = 280;

interface LayoutProps {
  children: ReactNode;
}

const menuItems = [
  { text: 'Upload Documents', icon: <UploadIcon />, path: '/' },
  { text: 'Q&A', icon: <ChatIcon />, path: '/qa' },
  { text: 'Extract KPIs', icon: <AssessmentIcon />, path: '/kpis' },
  { text: 'Risk Analysis', icon: <WarningIcon />, path: '/risks' },
  { text: 'Investment Memo', icon: <DescriptionIcon />, path: '/memo' },
];

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [stats, setStats] = useState<Stats | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    checkApiStatus();
    loadStats();
    
    // Poll for stats every 30 seconds
    const interval = setInterval(() => {
      loadStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const checkApiStatus = async () => {
    try {
      await checkHealth();
      setApiStatus('connected');
    } catch (error) {
      setApiStatus('disconnected');
    }
  };

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  const drawer = (
    <Box>
      <Toolbar sx={{ bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
          📊 FinanceY
        </Typography>
      </Toolbar>
      <Divider />
      
      {/* API Status */}
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          API Status
        </Typography>
        {apiStatus === 'checking' && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="caption">Checking...</Typography>
          </Box>
        )}
        {apiStatus === 'connected' && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'success.main' }}>
            <CheckCircleIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">Connected</Typography>
          </Box>
        )}
        {apiStatus === 'disconnected' && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'error.main' }}>
            <ErrorIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption">Disconnected</Typography>
          </Box>
        )}
      </Box>
      
      <Divider />
      
      {/* Statistics */}
      {stats && (
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Statistics
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            Documents: <strong>{stats.retriever.num_documents}</strong>
          </Typography>
          <Typography variant="body2">
            Index: <strong>{stats.retriever.index_exists ? '✅' : '❌'}</strong>
          </Typography>
        </Box>
      )}
      
      <Divider />
      
      {/* Navigation */}
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            FinanceY - AI-Powered Financial Analysis
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        {apiStatus === 'disconnected' && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Cannot connect to API. Make sure the backend is running on {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
          </Alert>
        )}
        {children}
      </Box>
    </Box>
  );
}

