import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Stethoscope, Loader2, AlertCircle, X, QrCode } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const statusColors = {
  Scheduled: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  Completed: 'text-green-400 bg-green-500/10 border-green-500/30',
  Cancelled: 'text-red-400 bg-red-500/10 border-red-500/30',
  'No-Show': 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
};

const AppointmentsPage = () => {
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

  // FIX #1: Use api.delete() to match the backend DELETE /api/appointments/{id} route.
  // The old code used api.post('/appointments/${id}/cancel') which returned 404/405.
  const cancelAppointment = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      await api.delete(`/appointments/${id}`);
      fetchAppointments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel appointment.');
    }
  };

  // FIX #3: Do NOT append 'Z' to the dateString.
  // The backend stores naive local timestamps (Asia/Kolkata, no tzinfo).
  // Appending 'Z' coerces them to UTC then re-shifts by +05:30, causing
  // a ~5.5-hour display error (e.g. 10:30 AM renders as 04:00 PM).
  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-IN'),
      time: date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    };
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
            {appointments.map((apt, idx) => {
              const { date, time } = formatDateTime(apt.appointment_time);
              return (
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
                      <span>{date}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-white/40 text-xs mt-1">
                      <Clock className="w-3 h-3" />
                      <span>{time}</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 items-end">
                    <span className={`text-xs font-medium px-3 py-1 rounded-full border ${statusColors[apt.status] || 'text-white/50 bg-white/5 border-white/10'}`}>
                      {apt.status}
                    </span>
                    {apt.status === 'Scheduled' && (
                      <div className="flex gap-2">
                        <button className="p-1.5 text-white/40 hover:text-white transition-colors">
                          <QrCode className="w-4 h-4" />
                        </button>
                        <button onClick={() => cancelAppointment(apt.id)} className="p-1.5 text-red-400/60 hover:text-red-400 transition-colors">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default AppointmentsPage;
