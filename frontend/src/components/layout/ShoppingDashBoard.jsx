import React, { useState } from 'react';
import { 
  ShoppingCart, ShieldCheck, Loader2, AlertCircle, Home, Mic, MicOff, 
  Search, ShoppingBag, Settings, LogOut, Volume2, Send, Plus, MapPin, 
  Trash2, ArrowRight, Wallet, AlertTriangle, Compass, Navigation, ArrowLeft, Heart, Sparkles 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const ShoppingDashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('home');
  const [navProduct, setNavProduct] = useState(null);
  const [cartItems, setCartItems] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', price: 75, quantity: 1 }
  ]);
  const [budgetLimit, setBudgetLimit] = useState(1000);

  const [products] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', brand: 'FarmFresh', price: 75, badge: 'Recommended', aisle: '4', rack: 'B2' },
    { id: '2', name: 'Almond Milk Unsweetened', brand: 'NutriGood', price: 140, badge: 'Popular', aisle: '4', rack: 'B3' },
    { id: '3', name: 'Whole Wheat Biscuits', brand: 'HealthyBake', price: 90, badge: 'Under ₹100', aisle: '2', rack: 'A1' },
    { id: '4', name: 'Gluten-Free Oats 500g', brand: 'NutriGood', price: 210, badge: 'Healthy Choice', aisle: '3', rack: 'C4' },
  ]);

  const [searchResults, setSearchResults] = useState(products);

  const handleSearch = (query) => {
    if (!query.trim()) {
      setSearchResults(products);
      return;
    }
    const filtered = products.filter((p) => 
      p.name.toLowerCase().includes(query.toLowerCase()) || 
      p.brand.toLowerCase().includes(query.toLowerCase())
    );
    setSearchResults(filtered);
  };

  const addToCart = (product) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  };

  const removeFromCart = (id) => {
    setCartItems((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <div className="min-h-screen bg-slate-50 flex text-slate-900 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={logout} />

      {/* Main Content Area */}
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex items-center justify-between mb-8 pb-4 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Welcome back, {user?.name || 'Shopper'}! 👋
            </h1>
            <p className="text-xs text-slate-500 font-medium">Cart Terminal ID: {user?.id || 'CART-99'}</p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 border border-purple-200 rounded-xl text-purple-700 text-sm font-semibold shadow-sm">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>AI Voice Ready</span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {navProduct ? (
              <NavigationPanel product={navProduct} onBack={() => setNavProduct(null)} />
            ) : (
              <>
                {activeTab === 'preferences' && <PreferencesPanel addToCart={addToCart} />}

                {activeTab === 'assistant' && (
                  <VoiceAssistant 
                    addToCart={addToCart} 
                    onNavigate={(p) => setNavProduct(p)} 
                  />
                )}

                {activeTab === 'search' && (
                  <div className="space-y-6">
                    <SearchBar onSearch={handleSearch} />
                    <h2 className="text-lg font-bold text-slate-900">Search Results</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {searchResults.map((p) => (
                        <ProductCard 
                          key={p.id} 
                          product={p} 
                          onAddToCart={addToCart} 
                          onNavigate={(prod) => setNavProduct(prod)} 
                        />
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'home' && (
                  <div className="space-y-8">
                    <VoiceAssistant 
                      addToCart={addToCart} 
                      onNavigate={(p) => setNavProduct(p)} 
                    />
                    <PreferencesPanel addToCart={addToCart} />
                    <div className="space-y-4">
                      <SearchBar onSearch={handleSearch} />
                      <h2 className="text-lg font-bold text-slate-900 pt-2">Recommended For You</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {searchResults.map((p) => (
                          <ProductCard 
                            key={p.id} 
                            product={p} 
                            onAddToCart={addToCart} 
                            onNavigate={(prod) => setNavProduct(prod)} 
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="lg:col-span-1">
            <CartSidebar 
              cartItems={cartItems} 
              onRemove={removeFromCart} 
              budgetLimit={budgetLimit} 
              setBudgetLimit={setBudgetLimit} 
            />
          </div>
        </div>
      </main>
    </div>
  );
};

// ==========================================
// SIDEBAR COMPONENT
// ==========================================
function Sidebar({ activeTab, setActiveTab, onLogout }) {
  const navItems = [
    { id: 'home', label: 'Dashboard', icon: Home },
    { id: 'assistant', label: 'Voice Assistant', icon: Mic },
    { id: 'search', label: 'Search Products', icon: Search },
    { id: 'preferences', label: 'Preferences', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between p-6">
      <div>
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-purple-600 rounded-2xl flex items-center justify-center text-white font-bold shadow-md shadow-purple-200">
            SC
          </div>
          <span className="text-base font-bold text-slate-900 tracking-tight">SmartCart AI</span>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-200'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <button
        onClick={onLogout}
        className="flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-2xl text-sm font-semibold transition-all w-full"
      >
        <LogOut className="w-5 h-5" />
        <span>End Session</span>
      </button>
    </aside>
  );
}

// ==========================================
// VOICE ASSISTANT COMPONENT
// ==========================================
function VoiceAssistant({ addToCart, onNavigate }) {
  const [status, setStatus] = useState('IDLE');
  const [response, setResponse] = useState("Hello! I'm your Smart Cart Assistant. How can I help you find items today?");
  const [textInput, setTextInput] = useState('');

  const processQuery = (query) => {
    if (!query.trim()) return;
    setStatus('PROCESSING');

    setTimeout(() => {
      const q = query.toLowerCase();
      let reply = `Searching for "${query}"...`;

      if (q.includes('milk')) {
        reply = "I found Organic Whole Milk in Aisle 4, Rack B2.";
      } else if (q.includes('add')) {
        reply = "Added Organic Whole Milk to your shopping cart!";
        addToCart({ id: '1', name: 'Organic Whole Milk 1L', price: 75 });
      } else if (q.includes('where') || q.includes('aisle') || q.includes('navigate')) {
        reply = "Opening in-store navigation for Aisle 4.";
        onNavigate({ name: 'Organic Whole Milk', aisle: '4', rack: 'B2' });
      }

      setResponse(reply);
      setStatus('RESPONDING');
      setTimeout(() => setStatus('IDLE'), 2500);
    }, 800);
  };

  return (
    <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-md relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-bold text-purple-700 uppercase tracking-wider bg-purple-50 border border-purple-200 px-3 py-1 rounded-full">
          AI Voice Assistant — {status}
        </span>
        <button onClick={() => alert(response)} className="p-2 text-slate-400 hover:text-slate-600 bg-slate-100 rounded-xl">
          <Volume2 className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-6">
        <p className="text-slate-800 text-sm font-medium leading-relaxed">{response}</p>
      </div>

      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          {status === 'LISTENING' && (
            <div className="absolute -inset-3 rounded-full border-2 border-purple-400 animate-ping opacity-75" />
          )}
          <button
            onClick={() => {
              if (status === 'LISTENING') setStatus('IDLE');
              else {
                setStatus('LISTENING');
                setTimeout(() => processQuery("Find organic milk"), 3000);
              }
            }}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-all shadow-lg ${
              status === 'LISTENING' 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'bg-purple-600 text-white hover:bg-purple-700 hover:scale-105'
            }`}
          >
            {status === 'LISTENING' ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            processQuery(textInput);
            setTextInput('');
          }}
          className="w-full flex gap-2 mt-2"
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type your query (e.g. 'Add milk to cart')..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500 transition-all"
          />
          <button type="submit" className="px-5 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-2xl font-semibold transition-all">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

// ==========================================
// SEARCH & PRODUCT CARD
// ==========================================
function SearchBar({ onSearch }) {
  return (
    <div className="relative w-full">
      <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
      <input
        type="text"
        onChange={(e) => onSearch(e.target.value)}
        placeholder="Search products by name or category (e.g., 'Milk', 'Oats')..."
        className="w-full bg-white border border-slate-200 rounded-2xl pl-12 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500 transition-all shadow-sm"
      />
    </div>
  );
}

function ProductCard({ product, onAddToCart, onNavigate }) {
  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition-all">
      <div>
        <div className="h-32 bg-slate-100 rounded-2xl mb-4 flex items-center justify-center text-slate-400 font-bold text-xs uppercase tracking-wider">
          {product.brand}
        </div>
        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg">
          {product.badge}
        </span>
        <h3 className="text-base font-bold text-slate-900 mt-2 mb-1">{product.name}</h3>
        <p className="text-lg font-bold text-emerald-600 mb-4">₹{product.price}</p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onAddToCart(product)}
          className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-purple-100"
        >
          <Plus className="w-4 h-4" /> Add
        </button>
        <button
          onClick={() => onNavigate(product)}
          className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-all"
          title="Navigate to Aisle"
        >
          <MapPin className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ==========================================
// PREFERENCES PANEL
// ==========================================
function PreferencesPanel({ addToCart }) {
  const [prefItems, setPrefItems] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', price: 75 },
    { id: '3', name: 'Whole Wheat Biscuits', price: 90 }
  ]);
  const [newItem, setNewItem] = useState('');

  const handleAdd = (e) => {
    e.preventDefault();
    if (!newItem.trim()) return;
    setPrefItems([...prefItems, { id: Date.now().toString(), name: newItem, price: 100 }]);
    setNewItem('');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-4">
        <Heart className="w-5 h-5 text-purple-600 fill-purple-100" />
        <h2 className="text-base font-bold text-slate-900">My Preferred Shopping List</h2>
      </div>

      <form onSubmit={handleAdd} className="flex gap-2 mb-4">
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="Add preferred item..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-purple-500"
        />
        <button type="submit" className="px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-semibold">
          Add
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {prefItems.map((item) => (
          <div key={item.id} className="bg-slate-50 border border-slate-200 p-3 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-900">{item.name}</p>
              <p className="text-[10px] text-purple-600 font-medium">₹{item.price}</p>
            </div>
            <button
              onClick={() => addToCart(item)}
              className="px-2.5 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-bold hover:bg-purple-200"
            >
              + Add
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================
// NAVIGATION PANEL
// ==========================================
function NavigationPanel({ product, onBack }) {
  return (
    <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-md">
      <button onClick={onBack} className="flex items-center gap-2 text-xs font-bold text-slate-600 mb-4 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4" /> Back to Products
      </button>

      <div className="flex items-center gap-4 mb-6 bg-purple-50 border border-purple-200 p-4 rounded-2xl">
        <MapPin className="w-8 h-8 text-purple-600" />
        <div>
          <h3 className="text-base font-bold text-slate-900">{product.name}</h3>
          <p className="text-xs text-purple-700 font-semibold">
            Located in Aisle {product.aisle || '4'} • Rack {product.rack || 'B2'}
          </p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl p-6 text-white mb-4 relative overflow-hidden h-48 flex items-center justify-center">
        <div className="grid grid-cols-3 gap-3 w-full max-w-sm text-center">
          <div className="bg-slate-800 p-3 rounded-xl border border-slate-700 text-xs">Aisle 1</div>
          <div className="bg-slate-800 p-3 rounded-xl border border-slate-700 text-xs">Aisle 2</div>
          <div className="bg-purple-600 text-white p-3 rounded-xl border border-purple-400 text-xs font-bold animate-pulse">
            Aisle 4 (Target)
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-500">Directions: Head straight down Main Corridor and turn right at Aisle 4.</p>
    </div>
  );
}

// ==========================================
// CART SIDEBAR & BUDGET TRACKER
// ==========================================
function CartSidebar({ cartItems, onRemove, budgetLimit, setBudgetLimit }) {
  const subtotal = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);
  const budgetPercentage = Math.min(Math.round((subtotal / budgetLimit) * 100), 100);
  const isOverBudget = subtotal > budgetLimit;

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-3 mb-6">
          <ShoppingBag className="w-5 h-5 text-purple-600" />
          <h2 className="text-lg font-bold text-slate-900">Cart Summary</h2>
        </div>

        {/* Budget Tracker Box */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-6">
          <div className="flex justify-between items-center text-xs font-semibold text-slate-700 mb-2">
            <span>Limit: ₹{budgetLimit}</span>
            <button onClick={() => setBudgetLimit(Number(prompt('Set Budget Limit (₹):', budgetLimit)) || budgetLimit)} className="text-purple-600">
              Edit
            </button>
          </div>
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden mb-2">
            <div
              className={`h-full transition-all ${isOverBudget ? 'bg-red-500' : 'bg-emerald-500'}`}
              style={{ width: `${budgetPercentage}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-500">Spent: ₹{subtotal} ({budgetPercentage}%)</p>
          {isOverBudget && (
            <div className="mt-2 text-red-600 text-[11px] font-bold flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> Budget Exceeded!
            </div>
          )}
        </div>

        {cartItems.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6">Your cart is empty.</p>
        ) : (
          <div className="space-y-3">
            {cartItems.map((item) => (
              <div key={item.id} className="flex justify-between items-center bg-slate-50 border border-slate-200 p-3 rounded-2xl text-xs">
                <div>
                  <p className="font-bold text-slate-900">{item.name}</p>
                  <p className="text-slate-500">Qty: {item.quantity} × ₹{item.price}</p>
                </div>
                <button onClick={() => onRemove(item.id)} className="text-slate-400 hover:text-red-600">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 pt-4 mt-6">
        <div className="flex justify-between font-bold text-slate-900 mb-4">
          <span>Total</span>
          <span className="text-emerald-600">₹{subtotal}</span>
        </div>
        <button disabled={cartItems.length === 0} className="w-full py-3.5 bg-purple-600 text-white font-semibold rounded-2xl shadow-md shadow-purple-200 hover:bg-purple-700 disabled:opacity-50">
          Checkout
        </button>
      </div>
    </div>
  );
}