import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { MessageSquare, Calendar, Users, LogOut, Shield } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { icon: MessageSquare, label: 'AI Assistant', path: '/dashboard' },
    { icon: Calendar, label: 'Appointments', path: '/appointments' },
    { icon: Users, label: 'Visitor Check-in', path: '/check-in' },
  ];

  // Fix #5: Functional logout — clears token and redirects to login
  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <motion.aside 
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="h-full w-64 glass-panel border-l-0 rounded-l-none rounded-r-3xl flex flex-col pt-8 pb-6 px-4"
    >
      <div className="flex items-center gap-3 px-2 mb-10">
        <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
          <Shield className="w-5 h-5 text-primary" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white">Aura Health</h1>
      </div>

      <nav className="flex-1 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive 
                  ? 'bg-primary/20 text-white border border-primary/30 shadow-[0_0_15px_rgba(19,146,236,0.15)]' 
                  : 'text-white/60 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Fix #5: onClick now calls handleLogout to clear the session */}
      <button
        onClick={handleLogout}
        className="flex items-center gap-3 px-4 py-3 text-red-300 hover:bg-red-500/10 hover:text-red-200 rounded-xl transition-colors mt-auto"
      >
        <LogOut className="w-5 h-5" />
        <span className="font-medium">Sign Out</span>
      </button>
    </motion.aside>
  );
};

export default Sidebar;

