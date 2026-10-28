import React from 'react';
import { Plus, MapPin, Info } from 'lucide-react';
import { useCart } from '../../context/CartContext';

export const ProductCard = ({ product, onNavigate }) => {
  const { addToCart } = useCart();

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between hover:border-purple-500/40 transition-all shadow-lg group">
      <div>
        <div className="relative h-40 bg-slate-950 rounded-xl overflow-hidden mb-4 flex items-center justify-center">
          <img
            src={product.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=500&q=80'}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          {product.badge && (
            <span className="absolute top-2 left-2 px-2.5 py-1 bg-purple-600/90 text-white text-xs font-semibold rounded-lg backdrop-blur-md">
              {product.badge}
            </span>
          )}
        </div>
        <p className="text-xs text-purple-400 font-medium mb-1">{product.brand || 'Store Brand'}</p>
        <h3 className="text-base font-semibold text-white mb-2 line-clamp-1">{product.name}</h3>
        <p className="text-lg font-bold text-emerald-400 mb-4">₹{product.price}</p>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => addToCart(product)}
          className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Add</span>
        </button>
        {onNavigate && (
          <button
            onClick={() => onNavigate(product)}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-gray-300 hover:text-white rounded-xl transition-all"
            title="Navigate to Aisle"
          >
            <MapPin className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};