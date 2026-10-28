import React from 'react';
import { MapPin, Navigation, Compass } from 'lucide-react';

export const StoreMap = ({ targetAisle = '4', targetRack = 'B2' }) => {
  // Mock layout of store aisles
  const aisles = [
    { id: '1', name: 'Aisle 1: Snacks & Beverages', x: 20, y: 30 },
    { id: '2', name: 'Aisle 2: Bakery & Biscuits', x: 40, y: 30 },
    { id: '3', name: 'Aisle 3: Produce & Fresh', x: 60, y: 30 },
    { id: '4', name: 'Aisle 4: Dairy & Organic', x: 80, y: 30 },
    { id: '5', name: 'Aisle 5: Household & Cleaning', x: 30, y: 70 },
    { id: '6', name: 'Aisle 6: Personal Care', x: 70, y: 70 },
  ];

  return (
    <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 backdrop-blur-xl shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Compass className="w-5 h-5 text-purple-400 animate-spin-slow" />
          <h3 className="text-base font-bold text-white">Store Floor Map & Route Guidance</h3>
        </div>
        <span className="text-xs px-3 py-1 bg-purple-600/20 text-purple-300 border border-purple-500/30 rounded-full font-medium">
          Target: Aisle {targetAisle} ({targetRack})
        </span>
      </div>

      {/* Visual Map Grid */}
      <div className="relative w-full h-64 bg-slate-950 rounded-xl border border-slate-800 p-4 overflow-hidden flex items-center justify-center">
        {/* Entrance Marker */}
        <div className="absolute bottom-3 left-6 px-3 py-1 bg-blue-600/30 border border-blue-500/50 rounded-lg text-blue-300 text-xs font-semibold flex items-center gap-1.5">
          <Navigation className="w-3.5 h-3.5" />
          <span>Cart Entrance</span>
        </div>

        {/* Store Aisles Layout */}
        <div className="grid grid-cols-3 gap-4 w-full max-w-lg z-10">
          {aisles.map((aisle) => {
            const isTarget = aisle.id === targetAisle;
            return (
              <div
                key={aisle.id}
                className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-center ${
                  isTarget
                    ? 'bg-purple-600/30 border-purple-500 text-white shadow-lg shadow-purple-600/30 animate-pulse'
                    : 'bg-slate-900/80 border-slate-800 text-gray-400'
                }`}
              >
                <MapPin className={`w-4 h-4 mb-1 ${isTarget ? 'text-purple-400' : 'text-gray-500'}`} />
                <span className="text-xs font-bold">Aisle {aisle.id}</span>
                <span className="text-[10px] opacity-70 truncate w-full">{aisle.name.split(':')[1]}</span>
              </div>
            );
          })}
        </div>

        {/* Pulsing route line overlay simulation */}
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,rgba(168,85,247,0.08)_0%,transparent_70%)]" />
      </div>
    </div>
  );
};