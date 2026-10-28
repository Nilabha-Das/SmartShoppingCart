import React, { useState } from 'react';
import { useCart } from '../../context/CartContext';
import { Trash2, ShoppingBag, ArrowRight, Wallet, AlertTriangle } from 'lucide-react';

export const CartSidebar = () => {
  const { cart, removeFromCart } = useCart();
  const [budgetLimit, setBudgetLimit] = useState(1000); // Default ₹1000 limit
  const [isEditingBudget, setIsEditingBudget] = useState(false);
  const [tempBudget, setTempBudget] = useState(1000);

  const items = cart?.items || [];
  const subtotal = cart?.subtotal || 0;
  const budgetPercentage = Math.min(Math.round((subtotal / budgetLimit) * 100), 100);
  const isOverBudget = subtotal > budgetLimit;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 h-full flex flex-col justify-between shadow-xl">
      <div>
        <div className="flex items-center gap-3 mb-6">
          <ShoppingBag className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-bold text-white">Cart Summary</h2>
          <span className="ml-auto px-2.5 py-0.5 bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded-full text-xs font-semibold">
            {items.length} items
          </span>
        </div>

        {/* Budget Tracker Box */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-gray-400 text-xs">
              <Wallet className="w-4 h-4 text-purple-400" />
              <span>Budget Limit: ₹{budgetLimit}</span>
            </div>
            <button
              onClick={() => setIsEditingBudget(!isEditingBudget)}
              className="text-purple-400 hover:underline text-xs font-medium"
            >
              {isEditingBudget ? 'Save' : 'Edit'}
            </button>
          </div>

          {isEditingBudget ? (
            <div className="flex gap-2 mb-3">
              <input
                type="number"
                value={tempBudget}
                onChange={(e) => setTempBudget(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-xs text-white"
              />
              <button
                onClick={() => {
                  setBudgetLimit(tempBudget);
                  setIsEditingBudget(false);
                }}
                className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs"
              >
                Set
              </button>
            </div>
          ) : (
            <>
              {/* Progress Bar */}
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full transition-all duration-500 ${
                    isOverBudget ? 'bg-red-500 animate-pulse' : budgetPercentage > 80 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${budgetPercentage}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-gray-400">
                <span>Spent: ₹{subtotal}</span>
                <span className={isOverBudget ? 'text-red-400 font-bold' : ''}>{budgetPercentage}% used</span>
              </div>
            </>
          )}

          {isOverBudget && (
            <div className="mt-3 flex items-center gap-2 bg-red-950/50 border border-red-500/30 rounded-lg p-2 text-red-300 text-xs">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>Budget limit exceeded by ₹{subtotal - budgetLimit}!</span>
            </div>
          )}
        </div>

        {items.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">Your cart is currently empty.</div>
        ) : (
          <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
            {items.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <div>
                  <h4 className="text-sm font-medium text-white">{item.product.name}</h4>
                  <p className="text-xs text-gray-400">Qty: {item.quantity} × ₹{item.product.price}</p>
                </div>
                <button
                  onClick={() => removeFromCart(item.product.id || item.product._id)}
                  className="text-gray-500 hover:text-red-400 p-1.5 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-slate-800 pt-4 mt-4">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-400">Total Amount</span>
          <span className="text-xl font-bold text-emerald-400">₹{subtotal}</span>
        </div>
        <button
          disabled={items.length === 0}
          className="w-full py-3.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-xl font-medium transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span>Proceed to Checkout</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};