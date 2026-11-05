import type { Entity } from '../data/ontology';
import { useClinicalResource } from './useClinicalRecords';

export type EtudeApi = {
  id: string;
  iri: string;
  type_etude?: string | null;
  medicament_id?: string | null;
  maladie_id?: string | null;
  phase?: number | null;
  annee?: number | null;
  participants?: number | null;
  comparative?: boolean | null;
  resultats?: ResultatApi[];
};

export type ResultatApi = {
  id: string;
  iri: string;
  type_resultat?: string | null;
  valeur?: number | null;
  unite?: string | null;
  etude_id?: string | null;
  type_etude?: string | null;
  medicament_id?: string | null;
};

export type StatEtudeApi = {
  type_etude: string;
  nombre_etudes: number;
  moyenne_participants?: number | null;
};

export type StatResultatApi = {
  type_resultat: string;
  nombre_resultats: number;
};

export function mapEtudeToEntity(e: EtudeApi): Entity {
  const props: Record<string, string> = {};
  if (e.phase != null) props.phaseEssai = String(e.phase);
  if (e.participants != null) props.nombreParticipants = String(e.participants);
  if (e.annee != null) props.anneePublication = String(e.annee);
  if (e.comparative != null) props.estComparative = String(e.comparative);
  const rels: {predicate: string; target: string}[] = [];
  if (e.medicament_id) rels.push({predicate: 'testeMedicament', target: e.medicament_id});
  if (e.maladie_id) rels.push({predicate: 'porteSurMaladie', target: e.maladie_id});
  for (const result of e.resultats ?? []) rels.push({predicate: 'aPourResultat', target: result.id});
  return {
    id: e.id,
    name: e.id.replaceAll('_', ' '),
    domain: 'studies',
    type: e.type_etude ?? 'EtudeClinique',
    description: `${e.type_etude ?? 'Étude clinique'}${e.medicament_id ? ` portant sur ${e.medicament_id}` : ''}${e.annee ? ` (${e.annee})` : ''}`,
    properties: props,
    relations: rels,
  };
}

export function mapResultatToEntity(r: ResultatApi): Entity {
  const props: Record<string, string> = {};
  if (r.valeur != null) props.valeurMesuree = String(r.valeur);
  if (r.unite) props.uniteMesure = r.unite;
  if (r.type_etude) props.typeEtudeAssociee = r.type_etude;
  const rels: {predicate: string; target: string}[] = [];

  return {
    id: r.id,
    name: r.id.replaceAll('_', ' '),
    domain: 'results',
    type: r.type_resultat ?? 'ResultatClinique',
    description: r.valeur != null && r.unite ? `Mesure clinique : ${r.valeur} ${r.unite}` : 'Résultat clinique',
    incomingRelations: r.etude_id ? [{predicate:'aPourResultat',source:r.etude_id,sourceDomain:'studies'}] : [],
    properties: props,
    relations: rels,
  };
}

export function isResearchDomain(domain?: string): domain is 'studies'|'results' {
  return domain === 'studies' || domain === 'results';
}

export function useResearchCollection(domain?:string) {
  const path = isResearchDomain(domain) ? domain === 'studies' ? '/etudes/' : '/resultats/' : null;
  const result = useClinicalResource<(EtudeApi|ResultatApi)[]>(path ?? '',path);
  return {...result,data:result.data?.map(record=>domain === 'studies' ? mapEtudeToEntity(record as EtudeApi) : mapResultatToEntity(record as ResultatApi)) ?? null};
}

export function useResearchRecord(domain?: string, id?: string) {
  const path = isResearchDomain(domain) && id ? (domain === 'studies' ? '/etudes/' : '/resultats/')+encodeURIComponent(id) : null;
  const resource = useClinicalResource<EtudeApi|ResultatApi>(path ?? '',path);
  const entity = resource.data ? (domain === 'studies' ? mapEtudeToEntity(resource.data as EtudeApi) : mapResultatToEntity(resource.data as ResultatApi)) : undefined;
  if (entity && resource.data) entity.properties = {IRI:resource.data.iri,...entity.properties};
  return {...resource,entity};
}
