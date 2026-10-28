import React, { useState } from 'react';
import { ShoppingCart, ShieldCheck, Loader2, AlertCircle, Lock, UserPlus, ArrowRightCircle } from 'lucide-react';

export const VerificationScreen = ({ onVerify, isVerifying, error }) => {
  const [step, setStep] = useState('WELCOME'); // 'WELCOME' | 'ASK_CUSTOMER' | 'LOGIN' | 'REGISTER'
  const [terminalId, setTerminalId] = useState('CART-8821');
  const [password, setPassword] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    onVerify(terminalId, password);
  };

  const handleRegisterSubmit = (e) => {
    e.preventDefault();
    onVerify(terminalId, regPassword); // Logs them in with the registered credentials
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-3xl p-8 shadow-xl">
        <div className="text-center">
          <div className="w-16 h-16 bg-purple-100 border border-purple-200 rounded-2xl flex items-center justify-center mx-auto mb-6 text-purple-600 shadow-inner">
            <ShoppingCart className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Smart Shopping Cart</h1>
          <p className="text-slate-500 text-sm mb-6">AI Voice Assistant & Retail Navigation</p>
        </div>

        {error && (
          <div className="w-full bg-red-50 border border-red-200 rounded-xl p-3 mb-6 flex items-center gap-3 text-red-600 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* STEP 1: Greeting & Welcome Message */}
        {step === 'WELCOME' && (
          <div className="space-y-6 text-center py-4">
            <div className="bg-purple-50 border border-purple-200 rounded-2xl p-4">
              <h2 className="text-lg font-bold text-purple-900 mb-1">👋 Welcome, Shopper!</h2>
              <p className="text-xs text-purple-700 leading-relaxed">
                Experience seamless AI-powered voice guidance and smart in-store navigation with us.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setStep('ASK_CUSTOMER')}
              className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-2xl shadow-lg shadow-purple-200 flex items-center justify-center gap-2 transition-all"
            >
              <span>Get Started</span>
              <ArrowRightCircle className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* STEP 2: Ask if Existing Customer */}
        {step === 'ASK_CUSTOMER' && (
          <div className="space-y-6 text-center py-4">
            <h2 className="text-lg font-bold text-slate-800">Are you an existing customer?</h2>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setStep('LOGIN')}
                className="flex-1 py-3.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-2xl shadow-md shadow-purple-200 transition-all"
              >
                Yes
              </button>
              <button
                type="button"
                onClick={() => setStep('REGISTER')}
                className="flex-1 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-2xl transition-all border border-slate-200"
              >
                No
              </button>
            </div>
            <button 
              type="button" 
              onClick={() => setStep('WELCOME')} 
              className="text-xs text-slate-400 hover:text-slate-600 underline block mx-auto pt-2"
            >
              Back to Welcome
            </button>
          </div>
        )}

        {/* STEP 3A: Existing User Login Form */}
        {step === 'LOGIN' && (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">Existing Customer Login</span>
              <button 
                type="button" 
                onClick={() => setStep('ASK_CUSTOMER')} 
                className="text-xs text-slate-400 hover:text-slate-600 underline"
              >
                Back
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Terminal ID</label>
              <input
                type="text"
                value={terminalId}
                onChange={(e) => setTerminalId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Security PIN / Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter PIN (Try 1234)..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl pl-12 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isVerifying}
              className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-2xl shadow-lg shadow-purple-200 flex items-center justify-center gap-3 transition-all disabled:opacity-50 mt-2"
            >
              {isVerifying ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  <span>Unlock Secure Session</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* STEP 3B: Create Account Form */}
        {step === 'REGISTER' && (
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">Create New Account</span>
              <button 
                type="button" 
                onClick={() => setStep('ASK_CUSTOMER')} 
                className="text-xs text-slate-400 hover:text-slate-600 underline"
              >
                Back
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                placeholder="Enter your email..."
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Create Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Choose a password..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl pl-12 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isVerifying}
              className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-2xl shadow-lg shadow-purple-200 flex items-center justify-center gap-3 transition-all disabled:opacity-50 mt-2"
            >
              {isVerifying ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5" />
                  <span>Register & Start Shopping</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};