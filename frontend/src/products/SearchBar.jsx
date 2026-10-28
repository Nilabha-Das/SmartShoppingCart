import React, { useState } from 'react';
import { Search, X } from 'lucide-react';

export const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSearch} className="relative w-full">
      <Search className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products by name, keyword, or category (e.g., 'Organic milk', 'Biscuits under ₹100')..."
        className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl pl-12 pr-10 py-3.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all shadow-lg"
      />
      {query && (
        <button
          type="button"
          onClick={() => {
            setQuery('');
            onSearch('');
          }}
          className="absolute right-4 top-3.5 text-gray-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </form>
  );
};