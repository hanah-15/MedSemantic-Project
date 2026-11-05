import type { DomainSlug, Entity } from '../data/ontology';
import { apiGet } from './api';

export type OntologyProperty = {
  predicate: string;
  value: string;
  value_type: 'uri' | 'literal' | 'typed-literal';
  datatype?: string;
  language?: string;
};

export type OntologyRecord = {
  uri: string;
  label: string | null;
  description: string | null;
  properties: OntologyProperty[];
};

const domainPaths = {
  diseases: 'diseases',
  symptoms: 'symptoms',
} as const;

export type ClinicalDomain = keyof typeof domainPaths;

export function getLocalName(uri: string): string {
  const separator = Math.max(uri.lastIndexOf('#'), uri.lastIndexOf('/'));
  return decodeURIComponent(uri.slice(separator + 1));
}

export function toClinicalEntity(record: OntologyRecord, domain: ClinicalDomain): Entity {
  const id = getLocalName(record.uri);
  const properties: Record<string, string> = {};
  const relations: NonNullable<Entity['relations']> = [];

  for (const property of record.properties) {
    const predicate = getLocalName(property.predicate);
    if (property.value_type === 'uri') {
      const target = getLocalName(property.value);
      relations.push({ predicate, target });
      properties[predicate] = properties[predicate]
        ? `${properties[predicate]}, ${target}`
        : target;
    } else {
      properties[predicate] = properties[predicate]
        ? `${properties[predicate]}, ${property.value}`
        : property.value;
    }
  }

  return {
    id,
    name: record.label?.trim() || id,
    domain: domain as DomainSlug,
    type: domain === 'diseases' ? 'Maladie' : 'Symptome',
    description: record.description ?? '',
    properties,
    relations,
  };
}

export function listClinicalRecords(
  domain: ClinicalDomain,
  signal?: AbortSignal,
): Promise<OntologyRecord[]> {
  return apiGet<OntologyRecord[]>(`/api/${domainPaths[domain]}`, signal);
}

export function getClinicalRecord(
  domain: ClinicalDomain,
  id: string,
  signal?: AbortSignal,
): Promise<OntologyRecord> {
  return apiGet<OntologyRecord>(`/api/${domainPaths[domain]}/${encodeURIComponent(id)}`, signal);
}

export function listDiseasesForSymptom(
  symptomId: string,
  signal?: AbortSignal,
): Promise<OntologyRecord[]> {
  return apiGet<OntologyRecord[]>(
    `/api/diseases?symptom=${encodeURIComponent(symptomId)}`,
    signal,
  );
}
