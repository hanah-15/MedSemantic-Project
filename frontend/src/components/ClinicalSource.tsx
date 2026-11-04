import type { LoadStatus } from '../hooks/useClinicalRecords';

export default function ClinicalSource({ status, retry, preview = false }: { status: LoadStatus; retry: () => void; preview?: boolean }) {
  const message = status === 'connected' ? 'Live ontology · Fuseki → FastAPI'
    : status === 'loading' ? 'Loading ontology records…'
    : status === 'not-found' ? 'Record not found in the live ontology'
    : status === 'error' ? 'The API could not load this record'
    : preview ? 'Preview records · FastAPI or Fuseki is unavailable'
    : 'FastAPI or Fuseki is unavailable';
  return <div className={'source-status source-' + status} role="status">
    <span>{message}</span>
    {['unavailable', 'error'].includes(status) && <button type="button" onClick={retry}>Retry connection</button>}
  </div>;
}
