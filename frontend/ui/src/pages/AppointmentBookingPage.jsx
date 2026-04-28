import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope, Calendar, Clock, User, ChevronLeft,
  Loader2, CheckCircle, AlertCircle, Search
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

// BUG-13 FIX: Full manual appointment booking form (in addition to AI chat)

const HOURS = Array.from({ length: 8 }, (_, i) => i + 9); // 9 AM – 4 PM (last slot at 16:30)
const MINUTES = [0, 30];

const AppointmentBookingPage = () => {
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState([]);
  const [diseases, setDiseases] = useState([]);
  const [specialties, setSpecialties] = useState([]);

  const [form, setForm] = useState({
    doctor_name: '',
    disease: '',
    appointment_year: '',
    appointment_month: '',
    appointment_day: '',
    appointment_hour: 9,
    appointment_minute: 0,
  });

  const [doctorSearch, setDoctorSearch] = useState('');
  const [selectedSpecialty, setSelectedSpecialty] = useState('');
  const [status, setStatus] = useState(null); // 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('');
  const [loadingDoctors, setLoadingDoctors] = useState(true);

  // Set default date to tomorrow
  useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setForm(prev => ({
      ...prev,
      appointment_year: tomorrow.getFullYear(),
      appointment_month: tomorrow.getMonth() + 1,
      appointment_day: tomorrow.getDate(),
    }));
  }, []);

  // Fetch doctors and specialties
  useEffect(() => {
    Promise.all([
      api.get('/doctors'),
      api.get('/doctors/specialties'),
    ]).then(([docRes, specRes]) => {
      setDoctors(docRes.data);
      setSpecialties(specRes.data);
      // Derive unique disease list from doctor specialties (simplified)
      setDiseases([]);
    }).catch(console.error)
      .finally(() => setLoadingDoctors(false));
  }, []);

  const filteredDoctors = doctors.filter(d => {
    const matchesSearch = d.name.toLowerCase().includes(doctorSearch.toLowerCase());
    const matchesSpecialty = !selectedSpecialty || d.specialty === selectedSpecialty;
    return matchesSearch && matchesSpecialty;
  });

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleDateChange = (e) => {
    const date = new Date(e.target.value);
    if (!isNaN(date)) {
      setForm(prev => ({
        ...prev,
        appointment_year: date.getFullYear(),
        appointment_month: date.getMonth() + 1,
        appointment_day: date.getDate(),
      }));
    }
  };

  const getDateValue = () => {
    if (!form.appointment_year) return '';
    const y = form.appointment_year;
    const m = String(form.appointment_month).padStart(2, '0');
    const d = String(form.appointment_day).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  const getTodayString = () => {
    const d = new Date();
    return d.toISOString().split('T')[0];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.doctor_name || !form.disease) {
      setStatus('error');
      setMessage('Please select a doctor and enter a disease/condition.');
      return;
    }

    setStatus('loading');
    setMessage('');

    try {
      const res = await api.post('/appointments', {
        doctor_name: form.doctor_name,
        disease: form.disease,
        appointment_year: Number(form.appointment_year),
        appointment_month: Number(form.appointment_month),
        appointment_day: Number(form.appointment_day),
        appointment_hour: Number(form.appointment_hour),
        appointment_minute: Number(form.appointment_minute),
      });

      setStatus('success');
      setMessage(`Appointment booked successfully! ID: ${res.data.appointment_id}`);
      setTimeout(() => navigate('/appointments'), 2000);
    } catch (err) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Booking failed. Please try again.');
    }
  };

  return (
    <div className="h-full flex flex-col overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6 shrink-0">
        <button
          onClick={() => navigate('/appointments')}
          className="p-2 glass-panel hover:bg-white/10 transition-colors rounded-xl"
        >
          <ChevronLeft className="w-5 h-5 text-white" />
        </button>
        <h2 className="text-xl font-bold text-white">Book New Appointment</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Doctor Selection */}
        <div className="glass-panel p-5 flex flex-col gap-4">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Stethoscope className="w-4 h-4 text-primary" /> Select Doctor
          </h3>

          {/* Specialty Filter */}
          <select
            value={selectedSpecialty}
            onChange={e => setSelectedSpecialty(e.target.value)}
            className="glass-input w-full text-white bg-transparent"
          >
            <option value="" className="bg-slate-900">All Specialties</option>
            {specialties.map(s => (
              <option key={s} value={s} className="bg-slate-900">{s}</option>
            ))}
          </select>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
            <input
              type="text"
              placeholder="Search doctor name..."
              value={doctorSearch}
              onChange={e => setDoctorSearch(e.target.value)}
              className="glass-input w-full pl-10"
            />
          </div>

          {/* Doctor List */}
          <div className="flex-1 overflow-y-auto space-y-2 max-h-64 scrollbar-hide">
            {loadingDoctors ? (
              <div className="flex justify-center py-4">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              </div>
            ) : filteredDoctors.length === 0 ? (
              <p className="text-white/40 text-center py-4 text-sm">No doctors found.</p>
            ) : (
              filteredDoctors.map(doc => (
                <button
                  key={doc.id}
                  type="button"
                  onClick={() => handleChange('doctor_name', doc.name)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    form.doctor_name === doc.name
                      ? 'bg-primary/20 border-primary/50 text-white'
                      : 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <p className="font-medium text-sm">{doc.name}</p>
                  <p className="text-xs opacity-60 mt-0.5">{doc.specialty}</p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right: Appointment Details */}
        <form onSubmit={handleSubmit} className="glass-panel p-5 flex flex-col gap-4">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary" /> Appointment Details
          </h3>

          {/* Selected Doctor Display */}
          {form.doctor_name && (
            <div className="bg-primary/10 border border-primary/30 rounded-xl px-4 py-2.5 text-primary text-sm flex items-center gap-2">
              <User className="w-4 h-4 shrink-0" />
              <span>{form.doctor_name}</span>
            </div>
          )}

          {/* Disease / Condition */}
          <div>
            <label className="text-white/60 text-xs mb-1 block">Disease / Condition *</label>
            <input
              type="text"
              placeholder="e.g. Migraine, Diabetes, Arthritis..."
              value={form.disease}
              onChange={e => handleChange('disease', e.target.value)}
              className="glass-input w-full"
              required
            />
          </div>

          {/* Date */}
          <div>
            <label className="text-white/60 text-xs mb-1 block flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Date *
            </label>
            <input
              type="date"
              value={getDateValue()}
              min={getTodayString()}
              onChange={handleDateChange}
              className="glass-input w-full text-white [color-scheme:dark]"
              required
            />
          </div>

          {/* Time */}
          <div>
            <label className="text-white/60 text-xs mb-1 block flex items-center gap-1">
              <Clock className="w-3 h-3" /> Time * (Working hours: 9:00 AM – 5:00 PM)
            </label>
            <div className="grid grid-cols-2 gap-3">
              <select
                value={form.appointment_hour}
                onChange={e => handleChange('appointment_hour', Number(e.target.value))}
                className="glass-input w-full text-white bg-transparent"
              >
                {HOURS.map(h => (
                  <option key={h} value={h} className="bg-slate-900">
                    {String(h).padStart(2, '0')}:00
                  </option>
                ))}
              </select>
              <select
                value={form.appointment_minute}
                onChange={e => handleChange('appointment_minute', Number(e.target.value))}
                className="glass-input w-full text-white bg-transparent"
              >
                {MINUTES.map(m => (
                  <option key={m} value={m} className="bg-slate-900">
                    :{String(m).padStart(2, '0')}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Feedback */}
          <AnimatePresence>
            {status === 'success' && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 text-green-300 p-3 rounded-xl text-sm"
              >
                <CheckCircle className="w-4 h-4 shrink-0" />
                {message}
              </motion.div>
            )}
            {status === 'error' && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-300 p-3 rounded-xl text-sm"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                {message}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submit */}
          <button
            type="submit"
            disabled={status === 'loading' || !form.doctor_name}
            className="btn-primary w-full flex items-center justify-center gap-2 mt-auto"
          >
            {status === 'loading' ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                Confirm Booking
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AppointmentBookingPage;
