export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = (import.meta.server && config.apiBaseServer) || config.public.apiBase
  return $fetch.create({ baseURL })
}
