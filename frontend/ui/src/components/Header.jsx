import React from 'react';
import { motion } from 'framer-motion';
import { Bell, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// Fix #7: Display the real logged-in user's name from AuthContext
const Header = ({ title = "Dashboard" }) => {
  const { user } = useAuth();
  const displayName = user?.name || user?.email || 'Guest';

  return (
    <motion.header 
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.1, ease: 'easeOut' }}
      className="h-20 w-full flex items-center justify-between px-8"
    >
      <h2 className="text-2xl font-bold tracking-tight text-white">{title}</h2>
      
      <div className="flex items-center gap-4">
        <button className="relative w-10 h-10 rounded-full glass-panel flex items-center justify-center text-white/70 hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
        </button>
        
        <div className="flex items-center gap-3 glass-panel py-1.5 px-3 rounded-full cursor-pointer hover:bg-white/10 transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-indigo-500 p-[1px]">
            <div className="w-full h-full bg-darker rounded-full flex items-center justify-center overflow-hidden">
              <User className="w-4 h-4 text-white/80" />
            </div>
          </div>
          <span className="text-sm font-medium text-white pr-2">{displayName}</span>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;

