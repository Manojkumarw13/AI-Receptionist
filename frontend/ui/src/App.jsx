import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

import ThreeBackground from './components/ThreeBackground';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './layouts/DashboardLayout';
import AiAssistantPage from './pages/AiAssistantPage';
import AppointmentsPage from './pages/AppointmentsPage';
import VisitorCheckInPage from './pages/VisitorCheckInPage';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="relative w-screen h-screen overflow-hidden bg-darker text-white font-sans">
          {/* The 3D Background */}
          <ThreeBackground />
          
          {/* Main Application Routes */}
          <div className="relative z-10 w-full h-full">
            <AnimatePresence mode="wait">
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* Protected Dashboard Layout */}
                <Route element={<DashboardLayout />}>
                  <Route path="/dashboard" element={<AiAssistantPage />} />
                  <Route path="/appointments" element={<AppointmentsPage />} />
                  <Route path="/check-in" element={<VisitorCheckInPage />} />
                </Route>

                {/* Default redirect */}
                <Route path="*" element={<Navigate to="/login" replace />} />
              </Routes>
            </AnimatePresence>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

