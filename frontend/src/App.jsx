import React, { useState } from 'react';
import { 
  ShoppingCart, ShieldCheck, Loader2, AlertCircle, Home, Mic, MicOff, 
  Search, ShoppingBag, Settings, LogOut, Volume2, Send, Plus, MapPin, 
  Trash2, ArrowRight, Wallet, AlertTriangle, Compass, Navigation, ArrowLeft, Heart, Sparkles, Lock, Star, CheckCircle2, Store, Bookmark, UserPlus, ArrowRightCircle
} from 'lucide-react';

// ==========================================
// 1. MAIN APP COMPONENT
// ==========================================
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState('');
  const [toastMessage, setToastMessage] = useState(null);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [finalBillData, setFinalBillData] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleVerify = (terminalId, password) => {
    setIsVerifying(true);
    setVerifyError('');

    setTimeout(() => {
      setIsVerifying(false);
      if (password !== '1234') {
        setVerifyError('Invalid security PIN. (Default PIN: 1234)');
        return;
      }
      setUser({ name: 'Juhi Das', id: terminalId || 'CART-8821', store: 'Store #04 - Downtown' });
      setIsAuthenticated(true);
      showToast('Secure session initialized successfully!');
    }, 1000);
  };

  const handleRegister = (email) => {
    setIsVerifying(true);
    setVerifyError('');

    setTimeout(() => {
      setIsVerifying(false);
      setUser({ name: email.split('@')[0] || 'New Shopper', id: 'CART-NEW', store: 'Store #04 - Downtown' });
      setIsAuthenticated(true);
      showToast('Account created successfully! Welcome!');
    }, 1000);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setIsCheckingOut(false);
    setFinalBillData(null);
  };

  // If checking out, show final billing payment screen & thank you message
  if (isCheckingOut && finalBillData) {
    return (
      <CheckoutScreen 
        bill={finalBillData} 
        user={user} 
        onFinish={handleLogout} 
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <VerificationScreen 
        onVerify={handleVerify} 
        onRegister={handleRegister}
        isVerifying={isVerifying} 
        error={verifyError} 
      />
    );
  }

  return (
    <Dashboard 
      user={user} 
      onLogout={handleLogout} 
      toast={toastMessage} 
      showToast={showToast} 
      onCheckout={(cartSummary) => {
        setFinalBillData(cartSummary);
        setIsCheckingOut(true);
      }}
    />
  );
}

