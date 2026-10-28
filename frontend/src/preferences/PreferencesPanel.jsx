import React, { useState } from 'react';
import { Heart, Plus, Trash2, ShoppingBag, Sparkles } from 'lucide-react';
import { useCart } from '../../context/CartContext';

export const PreferencesPanel = () => {
  const { addToCart } = useCart();
  const [newPreference, setNewPreference] = useState('');
  const [preferredItems, setPreferredItems] = useState([
    { id: 'pref-1', name: 'Organic Whole Milk 1L', brand: 'FarmFresh', price: 75 },
    { id: 'pref-2', name: 'Whole Wheat Digestive Biscuits', brand: 'HealthyBake', price: 90 },
    { id: 'pref-3', name: 'Almond Milk Unsweetened', brand: 'NutriGood', price: 140 },
  ]);

  const handleAddPreference = (e) => {
    e.preventDefault();
    if (!newPreference.trim()) return;

    const newItem = {
      id: `pref-${Date.now()}`,
      name: newPreference.trim(),
      brand: 'Custom Preference',
      price: 100, // Default estimated price
    };

    setPreferredItems([...preferredItems, newItem]);
    setNewPreference('');
  };

  const handleRemovePreference = (id) => {
    setPreferredItems(preferredItems.filter((item) => item.id !== id));
  };

  return (
    <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-6 backdrop-blur-xl shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600/20 border border-purple-500/40 rounded-xl flex items-center justify-center text-purple-400">
            <Heart className="w-5 h-5 fill-purple-400/20" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">My Preferred Shopping List</h2>
            <p className="text-xs text-gray-400">Save your regular items for quick 1-click ordering</p>
          </div>
        </div>
        <span className="text-xs px-3 py-1 bg-purple-600/20 text-purple-300 border border-purple-500/30 rounded-full font-semibold">
          {preferredItems.length} Saved Items
        </span>
      </div>

      {/* Add Item Form */}
      <form onSubmit={handleAddPreference} className="flex gap-2 mb-6">
        <input
          type="text"
          value={newPreference}
          onChange={(e) => setNewPreference(e.target.value)}
          placeholder="Add a product to your preferences (e.g., 'Greek Yogurt', 'Green Tea')..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition-all"
        />
        <button
          type="submit"
          className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-purple-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Add</span>
        </button>
      </form>

      {/* List of Preferred Items */}
      {preferredItems.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm bg-slate-950/40 rounded-xl border border-slate-800/60">
          No preferred items saved yet. Add items above to build your quick-access list!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {preferredItems.map((item) => (
            <div
              key={item.id}
              className="bg-slate-950/60 border border-slate-800 hover:border-purple-500/40 p-3.5 rounded-xl flex items-center justify-between transition-all group"
            >
              <div>
                <h4 className="text-sm font-semibold text-white">{item.name}</h4>
                <p className="text-xs text-purple-400 font-medium">₹{item.price} • {item.brand}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => addToCart(item)}
                  className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/30 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
                  title="Add to Cart"
                >
                  <ShoppingBag className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
                <button
                  onClick={() => handleRemovePreference(item.id)}
                  className="p-1.5 text-gray-500 hover:text-red-400 rounded-lg transition-all"
                  title="Remove"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};