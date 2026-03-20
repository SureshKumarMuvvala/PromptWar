import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 60000,
});

/**
 * POST /emergency/assess — multimodal triage
 */
export async function assessEmergency({ text, audio, image, latitude, longitude }) {
  const formData = new FormData();
  if (text) formData.append('text', text);
  if (audio) formData.append('audio', audio);
  if (image) formData.append('image', image);
  if (latitude != null) formData.append('latitude', latitude);
  if (longitude != null) formData.append('longitude', longitude);

  const response = await api.post('/emergency/assess', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * GET /hospitals — nearby hospital lookup
 */
export async function searchHospitals(lat, lng, radiusKm) {
  const params = { lat, lng };
  if (radiusKm) params.radius_km = radiusKm;
  const response = await api.get('/hospitals', { params });
  return response.data;
}

/**
 * GET /status — health check
 */
export async function checkStatus() {
  const response = await api.get('/status');
  return response.data;
}

export default api;
