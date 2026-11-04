const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export interface Molecule {
  nom: string;
  type_molecule: string; // "Principe actif" | "Excipient"
  formule_chimique?: string | null;
}

export interface Medicament {
  uri: string;
  nom_commercial: string;
  dosage: string;
  forme_galenique: string;
  molecules?: Molecule[];
}

export interface MedicamentCreate {
  uri?: string;
  nom_commercial: string;
  dosage: string;
  forme_galenique: string;
  molecules?: Molecule[];
}

export interface MedicamentUpdate {
  nom_commercial?: string;
  dosage?: string;
  forme_galenique?: string;
}

export interface NlpSearchResponse {
  query: string;
  intention: 'composition' | 'dosage' | 'forme_galenique' | 'inconnu';
  medicament: string | null;
  reponse: string;
  data?: Array<{
    nom: string;
    type: string;
    formule?: string | null;
  }>;
}

export const medicamentApi = {
  // 1. READ: Liste de tous les médicaments
  async getAll(): Promise<Medicament[]> {
    const res = await fetch(`${BASE_URL}/api/medicaments/`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  // 2. READ: Composition chimique d'un médicament (molécules)
  async getMolecules(nomCommercial: string): Promise<Molecule[]> {
    const res = await fetch(`${BASE_URL}/api/medicaments/${encodeURIComponent(nomCommercial)}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  // 3. CREATE: Ajouter un médicament
  async create(data: MedicamentCreate): Promise<Medicament> {
    const res = await fetch(`${BASE_URL}/api/medicaments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Erreur lors de la création');
    }
    return res.json();
  },

  // 4. UPDATE: Modifier un médicament
  async update(uri: string, data: MedicamentUpdate): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/api/medicaments/${encodeURIComponent(uri)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Erreur lors de la modification');
    }
    return res.json();
  },

  // 5. DELETE: Supprimer un médicament
  async delete(uri: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/api/medicaments/${encodeURIComponent(uri)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Erreur lors de la suppression');
    }
    return res.json();
  },

  // 6. RECHERCHE NLP INTELLIGENTE
  async askNlp(question: string): Promise<NlpSearchResponse> {
    const res = await fetch(`${BASE_URL}/api/recherche/?q=${encodeURIComponent(question)}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }
};
