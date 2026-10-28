import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({ items: [], subtotal: 0, total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const res = await api.get('/cart');
      setCart(res.data);
    } catch (err) {
      // Fallback mock cart if backend unlinked
      if (!cart.items.length) {
        setCart({ items: [], subtotal: 0, total: 0 });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const addToCart = async (product, quantity = 1) => {
    try {
      setLoading(true);
      let res;
      try {
        res = await api.post('/cart/add', { productId: product.id || product._id, quantity });
        setCart(res.data);
      } catch (err) {
        // Local state update fallback
        setCart((prev) => {
          const existingIndex = prev.items.findIndex(
            (item) => (item.product.id || item.product._id) === (product.id || product._id)
          );
          let updatedItems = [...prev.items];
          if (existingIndex > -1) {
            updatedItems[existingIndex].quantity += quantity;
          } else {
            updatedItems.push({ product, quantity });
          }
          const subtotal = updatedItems.reduce((acc, i) => acc + i.product.price * i.quantity, 0);
          return { items: updatedItems, subtotal, total: subtotal };
        });
      }
    } catch (err) {
      setError('Failed to add item to cart');
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId) => {
    try {
      setLoading(true);
      try {
        const res = await api.delete(`/cart/item/${productId}`);
        setCart(res.data);
      } catch (err) {
        setCart((prev) => {
          const updatedItems = prev.items.filter(
            (item) => (item.product.id || item.product._id) !== productId
          );
          const subtotal = updatedItems.reduce((acc, i) => acc + i.product.price * i.quantity, 0);
          return { items: updatedItems, subtotal, total: subtotal };
        });
      }
    } catch (err) {
      setError('Failed to remove item');
    } finally {
      setLoading(false);
    }
  };

  return (
    <CartContext.Provider value={{ cart, loading, error, addToCart, removeFromCart, fetchCart }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);