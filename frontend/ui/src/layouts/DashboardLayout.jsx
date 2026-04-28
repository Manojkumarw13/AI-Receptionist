import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// BUG-05 FIX: Auth guard — redirect unauthenticated users to /login
const DashboardLayout = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-darker">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-full w-full relative z-20 pointer-events-auto p-4 gap-4">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        
        <motion.main 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="flex-1 glass-panel overflow-hidden mt-4 mr-4 p-6"
        >
          {/* This renders the child routes (e.g., AiAssistantPage) */}
          <Outlet />
        </motion.main>
      </div>
    </div>
  );
};

export default DashboardLayout;

