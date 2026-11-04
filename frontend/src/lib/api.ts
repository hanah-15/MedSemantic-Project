/** Read-only FastAPI transport. Preview data is chosen and labeled by the UI. */
const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export class ApiError extends Error {
  constructor(public status: number) { super(`API error ${status}`); }
}
export async function apiGet<T>(path:string,signal?:AbortSignal):Promise<T>{
  const timeout = AbortSignal.timeout(15000);
  const response=await fetch(base+path,{signal:signal ? AbortSignal.any([signal,timeout]) : timeout});
  if(!response.ok) throw new ApiError(response.status);
  return response.json() as Promise<T>;
}
