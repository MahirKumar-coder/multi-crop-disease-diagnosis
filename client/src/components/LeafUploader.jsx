import React, { useState } from 'react';
import { predictDisease } from '../services/api';

const LeafUploader = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const response = await predictDisease(file);
      onUploadSuccess(response.data); // Axios se data receive karke parent ko pass karna[cite: 2]
    } catch (error) {
      alert("Error predicting disease.");
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