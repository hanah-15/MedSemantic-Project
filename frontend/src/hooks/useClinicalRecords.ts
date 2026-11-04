import { useEffect, useState } from 'react';
import { ApiError, apiGet } from '../lib/api';
import type { DomainSlug, Entity } from '../data/ontology';

export type LoadStatus = 'idle' | 'loading' | 'connected' | 'unavailable' | 'not-found' | 'error';
type LoadResult<T> = { key: string; status: LoadStatus; data: T | null };

const servicePaths = {
  patients: '/api/patients',
  conditions: '/api/conditions',
} as const;

type ClinicalDomain = keyof typeof servicePaths;

export function isClinicalDomain(domain?: string): domain is ClinicalDomain {
  return domain === 'patients' || domain === 'conditions';
}

/** Shared domain-specific transport; other teammates' pages remain unchanged. */
export function useClinicalResource<T>(key: string, path: string | null) {
  const [result, setResult] = useState<LoadResult<T>>({ key: '', status: 'idle', data: null });
  const [attempt, setAttempt] = useState(0);
  const retry = () => setAttempt(current => current + 1);

  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setResult({ key, status: 'loading', data: null });
    apiGet<T>(path, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ key, status: 'connected', data }); })
      .catch(error => {
        if (controller.signal.aborted) return;
        const status = error instanceof ApiError
          ? error.status === 404 ? 'not-found' : error.status === 503 ? 'unavailable' : 'error'
          : 'unavailable';
        setResult({ key, status, data: null });
      });
    return () => controller.abort();
  }, [key, path, attempt]);

  if (!path) return { data: null, status: 'idle' as LoadStatus, retry };
  if (result.key !== key) return { data: null, status: 'loading' as LoadStatus, retry };
  return { data: result.data, status: result.status, retry };
}

export function useClinicalCollection(domain?: DomainSlug | string, filters:Record<string,string> = {}) {
  const enabled = isClinicalDomain(domain);
  const query = new URLSearchParams(Object.entries(filters).filter(([,value])=>value.trim() !== '')).toString();
  const path = enabled ? servicePaths[domain] + (query ? '?'+query : '') : null;
  return useClinicalResource<Entity[]>(path ?? '', path);
}

export function useClinicalEntity(domain?: string, id?: string) {
  const enabled = isClinicalDomain(domain) && !!id;
  const path = enabled ? servicePaths[domain] + '/' + encodeURIComponent(id) : null;
  return useClinicalResource<Entity>(enabled ? `${domain}/${id}` : '', path);
}
