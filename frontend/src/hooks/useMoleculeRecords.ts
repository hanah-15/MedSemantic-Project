import type { Entity } from '../data/ontology';
import { useClinicalResource } from './useClinicalRecords';

export function useMoleculeCollection(enabled=true) {
  const path = enabled ? '/api/molecules' : null;
  return useClinicalResource<Entity[]>(path ?? '',path);
}
export function useMoleculeRecord(enabled:boolean,id?:string) {
  const path = enabled && id ? '/api/molecules/'+encodeURIComponent(id) : null;
  const result = useClinicalResource<Entity>(path ?? '',path);
  return {...result,entity:result.data};
}
