import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { motion } from 'framer-motion';

const DashboardLayout = () => {
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
