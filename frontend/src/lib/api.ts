/** Future FastAPI integration. The sample UI uses local demo data until endpoints exist. */
const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export async function apiGet<T>(path:string,signal?:AbortSignal):Promise<T>{
  const response=await fetch(base+path,{signal});
  if(!response.ok) throw new Error(`API error ${response.status}`);
  return response.json() as Promise<T>;
}
