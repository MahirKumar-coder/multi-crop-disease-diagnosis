import axios from 'axios'; 

// Hamesha live Render backend ko point karega
const baseURL = import.meta.env.VITE_API_URL || 'https://multi-crop-disease-diagnosis.onrender.com';

const API = axios.create({
  baseURL: baseURL,
});

export const predictDisease = (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  return API.post('/api/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getAllDiseases = () => API.get('/api/diseases');