// ==========================================
// 2. WELCOME, GREETING & AUTHENTICATION SCREEN
// ==========================================
function VerificationScreen({ onVerify, onRegister, isVerifying, error }) {
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
    onRegister(regEmail);
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

        {/* STEP 1: Welcome Greeting */}
        {step === 'WELCOME' && (
          <div className="space-y-6 text-center py-4">
            <div className="bg-purple-50 border border-purple-200 rounded-2xl p-5">
              <h2 className="text-lg font-bold text-purple-900 mb-1">👋 Welcome, Shopper!</h2>
              <p className="text-xs text-purple-700 leading-relaxed">
                We are thrilled to have you here. Let's make your shopping experience smart, quick, and seamless!
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

        {/* STEP 3A: Existing Customer Login (Direct Credentials) */}
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

        {/* STEP 3B: Create Account View (Shown only if NOT existing customer) */}
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
}

// ==========================================
// 3. FINAL CHECKOUT / BILLING PAYMENT SCREEN
// ==========================================
function CheckoutScreen({ bill, user, onFinish }) {
  const tax = Math.round(bill.subtotal * 0.05); // 5% GST estimate
  const grandTotal = bill.subtotal + tax;

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 font-sans">
      <div className="max-w-lg w-full bg-white border border-slate-200 rounded-3xl p-8 shadow-2xl text-center space-y-6">
        <div className="w-16 h-16 bg-emerald-100 border border-emerald-200 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 shadow-inner">
          <CheckCircle2 className="w-8 h-8" />
        </div>

        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Billing & Payment Summary</h1>
          <p className="text-xs text-slate-500">Shopper: {user?.name} | Terminal: {user?.id}</p>
        </div>

        {/* Itemized Bill Breakdown */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 text-left space-y-3">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Purchased Items</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
            {bill.items.map((item) => (
              <div key={item.id} className="flex justify-between text-xs text-slate-700">
                <span>{item.name} (x{item.quantity})</span>
                <span className="font-semibold">₹{item.price * item.quantity}</span>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-200 pt-3 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-500">
              <span>Subtotal</span>
              <span>₹{bill.subtotal}</span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Estimated Tax (5%)</span>
              <span>₹{tax}</span>
            </div>
            <div className="flex justify-between font-bold text-slate-900 text-sm border-t border-slate-200 pt-2">
              <span>Total Payment Due</span>
              <span className="text-emerald-600">₹{grandTotal}</span>
            </div>
          </div>
        </div>

        {/* Thank You Message */}
        <div className="bg-purple-50 border border-purple-200 rounded-2xl p-4 text-purple-900">
          <p className="text-sm font-bold">Thanks for buying! Visit again.</p>
          <p className="text-[11px] text-purple-700 mt-0.5">We hope you enjoyed your smart shopping experience.</p>
        </div>

        <button
          onClick={onFinish}
          className="w-full py-4 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-2xl shadow-lg transition-all"
        >
          Start New Session / Exit
        </button>
      </div>
    </div>
  );
}

// ==========================================
// 4. ENHANCED DASHBOARD
// ==========================================
function Dashboard({ user, onLogout, toast, showToast, onCheckout }) {
  const [activeTab, setActiveTab] = useState('home');
  const [navProduct, setNavProduct] = useState(null);
  const [cartItems, setCartItems] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', price: 75, quantity: 1 }
  ]);
  const [budgetLimit, setBudgetLimit] = useState(1000);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [favorites, setFavorites] = useState(['1']);

  const [products] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', brand: 'FarmFresh', price: 75, badge: 'Recommended', category: 'Dairy', rating: 4.8, aisle: '4', rack: 'B2', stock: 'In Stock' },
    { id: '2', name: 'Almond Milk Unsweetened', brand: 'NutriGood', price: 140, badge: 'Popular', category: 'Dairy', rating: 4.6, aisle: '4', rack: 'B3', stock: 'In Stock' },
    { id: '3', name: 'Whole Wheat Biscuits', brand: 'HealthyBake', price: 90, badge: 'Under ₹100', category: 'Bakery', rating: 4.5, aisle: '2', rack: 'A1', stock: 'In Stock' },
    { id: '4', name: 'Gluten-Free Oats 500g', brand: 'NutriGood', price: 210, badge: 'Healthy Choice', category: 'Snacks', rating: 4.9, aisle: '3', rack: 'C4', stock: 'Low Stock' },
  ]);

  const [searchResults, setSearchResults] = useState(products);

  const toggleFavorite = (productId) => {
    if (favorites.includes(productId)) {
      setFavorites(favorites.filter(id => id !== productId));
      showToast('Removed from favorites.');
    } else {
      setFavorites([...favorites, productId]);
      showToast('Added to your favorites list! ❤️');
    }
  };

  const handleSearch = (query) => {
    if (!query.trim()) {
      filterByCategory(selectedCategory);
      return;
    }
    const filtered = products.filter((p) => 
      p.name.toLowerCase().includes(query.toLowerCase()) || 
      p.brand.toLowerCase().includes(query.toLowerCase()) ||
      p.category.toLowerCase().includes(query.toLowerCase())
    );
    setSearchResults(filtered);
  };

  const filterByCategory = (cat) => {
    setSelectedCategory(cat);
    if (cat === 'All') {
      setSearchResults(products);
    } else {
      setSearchResults(products.filter(p => p.category === cat));
    }
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
    showToast(`Added "${product.name}" to cart!`);
  };

  const removeFromCart = (id) => {
    setCartItems((prev) => prev.filter((item) => item.id !== id));
    showToast('Item removed from cart.');
  };

  const handleProceedCheckout = () => {
    const subtotal = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);
    onCheckout({ items: cartItems, subtotal });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex text-slate-900 font-sans relative">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 text-xs font-semibold animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toast}</span>
        </div>
      )}

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={onLogout} favoritesCount={favorites.length} />

      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-4 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              Welcome back, {user?.name || 'Shopper'}! 👋
            </h1>
            <p className="text-xs text-slate-500 font-medium flex items-center gap-2 mt-1">
              <Store className="w-3.5 h-3.5 text-purple-600" /> {user?.store} | Terminal ID: {user?.id}
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 border border-purple-200 rounded-2xl text-purple-700 text-sm font-semibold shadow-sm">
            <Sparkles className="w-4 h-4 text-purple-600 animate-spin" />
            <span>AI Voice Ready</span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {navProduct ? (
              <NavigationPanel product={navProduct} onBack={() => setNavProduct(null)} />
            ) : (
              <>
                {activeTab === 'preferences' && <PreferencesPanel addToCart={addToCart} showToast={showToast} />}

                {activeTab === 'favorites' && (
                  <div className="space-y-6">
                    <div className="flex items-center gap-3 mb-2">
                      <Heart className="w-6 h-6 text-purple-600 fill-purple-600" />
                      <div>
                        <h2 className="text-lg font-bold text-slate-900">My Saved Favorites</h2>
                        <p className="text-xs text-slate-500">Items you marked to purchase later</p>
                      </div>
                    </div>

                    {favorites.length === 0 ? (
                      <div className="bg-white border border-slate-200 rounded-3xl p-12 text-center">
                        <Heart className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                        <p className="text-sm font-semibold text-slate-700">No favorite items saved yet.</p>
                        <p className="text-xs text-slate-400 mt-1">Click the heart icon on any product card to save it here.</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {products
                          .filter((p) => favorites.includes(p.id))
                          .map((p) => (
                            <ProductCard 
                              key={p.id} 
                              product={p} 
                              isFavorite={true}
                              onToggleFavorite={toggleFavorite}
                              onAddToCart={addToCart} 
                              onNavigate={(prod) => setNavProduct(prod)} 
                            />
                          ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'assistant' && (
                  <VoiceAssistant 
                    addToCart={addToCart} 
                    onNavigate={(p) => setNavProduct(p)} 
                    onSearch={(q) => handleSearch(q)}
                  />
                )}

                {activeTab === 'search' && (
                  <div className="space-y-6">
                    <SearchBar onSearch={handleSearch} />
                    <CategoryChips selected={selectedCategory} onSelect={filterByCategory} />
                    <h2 className="text-lg font-bold text-slate-900">Search Results</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {searchResults.map((p) => (
                        <ProductCard 
                          key={p.id} 
                          product={p} 
                          isFavorite={favorites.includes(p.id)}
                          onToggleFavorite={toggleFavorite}
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
                      onSearch={(q) => handleSearch(q)}
                    />
                    <PreferencesPanel addToCart={addToCart} showToast={showToast} />
                    <div className="space-y-4">
                      <SearchBar onSearch={handleSearch} />
                      <CategoryChips selected={selectedCategory} onSelect={filterByCategory} />
                      <h2 className="text-lg font-bold text-slate-900 pt-2">Recommended For You</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {searchResults.map((p) => (
                          <ProductCard 
                            key={p.id} 
                            product={p} 
                            isFavorite={favorites.includes(p.id)}
                            onToggleFavorite={toggleFavorite}
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
              onCheckout={handleProceedCheckout}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

// ==========================================
// 5. SUPPORTING COMPONENTS (Sidebar, VoiceAssistant, etc.)
// ==========================================
function Sidebar({ activeTab, setActiveTab, onLogout, favoritesCount }) {
  const navItems = [
    { id: 'home', label: 'Dashboard', icon: Home },
    { id: 'favorites', label: 'Favorites', icon: Heart, badge: favoritesCount },
    { id: 'assistant', label: 'Voice Assistant', icon: Mic },
    { id: 'search', label: 'Search Products', icon: Search },
    { id: 'preferences', label: 'Preferences', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between p-6 shadow-sm">
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
                className={`w-full flex items-center justify-between px-4 py-3 rounded-2xl text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-200'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </div>
                {item.badge > 0 && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${isActive ? 'bg-white text-purple-700' : 'bg-purple-100 text-purple-700'}`}>
                    {item.badge}
                  </span>
                )}
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

function VoiceAssistant({ addToCart, onNavigate, onSearch }) {
  const [status, setStatus] = useState('IDLE');
  const [response, setResponse] = useState("Hello Juhi! I'm your Smart Cart Assistant. Tap the mic or choose a quick prompt below.");
  const [textInput, setTextInput] = useState('');

  const processQuery = (query) => {
    if (!query.trim()) return;
    setStatus('PROCESSING');

    setTimeout(() => {
      const q = query.toLowerCase();
      let reply = `Processed: "${query}"`;

      if (q.includes('milk')) {
        reply = "I found Organic Whole Milk in Aisle 4, Rack B2.";
        onSearch('Milk');
      } else if (q.includes('add')) {
        reply = "Added Organic Whole Milk to your shopping cart!";
        addToCart({ id: '1', name: 'Organic Whole Milk 1L', price: 75 });
      } else if (q.includes('where') || q.includes('aisle') || q.includes('navigate')) {
        reply = "Opening in-store store navigation for Aisle 4.";
        onNavigate({ name: 'Organic Whole Milk', aisle: '4', rack: 'B2' });
      } else {
        onSearch(query);
      }

      setResponse(reply);
      setStatus('RESPONDING');
      setTimeout(() => setStatus('IDLE'), 2500);
    }, 800);
  };

  const quickPrompts = [
    "Find organic milk",
    "Add milk to cart",
    "Where is aisle 4?",
    "Snacks under ₹200"
  ];

  return (
    <div className="bg-white border border-purple-200 rounded-3xl p-6 shadow-md relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-bold text-purple-700 uppercase tracking-wider bg-purple-50 border border-purple-200 px-3 py-1 rounded-full flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          AI Voice Assistant — {status}
        </span>
        <button onClick={() => alert(response)} className="p-2 text-slate-400 hover:text-slate-600 bg-slate-100 rounded-xl">
          <Volume2 className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-4">
        <p className="text-slate-800 text-sm font-medium leading-relaxed">{response}</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        <span className="text-[11px] text-slate-400 font-semibold self-center mr-1">Quick Ask:</span>
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => processQuery(prompt)}
            className="px-3 py-1 bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-700 rounded-full text-xs font-semibold transition-all"
          >
            💬 {prompt}
          </button>
        ))}
      </div>

      <div className="flex flex-col items-center gap-4">
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
            placeholder="Type your query or command..."
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

function CategoryChips({ selected, onSelect }) {
  const categories = ['All', 'Dairy', 'Bakery', 'Snacks'];
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => onSelect(cat)}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
            selected === cat
              ? 'bg-slate-900 text-white shadow-md'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}

function SearchBar({ onSearch }) {
  return (
    <div className="relative w-full">
      <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
      <input
        type="text"
        onChange={(e) => onSearch(e.target.value)}
        placeholder="Search products by name or category..."
        className="w-full bg-white border border-slate-200 rounded-2xl pl-12 pr-4 py-3 text-sm text-slate-900 focus:outline-none focus:border-purple-500 transition-all shadow-sm"
      />
    </div>
  );
}

function ProductCard({ product, isFavorite, onToggleFavorite, onAddToCart, onNavigate }) {
  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-5 flex flex-col justify-between shadow-sm hover:shadow-md transition-all group relative">
      <div>
        <div className="flex justify-between items-start mb-3">
          <span className="text-xs font-bold text-purple-700 bg-purple-50 border border-purple-200 px-2.5 py-1 rounded-lg">
            {product.badge}
          </span>
          <button
            onClick={() => onToggleFavorite(product.id)}
            className={`p-2 rounded-xl border transition-all ${
              isFavorite 
                ? 'bg-purple-100 border-purple-300 text-purple-600' 
                : 'bg-slate-50 border-slate-200 text-slate-400 hover:text-purple-600'
            }`}
          >
            <Heart className={`w-4 h-4 ${isFavorite ? 'fill-purple-600' : ''}`} />
          </button>
        </div>

        <div className="h-28 bg-slate-100 rounded-2xl mb-4 flex items-center justify-center text-slate-400 font-bold text-xs uppercase tracking-wider">
          {product.brand}
        </div>

        <div className="flex justify-between items-center mb-1">
          <h3 className="text-base font-bold text-slate-900 line-clamp-1">{product.name}</h3>
          <div className="flex items-center gap-1 text-xs font-bold text-amber-500">
            <Star className="w-3.5 h-3.5 fill-amber-400" />
            <span>{product.rating}</span>
          </div>
        </div>

        <p className="text-lg font-bold text-emerald-600 mb-4">₹{product.price}</p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onAddToCart(product)}
          className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-purple-100 transition-all"
        >
          <Plus className="w-4 h-4" /> Add to Cart
        </button>
        <button
          onClick={() => onNavigate(product)}
          className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-all"
        >
          <MapPin className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function PreferencesPanel({ addToCart, showToast }) {
  const [prefItems, setPrefItems] = useState([
    { id: '1', name: 'Organic Whole Milk 1L', price: 75, brand: 'FarmFresh' },
    { id: '3', name: 'Whole Wheat Biscuits', price: 90, brand: 'HealthyBake' }
  ]);
  const [newItem, setNewItem] = useState('');

  const handleAdd = (e) => {
    e.preventDefault();
    if (!newItem.trim()) return;
    setPrefItems([...prefItems, { id: Date.now().toString(), name: newItem, price: 100, brand: 'Custom' }]);
    setNewItem('');
    showToast('Preference item added successfully!');
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
          className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-2 text-xs text-slate-900 focus:outline-none focus:border-purple-500"
        />
        <button type="submit" className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-2xl text-xs font-semibold">
          Add
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {prefItems.map((item) => (
          <div key={item.id} className="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-900">{item.name}</p>
              <p className="text-[10px] text-purple-600 font-medium">₹{item.price} • {item.brand}</p>
            </div>
            <button
              onClick={() => addToCart(item)}
              className="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-xl text-xs font-bold transition-all"
            >
              + Add
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

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
            Located in Aisle {product.aisle || '4'} | Rack {product.rack || 'B2'}
          </p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl p-6 text-white mb-4 relative overflow-hidden h-48 flex items-center justify-center">
        <div className="grid grid-cols-3 gap-3 w-full max-w-sm text-center">
          <div className="bg-slate-800 p-3 rounded-xl border border-slate-700 text-xs">Aisle 1</div>
          <div className="bg-slate-800 p-3 rounded-xl border border-slate-700 text-xs">Aisle 2</div>
          <div className="bg-purple-600 text-white p-3 rounded-xl border border-purple-400 text-xs font-bold animate-pulse">
            Aisle {product.aisle || '4'} (Target)
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-500">Directions: Head straight down Main Corridor and turn right at Aisle {product.aisle || '4'}.</p>
    </div>
  );
}

function CartSidebar({ cartItems, onRemove, budgetLimit, setBudgetLimit, onCheckout }) {
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

        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-6">
          <div className="flex justify-between items-center text-xs font-semibold text-slate-700 mb-2">
            <span>Limit: ₹{budgetLimit}</span>
            <button onClick={() => setBudgetLimit(Number(prompt('Set Budget Limit (₹):', budgetLimit)) || budgetLimit)} className="text-purple-600 font-bold hover:underline">
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
                <button onClick={() => onRemove(item.id)} className="text-slate-400 hover:text-red-600 p-1">
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
        <button 
          onClick={onCheckout}
          disabled={cartItems.length === 0} 
          className="w-full py-3.5 bg-purple-600 text-white font-semibold rounded-2xl shadow-md shadow-purple-200 hover:bg-purple-700 disabled:opacity-50 transition-all"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  );
}