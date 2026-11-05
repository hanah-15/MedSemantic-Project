import { isClinicalDomain, useClinicalCollection } from './useClinicalRecords';
import { isDiseaseDomain, useDiseaseCollection } from './useDiseaseRecords';
import { isSafetyDomain, useSafetyCollection } from './useSafetyRecords';
import { isResearchDomain, useResearchCollection } from './useResearchRecords';
import { useMedicationCollection } from './useMedicationRecord';
import { useMoleculeCollection } from './useMoleculeRecords';

export function useAtlasCollection(domain:string) {
  const clinical = useClinicalCollection(domain);
  const disease = useDiseaseCollection(domain);
  const safety = useSafetyCollection(domain);
  const research = useResearchCollection(domain);
  const medication = useMedicationCollection(domain === 'medications');
  const molecule = useMoleculeCollection(domain === 'molecules');
  return isClinicalDomain(domain) ? clinical : isDiseaseDomain(domain) ? disease : isSafetyDomain(domain) ? safety
    : isResearchDomain(domain) ? research : domain === 'medications' ? medication : molecule;
}
