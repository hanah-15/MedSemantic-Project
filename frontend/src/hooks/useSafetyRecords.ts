import type { Entity } from '../data/ontology';
import { useClinicalResource } from './useClinicalRecords';

type Related = {id:string;iri:string};
export type SafetyRecord = {
  id:string; iri:string; label?:string|null; type_effet?:string|null; type_ci?:string|null;
  frequence?:string|null; gravite?:string|null; description?:string|null;
  symptome_id?:string|null; condition_id?:string|null; medicaments_lies?:string[];
  symptomes?:Related[]; medicaments?:Related[];
  conditions_concernees?:Related[]; medicaments_concernes?:Related[];
};

export function isSafetyDomain(domain?:string):domain is 'side-effects'|'contraindications' {
  return domain === 'side-effects' || domain === 'contraindications';
}
export function safetyPath(domain:string) {
  return domain === 'side-effects' ? '/api/effets-secondaires' : '/api/contre-indications';
}
export function safetyToEntity(record:SafetyRecord,domain:'side-effects'|'contraindications'):Entity {
  const properties:Record<string,string> = {};
  if (record.frequence) properties.frequenceEffet = record.frequence;
  if (record.gravite) properties.gravite = record.gravite;
  const effects = domain === 'side-effects';
  const targets = effects ? record.symptomes?.map(item=>item.id) ?? (record.symptome_id ? [record.symptome_id] : [])
    : record.conditions_concernees?.map(item=>item.id) ?? (record.condition_id ? [record.condition_id] : []);
  const meds = record.medicaments?.map(item=>item.id) ?? record.medicaments_concernes?.map(item=>item.id) ?? record.medicaments_lies ?? [];
  return {id:record.id,name:record.label || record.id.replaceAll('_',' '),domain,
    type:record.type_effet ?? record.type_ci ?? (effects ? 'EffetSecondaire' : 'ContreIndication'),
    description:record.description || (effects ? 'Recorded side effect' : 'Recorded contraindication'),properties,
    relations:targets.map(target=>({predicate:effects ? 'manifesteSymptome' : 'concerneCondition',target})),
    incomingRelations:meds.map(source=>({predicate:effects ? 'provoque' : 'aPourContreIndication',source,sourceDomain:'medications'})),
  };
}
export function useSafetyCollection(domain?:string,filters:Record<string,string>={}) {
  const params = new URLSearchParams(Object.entries(filters).filter(([,value])=>!!value)).toString();
  const path = isSafetyDomain(domain) ? safetyPath(domain)+(params ? '?'+params : '') : null;
  const result = useClinicalResource<SafetyRecord[]>(path ?? '',path);
  return {...result,data:result.data && isSafetyDomain(domain) ? result.data.map(record=>safetyToEntity(record,domain)) : null};
}
export function useSafetyRecord(domain?:string,id?:string) {
  const path = isSafetyDomain(domain) && id ? safetyPath(domain)+'/'+encodeURIComponent(id) : null;
  const result = useClinicalResource<SafetyRecord>(path ?? '',path);
  return {...result,entity:result.data && isSafetyDomain(domain) ? safetyToEntity(result.data,domain) : undefined};
}
