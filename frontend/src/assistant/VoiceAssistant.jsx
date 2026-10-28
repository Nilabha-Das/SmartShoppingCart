import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, Send, RefreshCw, AlertTriangle } from 'lucide-react';
import { AudioWaveform } from './AudioWaveform';
import { useCart } from '../../context/CartContext';

export const VoiceAssistant = ({ onSelectProductForNavigation }) => {
  const [assistantState, setAssistantState] = useState('IDLE'); // IDLE, LISTENING, PROCESSING, RESPONDING, ERROR
  const [transcript, setTranscript] = useState('');
  const [responseMessage, setResponseMessage] = useState(
    "Hello! Welcome to Smart Shopping Cart. Tell me what you're looking for, and I'll help you find products, add items, and navigate aisles."
  );
  const [textInput, setTextInput] = useState('');
  const { addToCart } = useCart();
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Initialize Web Speech API if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => setAssistantState('LISTENING');
      recognition.onresult = (event) => {
        const current = event.resultIndex;
        const text = event.results[current][0].transcript;
        setTranscript(text);
      };
      recognition.onerror = () => {
        setAssistantState('ERROR');
        setResponseMessage('Microphone error or permission denied. Please use text input.');
      };
      recognition.onend = () => {
        if (assistantState === 'LISTENING') {
          processUserQuery(transcript);
        }
      };
      recognitionRef.current = recognition;
    }
  }, [transcript]);

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  const processUserQuery = async (queryText) => {
    if (!queryText.trim()) return;
    setAssistantState('PROCESSING');

    setTimeout(() => {
      let reply = `I processed your request for "${queryText}".`;
      const lower = queryText.toLowerCase();

      if (lower.includes('milk') || lower.includes('organic')) {
        reply = "I found 3 organic milk products. Showing options below.";
      } else if (lower.includes('add') && lower.includes('cart')) {
        reply = "I've added the selected product to your cart.";
        addToCart({ id: 'p1', name: 'Organic Whole Milk 1L', price: 75, brand: 'FarmFresh' });
      } else if (lower.includes('where') || lower.includes('locate') || lower.includes('aisle')) {
        reply = "Your product is located in Aisle 4, Rack B2.";
        if (onSelectProductForNavigation) {
          onSelectProductForNavigation({ name: 'Organic Whole Milk', aisle: '4', rack: 'B2' });
        }
      }

      setResponseMessage(reply);
      setAssistantState('RESPONDING');
      speakText(reply);
      setTimeout(() => setAssistantState('IDLE'), 3000);
    }, 1000);
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use text search.');
      return;
    }
    if (assistantState === 'LISTENING') {
      recognitionRef.current.stop();
      setAssistantState('IDLE');
    } else {
      setTranscript('');
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error(e);
      }
    }
  };

  return (
    <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 backdrop-blur-xl shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-semibold tracking-wide text-purple-300 uppercase">
            AI Assistant — {assistantState}
          </span>
        </div>
        <button
          onClick={() => speakText(responseMessage)}
          className="p-2 text-gray-400 hover:text-white bg-slate-800 rounded-xl transition-all"
          title="Repeat Response"
        >
          <Volume2 className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-slate-950/60 rounded-xl p-4 mb-6 border border-slate-800">
        <p className="text-gray-200 text-base leading-relaxed">{responseMessage}</p>
        {transcript && <p className="text-purple-400 text-sm mt-2 italic">"{transcript}"</p>}
      </div>

      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          {assistantState === 'LISTENING' && <AudioWaveform />}
          <button
            onClick={toggleListening}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-2xl ${
              assistantState === 'LISTENING'
                ? 'bg-red-600 text-white animate-pulse glow-purple'
                : 'bg-gradient-to-tr from-purple-600 to-blue-600 text-white hover:scale-105 glow-purple'
            }`}
          >
            {assistantState === 'LISTENING' ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            processUserQuery(textInput);
            setTextInput('');
          }}
          className="w-full flex gap-2 mt-2"
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type your request (e.g., 'Find organic milk')..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-purple-500 transition-all"
          />
          <button
            type="submit"
            className="px-5 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-medium transition-all flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};