import axios from 'axios'; // API requests via Axios[cite: 2]

const API = axios.create({
  baseURL: 'https://multi-crop-disease-diagnosis.onrender.com', // Production URL
});

export const predictDisease = (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  return API.post('/api/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getAllDiseases = () => API.get('/api/diseases');