import React, { useEffect, useState } from 'react';
import { getAllDiseases } from '../services/api';

const Encyclopedia = () => {
  const [diseases, setDiseases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Naya state: Kaunsi bimari par click kiya gaya hai (Popup ke liye)
  const [selectedDisease, setSelectedDisease] = useState(null);

  // Fallback data in case the API is down
  const fallbackData = [
    { 
      name: "Apple Scab", 
      type: "Fungal",
      description: "A fungal disease that affects apple trees, causing dark, scabby lesions on leaves and fruit.",
      treatment: "Use organic fungicides and clear fallen leaves."
    },
    { 
      name: "Corn Northern Leaf Blight", 
      type: "Fungal",
      description: "Causes large, cigar-shaped lesions on corn leaves, reducing yield.",
      treatment: "Plant resistant hybrids and practice crop rotation."
    },
    { 
      name: "Tomato Early Blight", 
      type: "Fungal",
      description: "Causes 'bullseye' spots on lower leaves of tomato plants.",
      treatment: "Ensure good air circulation and apply copper-based fungicides."
    },
    { 
      name: "Potato Late Blight", 
      type: "Oomycete",
      description: "A devastating disease that causes rapid decaying of potato leaves and tubers (caused the Irish Potato Famine).",
      treatment: "Destroy infected plants immediately and use specific late-blight fungicides."
    }
  ];

  useEffect(() => {
    getAllDiseases()
      .then(res => {
        const data = Array.isArray(res.data) ? res.data : res.data.diseases || fallbackData;
        setDiseases(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("API Error:", err);
        setError("Could not connect to the database. Showing offline sample data.");
        setDiseases(fallbackData);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto relative">
      <h1 className="text-3xl font-bold text-green-700 mb-6">Disease Encyclopedia</h1>
      
      {loading && <p className="text-gray-500">Loading encyclopedia data...</p>}
      
      {error && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded shadow-sm">
          <p className="font-bold">Notice</p>
          <p>{error}</p>
        </div>
      )}

      {/* Cards Grid */}
      {!loading && diseases.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {diseases.map((disease, idx) => (
            <div 
              key={idx} 
              onClick={() => setSelectedDisease(disease)} // Click karne par popup set hoga
              className="bg-white p-5 shadow-sm rounded-lg border-l-4 border-green-500 hover:shadow-xl transition-all cursor-pointer transform hover:-translate-y-1 relative group"
            >
              <h3 className="font-bold text-lg text-gray-800 group-hover:text-green-700 transition-colors">{disease.name}</h3>
              {disease.type && <p className="text-sm text-gray-500 mt-1">Type: {disease.type}</p>}
              
              {/* Naya 'Click to view' text jo hover karne par highlight hoga */}
              <p className="text-xs text-green-600 mt-3 font-semibold flex items-center gap-1 opacity-70 group-hover:opacity-100">
                Click for details <span>&rarr;</span>
              </p>
            </div>
          ))}
        </div>
      )}
      
      {!loading && diseases.length === 0 && !error && (
         <p className="text-gray-500">No diseases found in the database.</p>
      )}

      {/* 🚀 NAYA POPUP (MODAL) COMPONENT 🚀 */}
      {selectedDisease && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg relative animate-[fadeIn_0.2s_ease-out]">
            {/* Close Button (X) */}
            <button 
              onClick={() => setSelectedDisease(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-red-500 hover:bg-red-50 w-8 h-8 rounded-full flex items-center justify-center font-bold text-xl transition-colors"
            >
              &times;
            </button>
            
            <h2 className="text-2xl font-bold text-gray-800 mb-2 pr-8">{selectedDisease.name}</h2>
            
            <span className="inline-block bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full mb-6 font-semibold border border-green-200">
              {selectedDisease.type || "Unknown Type"}
            </span>
            
            <div className="space-y-4 text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-100">
              <p>
                <strong className="block text-gray-900 mb-1 text-base">Description:</strong> 
                {selectedDisease.description || "Detailed description is not available in the database right now."}
              </p>
              <p>
                <strong className="block text-gray-900 mb-1 text-base">Recommended Action:</strong> 
                {selectedDisease.treatment || "Please consult a local agricultural expert."}
              </p>
            </div>
            
            <button 
              onClick={() => setSelectedDisease(null)}
              className="mt-6 w-full bg-green-600 text-white py-2.5 rounded-lg hover:bg-green-700 transition font-medium shadow-md hover:shadow-lg"
            >
              Close Information
            </button>
          </div>

        </div>
      )}
    </div>
  );
};

export default Encyclopedia;