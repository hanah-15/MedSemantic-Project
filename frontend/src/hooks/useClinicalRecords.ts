import { useEffect, useState } from 'react';
import { apiGet } from '../lib/api';
import type { DomainSlug, Entity } from '../data/ontology';

type LoadStatus = 'idle' | 'loading' | 'connected' | 'unavailable';
type LoadResult<T> = { key: string; status: LoadStatus; data: T | null };

const servicePaths = {
  patients: '/api/patients',
  conditions: '/api/conditions',
} as const;

type ClinicalDomain = keyof typeof servicePaths;

function isClinicalDomain(domain?: string): domain is ClinicalDomain {
  return domain === 'patients' || domain === 'conditions';
}

/** Shared domain-specific transport; other teammates' pages remain unchanged. */
function useClinicalResource<T>(key: string, path: string | null) {
  const [result, setResult] = useState<LoadResult<T>>({ key: '', status: 'idle', data: null });

  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setResult({ key, status: 'loading', data: null });
    apiGet<T>(path, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ key, status: 'connected', data }); })
      .catch(() => { if (!controller.signal.aborted) setResult({ key, status: 'unavailable', data: null }); });
    return () => controller.abort();
  }, [key, path]);

  if (!path) return { data: null, status: 'idle' as LoadStatus };
  if (result.key !== key) return { data: null, status: 'loading' as LoadStatus };
  return { data: result.data, status: result.status };
}

export function useClinicalCollection(domain?: DomainSlug | string) {
  const enabled = isClinicalDomain(domain);
  return useClinicalResource<Entity[]>(enabled ? domain : '', enabled ? servicePaths[domain] : null);
}

export function useClinicalEntity(domain?: string, id?: string) {
  const enabled = isClinicalDomain(domain) && !!id;
  const path = enabled ? servicePaths[domain] + '/' + encodeURIComponent(id) : null;
  return useClinicalResource<Entity>(enabled ? `${domain}/${id}` : '', path);
}
