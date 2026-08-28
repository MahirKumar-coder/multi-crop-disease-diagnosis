import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-green-700 text-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex justify-between items-center">
        
        {/* Logo Section */}
        <Link to="/" className="text-2xl font-bold flex items-center gap-2">
          {/* Exact path updated here */}
          <img 
            src="/sample_leaves/favicon.ico" 
            alt="CropCare Logo" 
            className="w-8 h-8 object-contain bg-white/20 rounded-full p-1" 
          />
          <span className="tracking-tight mt-1">CropCare AI</span>
        </Link>
        
        {/* Navigation Links */}
        <div className="flex gap-6 font-medium">
          <Link to="/" className="hover:text-green-200 transition-colors">
            Dashboard
          </Link>
          <Link to="/encyclopedia" className="hover:text-green-200 transition-colors">
            Encyclopedia
          </Link>
        </div>
        
      </div>
    </nav>
  );
};

export default Navbar;