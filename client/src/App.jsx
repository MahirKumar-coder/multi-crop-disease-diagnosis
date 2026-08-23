import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Encyclopedia from './pages/Encyclopedia';

function App() {
  return (
    <Router>
      {/* Naya Background Image Setup */}
      <div 
        className="min-h-screen bg-cover bg-center bg-fixed relative z-0"
        style={{ 
          // Yahan maine ek sundar khet ki demo image lagayi hai. Aap is URL ko badal sakte hain.
          backgroundImage: "url('https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?q=80&w=2070&auto=format&fit=crop')" 
        }}
      >
        
        {/* Glass Effect Overlay (Taaki text clear padhne mein aaye) */}
        <div className="absolute inset-0 bg-white/80 backdrop-blur-[4px] -z-10"></div>

        <Navbar />
        
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/encyclopedia" element={<Encyclopedia />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;