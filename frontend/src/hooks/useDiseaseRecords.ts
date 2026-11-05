import { useClinicalResource } from './useClinicalRecords';
import { toClinicalEntity, type ClinicalDomain, type OntologyRecord } from '../lib/ontologyApi';

export function isDiseaseDomain(domain?: string): domain is ClinicalDomain {
  return domain === 'diseases' || domain === 'symptoms';
}

export function useDiseaseCollection(domain?: string) {
  const path = isDiseaseDomain(domain) ? '/api/'+domain : null;
  const resource = useClinicalResource<OntologyRecord[]>(path ?? '',path);
  return {...resource,data:resource.data && isDiseaseDomain(domain) ? resource.data.map(record=>toClinicalEntity(record,domain)) : null};
}

export function useDiseaseRecord(domain?: string,id?: string) {
  const path = isDiseaseDomain(domain) && id ? '/api/'+domain+'/'+encodeURIComponent(id) : null;
  const resource = useClinicalResource<OntologyRecord>(path ?? '',path);
  const incomingPath = domain === 'symptoms' && id ? '/api/diseases?symptom='+encodeURIComponent(id) : null;
  const incoming = useClinicalResource<OntologyRecord[]>(incomingPath ?? '',incomingPath);
  const entity = resource.data && isDiseaseDomain(domain) ? toClinicalEntity(resource.data,domain) : undefined;
  if (entity) entity.incomingRelations = (incoming.data ?? []).map(record=>({predicate:'presenteSymptome',source:toClinicalEntity(record,'diseases').id,sourceDomain:'diseases'}));
  return {...resource,entity,incoming,retry:()=>{resource.retry();incoming.retry();}};
}
