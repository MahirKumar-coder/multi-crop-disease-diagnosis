import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => (
  <nav className="bg-green-700 text-white shadow-md p-4">
    <div className="container mx-auto flex justify-between items-center">
      <Link to="/" className="text-xl font-bold flex items-center gap-2">🍃 CropCare AI</Link>
      <div className="flex gap-4 font-medium">
        <Link to="/" className="hover:text-green-200">Dashboard</Link>
        <Link to="/encyclopedia" className="hover:text-green-200">Encyclopedia</Link>
      </div>
    </div>
  </nav>
);

export default Navbar;