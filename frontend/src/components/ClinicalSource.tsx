import type { LoadStatus } from '../hooks/useClinicalRecords';

export default function ClinicalSource({ status, retry, preview = false }: { status: LoadStatus; retry: () => void; preview?: boolean }) {
  if (status === 'connected' || status === 'idle') return null;
  const message = status === 'loading' ? 'Loading records…'
    : status === 'not-found' ? 'Record not found.'
    : status === 'error' ? 'Unable to load records. Please try again.'
    : preview ? 'Showing sample records. Current records are unavailable.'
    : 'Records are temporarily unavailable.';
  return <div className={'source-status source-' + status} role="status">
    <span>{message}</span>
    {['unavailable', 'error'].includes(status) && <button type="button" onClick={retry}>Try again</button>}
  </div>;
}
