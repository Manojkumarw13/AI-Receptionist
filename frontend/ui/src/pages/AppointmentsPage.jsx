import React, { useState, useEffect } from 'react';
import { Calendar, Clock, User, Stethoscope, Loader2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const statusColors = {
  Scheduled: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  Completed: 'text-green-400 bg-green-500/10 border-green-500/30',
  Cancelled: 'text-red-400 bg-red-500/10 border-red-500/30',
  'No-Show': 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
};

const AppointmentsPage = () => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/appointments');
      setAppointments(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load appointments.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 text-red-300">
        <AlertCircle className="w-10 h-10" />
        <p>{error}</p>
        <button onClick={fetchAppointments} className="btn-primary px-4 py-2 text-sm">Retry</button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">My Appointments</h2>
        <span className="text-white/40 text-sm">{appointments.length} total</span>
      </div>

      {appointments.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-white/40 gap-3">
          <Calendar className="w-12 h-12" />
          <p>No appointments found. Use the AI Assistant to book one!</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-hide">
          <AnimatePresence>
            {appointments.map((apt, idx) => (
              <motion.div
                key={apt.id || idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="glass-panel p-4 flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                  <Stethoscope className="w-5 h-5 text-primary" />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">{apt.doctor_name}</p>
                  <p className="text-white/50 text-sm truncate">{apt.disease}</p>
                </div>

                <div className="text-right shrink-0">
                  <div className="flex items-center gap-1.5 text-white/60 text-sm">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(apt.appointment_time).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-white/40 text-xs mt-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(apt.appointment_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>

                <span className={`text-xs font-medium px-3 py-1 rounded-full border ${statusColors[apt.status] || 'text-white/50 bg-white/5 border-white/10'}`}>
                  {apt.status}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default AppointmentsPage;
