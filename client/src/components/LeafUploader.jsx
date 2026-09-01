import React, { useState } from 'react';
import { predictDisease } from '../services/api';

const LeafUploader = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const originalUrl = URL.createObjectURL(file);
      const response = await predictDisease(file);
      onUploadSuccess({ ...response.data, original_url: originalUrl }); // Pass response data and locally generated URL[cite: 2]
    } catch (error) {
      console.error("Prediction failed:", error);
      const msg = error.response?.data?.detail || 
        "Failed to connect to backend server. If using Render, the free instance might be waking up (cold start) or redeploying. Please check server logs and try again.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-2 border-dashed border-green-500 p-8 text-center rounded-lg bg-white max-w-md mx-auto">
      <h3 className="font-bold mb-4 text-gray-700">Drag & Drop Leaf Image</h3>
      <input type="file" accept="image/*" onChange={handleUpload} disabled={loading} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:bg-green-50 file:text-green-700" />
      {loading && <p className="text-green-600 mt-4 animate-pulse">Analyzing with EfficientNet...</p>}
    </div>
  );
};

export default LeafUploader;