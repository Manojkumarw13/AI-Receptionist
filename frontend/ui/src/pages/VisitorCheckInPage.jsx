import React, { useState } from 'react';
import { UserPlus, Building2, FileText, Camera, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const VisitorCheckInPage = () => {
  const [form, setForm] = useState({ name: '', purpose: '', company: '' });
  const [image, setImage] = useState(null);
  const [status, setStatus] = useState(null); // 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.purpose.trim()) return;

    setStatus('loading');
    setMessage('');

    try {
      const data = new FormData();
      data.append('name', form.name);
      data.append('purpose', form.purpose);
      if (form.company) data.append('company', form.company);
      if (image) data.append('image', image);

      const res = await api.post('/visitors', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setStatus('success');
      setMessage(res.data.message || 'Visitor checked in successfully!');
      setForm({ name: '', purpose: '', company: '' });
      setImage(null);
    } catch (err) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Check-in failed. Please try again.');
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <h2 className="text-xl font-bold text-white mb-6">Visitor Check-In</h2>

      <div className="max-w-lg mx-auto w-full">
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6 space-y-5"
        >
          {/* Name */}
          <div className="relative group">
            <UserPlus className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40 group-focus-within:text-primary transition-colors" />
            <input
              type="text"
              name="name"
              placeholder="Visitor Name *"
              value={form.name}
              onChange={handleChange}
              className="glass-input w-full pl-12"
              required
            />
          </div>

          {/* Purpose */}
          <div className="relative group">
            <FileText className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40 group-focus-within:text-primary transition-colors" />
            <input
              type="text"
              name="purpose"
              placeholder="Purpose of Visit *"
              value={form.purpose}
              onChange={handleChange}
              className="glass-input w-full pl-12"
              required
            />
          </div>

          {/* Company */}
          <div className="relative group">
            <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40 group-focus-within:text-primary transition-colors" />
            <input
              type="text"
              name="company"
              placeholder="Company (optional)"
              value={form.company}
              onChange={handleChange}
              className="glass-input w-full pl-12"
            />
          </div>

          {/* Photo upload */}
          <div className="relative">
            <label className="flex items-center gap-3 glass-input w-full cursor-pointer text-white/50 hover:text-white/70 transition-colors">
              <Camera className="w-5 h-5 shrink-0" />
              <span className="truncate">{image ? image.name : 'Upload photo (optional)'}</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => setImage(e.target.files[0] || null)}
              />
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={status === 'loading'}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {status === 'loading' ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                Check In Visitor
              </>
            )}
          </button>
        </motion.form>

        {/* Feedback */}
        {status === 'success' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 bg-green-500/10 border border-green-500/30 text-green-300 p-3 rounded-xl text-sm"
          >
            <CheckCircle className="w-5 h-5 shrink-0" />
            {message}
          </motion.div>
        )}
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-300 p-3 rounded-xl text-sm"
          >
            <AlertCircle className="w-5 h-5 shrink-0" />
            {message}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default VisitorCheckInPage;
