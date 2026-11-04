import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/medicaments';

export const medicamentService = {
  // Récupérer tous les médicaments
  getAll: async () => {
    const response = await axios.get(`${API_BASE_URL}/`);
    return response.data;
  },

  // Récupérer les détails d'un médicament et ses molécules par URI
  getDetailsByUri: async (uri) => {
    const response = await axios.get(`${API_BASE_URL}/details/${encodeURIComponent(uri)}`);
    return response.data;
  },

  // Récupérer les molécules par nom commercial
  getMoleculesByNom: async (nomCommercial) => {
    const response = await axios.get(`${API_BASE_URL}/${encodeURIComponent(nomCommercial)}`);
    return response.data;
  },

  // Créer un nouveau médicament
  create: async (data) => {
    const response = await axios.post(`${API_BASE_URL}/`, data);
    return response.data;
  },

  // Mettre à jour un médicament
  update: async (uri, data) => {
    const response = await axios.put(`${API_BASE_URL}/${encodeURIComponent(uri)}`, data);
    return response.data;
  },

  // Supprimer un médicament
  delete: async (uri) => {
    const response = await axios.delete(`${API_BASE_URL}/${encodeURIComponent(uri)}`);
    return response.data;
  }
};
