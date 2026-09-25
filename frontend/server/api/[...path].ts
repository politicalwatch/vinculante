/**
 * Same-origin proxy to the engine, so the browser never calls it directly
 * (avoids mixed content when the site is served over HTTPS). Enabled by
 * setting `NUXT_PUBLIC_API_BASE=/api` and `NUXT_API_BASE_SERVER` to the
 * engine's internal URL.
 */
export default defineEventHandler((event) => {
  const { apiBaseServer } = useRuntimeConfig(event)
  if (!apiBaseServer) {
    throw createError({ statusCode: 404 })
  }
  const path = getRouterParam(event, 'path') ?? ''
  const { search } = getRequestURL(event)
  return proxyRequest(event, `${apiBaseServer.replace(/\/$/, '')}/${path}${search}`)
})
