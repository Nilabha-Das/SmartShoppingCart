import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8081/api/ai";

function App() {
  const [message, setMessage] = useState("");
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("Voice search is ready");

  const recognitionRef = useRef(null);
  const shouldListenRef = useRef(false);

  async function searchProducts(query) {
    const searchMessage = query.trim();
    if (!searchMessage) return;

    setMessage(searchMessage);
    setLoading(true);
    setError("");
    setSearched(true);
    setProducts([]);

    try {
      const params = new URLSearchParams({
        message: searchMessage,
        session_id: "react-session-01",
        ask_preferences: "false",
      });

      const response = await fetch(
        `${API_BASE}/shopping/search?${params.toString()}`,
      );

      if (!response.ok) {
        throw new Error(`Search failed (${response.status})`);
      }

      const data = await response.json();

      const foundProducts = Array.isArray(data)
        ? data
        : (data.products ?? data.results ?? data.recommendations ?? []);

      setProducts(foundProducts);

      if (foundProducts.length === 0) {
        setVoiceStatus("No matching products found. Try another search.");
      } else {
        setVoiceStatus(`Found ${foundProducts.length} products.`);
      }
    } catch (err) {
      setError(
        "Could not connect to the shopping service. Check that the Spring Boot backend and Python AI service are running.",
      );
      setVoiceStatus("Search failed. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(event) {
    event.preventDefault();
    searchProducts(message);
  }

  function startVoiceSearch() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        "Speech recognition is not supported in this browser. Please use Chrome or Edge.",
      );
      return;
    }

    if (shouldListenRef.current) return;

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
      setVoiceStatus("Listening... Tell me what you want to buy.");
    };

    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        if (event.results[i].isFinal) {
          const spokenText = event.results[i][0].transcript.trim();

          if (spokenText) {
            setMessage(spokenText);
            setVoiceStatus(`You said: "${spokenText}"`);
            searchProducts(spokenText);
          }
        }
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);

      if (event.error === "not-allowed") {
        shouldListenRef.current = false;
        setListening(false);
        setVoiceStatus("Microphone permission denied.");
      } else if (event.error !== "no-speech") {
        setVoiceStatus(`Voice error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      if (shouldListenRef.current) {
        try {
          recognition.start();
        } catch (err) {
          console.error("Could not restart speech recognition:", err);
        }
      } else {
        setListening(false);
        setVoiceStatus("Voice search stopped.");
      }
    };

    recognitionRef.current = recognition;
    shouldListenRef.current = true;

    try {
      recognition.start();
    } catch (err) {
      shouldListenRef.current = false;
      setListening(false);
      setVoiceStatus("Could not start the microphone.");
      console.error(err);
    }
  }

  function stopVoiceSearch() {
    shouldListenRef.current = false;

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    setListening(false);
    setVoiceStatus("Voice search stopped.");
  }

  useEffect(() => {
    return () => {
      shouldListenRef.current = false;

      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-icon">S</span>
          SmartCart
        </a>
        <span className="topbar-label">AI-powered shopping</span>
      </header>

      <main className="main">
        <section className="hero">
          <span className="eyebrow">YOUR SMART SHOPPING ASSISTANT</span>

          <h1>
            Shopping made <span>smarter.</span>
          </h1>

          <p>
            Tell us what you need. Discover products with help from AI-powered
            search and recommendations.
          </p>

          <form className="search-form" onSubmit={handleSearch}>
            <span className="search-icon">⌕</span>

            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Try 'snacks under 200 rupees'"
              aria-label="Search for products"
            />

            <button type="submit" disabled={loading || !message.trim()}>
              {loading ? "Searching..." : "Search"}
            </button>
          </form>

          <div className="voice-panel">
            <button
              type="button"
              className={`voice-button ${listening ? "voice-active" : ""}`}
              onClick={listening ? stopVoiceSearch : startVoiceSearch}
            >
              {listening ? "■ Stop listening" : "🎙 Start voice shopping"}
            </button>

            <p className="voice-status" aria-live="polite">
              {voiceStatus}
            </p>
          </div>

          <div className="suggestions">
            <span>Try:</span>

            {["Snacks under 200 rupees", "Biscuits", "Show me pasta"].map(
              (suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  onClick={() => searchProducts(suggestion)}
                >
                  {suggestion}
                </button>
              ),
            )}
          </div>
        </section>

        <section className="results">
          <div className="section-heading">
            <div>
              <span className="eyebrow">SMART PRODUCT DISCOVERY</span>
              <h2>{searched ? "Search results" : "Discover products"}</h2>
            </div>

            {searched && (
              <span className="result-count">{products.length} products</span>
            )}
          </div>

          {error && <div className="error">{error}</div>}

          {!searched && !error && (
            <div className="welcome-card">
              <div className="welcome-icon">✳</div>
              <h3>What are you looking for today?</h3>
              <p>
                Type your requirements or start the microphone to search using
                your voice.
              </p>
            </div>
          )}

          {loading && (
            <p className="message">Finding the best matching products...</p>
          )}

          {searched && !loading && !error && products.length === 0 && (
            <div className="welcome-card">
              <h3>No products found</h3>
              <p>Try a different search or change your requirements.</p>
            </div>
          )}

          {products.length > 0 && (
            <div className="product-grid">
              {products.map((product, index) => (
                <article
                  className="product-card"
                  key={
                    product.product_id ??
                    product.id ??
                    `${product.product_name ?? product.name ?? "product"}-${index}`
                  }
                >
                  <div className="product-art">
                    {product.image_url || product.image ? (
                      <img
                        src={product.image_url ?? product.image}
                        alt={product.product_name ?? product.name ?? "Product"}
                      />
                    ) : (
                      <span>🛒</span>
                    )}
                  </div>

                  <div className="product-info">
                    <span className="product-category">
                      {product.category ?? product.subcategory ?? "PRODUCT"}
                    </span>

                    <h3>
                      {product.product_name ??
                        product.name ??
                        product.title ??
                        product.product_id ??
                        "Product"}
                    </h3>

                    <p className="product-brand">
                      {product.brand ?? "SmartCart catalog"}
                    </p>

                    <div className="product-bottom">
                      <strong>
                        {product.price != null
                          ? `₹${product.price}`
                          : product.displayed_price != null
                            ? `₹${product.displayed_price}`
                            : "Price unavailable"}
                      </strong>

                      {product.rating != null && (
                        <span>★ {product.rating}</span>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer>SmartCart · Smarter choices, simpler shopping.</footer>
    </div>
  );
}

export default App;
