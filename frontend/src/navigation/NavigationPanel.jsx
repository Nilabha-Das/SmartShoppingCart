import React from 'react';
import { MapPin, Navigation, ArrowLeft } from 'lucide-react';

export const NavigationPanel = ({ product, onBack }) => {
  return (
    <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 backdrop-blur-xl shadow-xl">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={onBack} className="p-2 text-gray-400 hover:text-white bg-slate-800 rounded-xl">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h2 className="text-lg font-bold text-white">In-Store Navigation</h2>
      </div>

      <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 bg-purple-600/20 border border-purple-500/40 rounded-xl flex items-center justify-center text-purple-400">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">{product?.name || 'Organic Whole Milk'}</h3>
            <p className="text-sm text-purple-400 font-medium">Aisle {product?.aisle || '4'} • Rack {product?.rack || 'B2'}</p>
          </div>
        </div>

        <div className="space-y-3 text-sm text-gray-300 border-t border-slate-800 pt-4">
          <p className="flex items-start gap-2">
            <Navigation className="w-4 h-4 text-emerald-400 mt-1 flex-shrink-0" />
            <span>Continue straight from your current position past the dairy cooler, then take a right at Aisle 4.</span>
          </p>
        </div>
      </div>
    </div>
  );
};