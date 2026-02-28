import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { chatService } from '../services/api';

const INITIAL_MESSAGE = { id: 1, role: 'assistant', content: 'Hello! I am Aura, your AI Receptionist. How can I help you today? I can book appointments, check in visitors, or find available doctors.' };

const AiAssistantPage = () => {
  // Fix #4: Restore messages from sessionStorage so chat survives page refresh
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem('aura_chat');
      return saved ? JSON.parse(saved) : [INITIAL_MESSAGE];
    } catch {
      return [INITIAL_MESSAGE];
    }
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fix #4: Persist messages to sessionStorage whenever they change
  useEffect(() => {
    sessionStorage.setItem('aura_chat', JSON.stringify(messages));
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      // Map existing messages to the format expected by the backend
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      
      const response = await chatService.sendMessage(userMsg, history);
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: response.reply 
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: 'Sorry, I encountered a communication error with the backend. Please ensure you are logged in.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col relative w-full overflow-hidden rounded-xl">
      
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto mb-4 scrollbar-hide pr-4 space-y-6">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-10 h-10 shrink-0 rounded-full flex items-center justify-center shadow-lg ${
                msg.role === 'assistant' 
                  ? 'bg-gradient-to-br from-primary to-indigo-600 border border-indigo-400/30' 
                  : 'bg-white/10 backdrop-blur-md border border-white/20'
              }`}>
                {msg.role === 'assistant' ? <Bot className="w-5 h-5 text-white" /> : <User className="w-5 h-5 text-white/80" />}
              </div>

              {/* Message Bubble */}
              <div className={`p-4 rounded-2xl ${
                msg.role === 'assistant'
                  ? 'bg-white/5 border border-white/10 text-white shadow-[0_4px_30px_rgba(0,0,0,0.1)] backdrop-blur-md rounded-tl-none'
                  : 'bg-primary/20 border border-primary/30 text-white shadow-[0_0_15px_rgba(19,146,236,0.1)] rounded-tr-none'
              }`}>
                <p className="leading-relaxed text-[15px]">{msg.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-4 max-w-3xl"
          >
            <div className="w-10 h-10 shrink-0 rounded-full flex items-center justify-center bg-gradient-to-br from-primary to-indigo-600 border border-indigo-400/30 shadow-lg">
               <Loader2 className="w-5 h-5 text-white animate-spin" />
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-white/60 backdrop-blur-md rounded-tl-none flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-primary animate-bounce delay-75" />
              <span className="w-2 h-2 rounded-full bg-primary animate-bounce delay-150" />
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-auto relative group shrink-0">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message to Aura..."
            className="w-full glass-input pr-16 py-4 shadow-[0_0_20px_rgba(0,0,0,0.2)] focus:shadow-[0_0_30px_rgba(19,146,236,0.2)]"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2.5 rounded-xl bg-primary hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 shadow-lg shadow-primary/20"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <div className="text-center mt-3 text-xs text-white/40">
          Aura AI can make mistakes. Verify important appointments.
        </div>
      </div>

    </div>
  );
};

export default AiAssistantPage;
