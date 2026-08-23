import axios from 'axios'; // API requests via Axios[cite: 2]

const baseURL = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : 'https://multi-crop-disease-diagnosis.onrender.com');

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