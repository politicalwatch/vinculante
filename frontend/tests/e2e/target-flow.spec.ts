/**
 * Golden-path e2e tests for a law: the catalogue, the tab navigation and each
 * tab (Resumen, Vinculaciones, Propuestas) opened from its own URL.
 *
 * Prerequisites:
 *   - Engine running (docker compose up); E2E_API_BASE overrides http://localhost:8000
 *   - DB has at least one target with accepted (alto/medio) matches
 *
 * Selectors rely on roles and aria-/data- attributes, not styling classes.
 */

import { test, expect, type Page } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE ?? 'http://localhost:8000'

let targetId: number

test.beforeAll(async ({ request }) => {
  const response = await request.get(`${API_BASE}/targets`)
  expect(response.ok(), `GET ${API_BASE}/targets`).toBeTruthy()
  const targets: Array<{ id: number, incorporated: number }> = await response.json()
  const target = targets.find(item => item.incorporated > 0)
  expect(target, 'a target with accepted matches').toBeDefined()
  targetId = target!.id
})

test.beforeEach(({ page }) => {
  // Surface page-level errors so failures show the actual cause
  page.on('pageerror', err => console.log('[page:error]', err.message))
})

/**
 * Opens a page and waits for hydration: the SSR markup is visible before Vue attaches
 * its listeners, so earlier clicks do nothing. Then rejects analytics if the cookie
 * banner shows up, so it never covers a click.
 */
async function open(page: Page, path: string) {
  await page.goto(path)
  await page.waitForFunction(() => {
    const app = (document.querySelector('#__nuxt') as { __vue_app__?: { $nuxt?: { isHydrating?: boolean } } } | null)?.__vue_app__
    return app?.$nuxt?.isHydrating === false
  })
  const reject = page.locator('.cookieControl__Bar').getByRole('button', { name: 'Rechazar', exact: true })
  if (await reject.isVisible({ timeout: 2_000 }).catch(() => false)) {
    await reject.click()
  }
}

function viewNav(page: Page) {
  return page.getByRole('navigation', { name: 'Vista' })
}

test('navigates from the catalogue through every tab', async ({ page }) => {
  await open(page, '/')
  await expect(page.getByRole('heading', { name: 'Documentos analizados' })).toBeVisible()

  await page.locator(`a[href="/${targetId}"]`).first().click()
  await expect(page).toHaveURL(new RegExp(`/${targetId}$`))
  await expect(viewNav(page).getByRole('link', { name: 'Resumen' })).toHaveAttribute('aria-current', 'page')

  await viewNav(page).getByRole('link', { name: 'Vinculaciones' }).click()
  await expect(page).toHaveURL(new RegExp(`/${targetId}/detalle\\?vista=vinculaciones$`))
  await expect(viewNav(page).getByRole('link', { name: 'Vinculaciones' })).toHaveAttribute('aria-current', 'page')

  await viewNav(page).getByRole('link', { name: 'Propuestas' }).click()
  await expect(page).toHaveURL(new RegExp(`/${targetId}/detalle\\?vista=propuestas$`))
  await expect(viewNav(page).getByRole('link', { name: 'Propuestas' })).toHaveAttribute('aria-current', 'page')

  await viewNav(page).getByRole('link', { name: 'Resumen' }).click()
  await expect(page).toHaveURL(new RegExp(`/${targetId}$`))
})

test('Resumen shows the law summary and links to the linkages', async ({ page }) => {
  await open(page, `/${targetId}`)

  await expect(page.getByRole('heading', { level: 1 })).not.toBeEmpty()

  // The scroll-spy marks the first section on load; a nav link jumps to its section.
  // (The last sections may never reach the spy offset, so aria-current is only checked on load.)
  const sections = page.getByRole('navigation', { name: 'Secciones del resumen' }).getByRole('link')
  await expect(sections.first()).toHaveAttribute('aria-current', 'true')
  const last = sections.last()
  const hash = await last.getAttribute('href')
  await last.click()
  await expect(page).toHaveURL(new RegExp(`${hash}$`))
  await expect(page.locator(hash!)).toBeInViewport()

  await page.getByRole('link', { name: '+ Ver todas las vinculaciones' }).click()
  await expect(page).toHaveURL(new RegExp(`/${targetId}/detalle`))
})

test('Vinculaciones selects an article and shows its linked proposals', async ({ page }) => {
  await open(page, `/${targetId}/detalle?vista=vinculaciones`)

  // Article cards: the select button is the one with aria-pressed
  const articles = page.locator('article button[aria-pressed]')
  await expect(articles.first()).toBeVisible({ timeout: 15_000 })

  const article = articles.first()
  await article.click()
  await expect(article).toHaveAttribute('aria-pressed', 'true')

  // Proposals not linked to the selected article fade out and become aria-hidden
  const linked = page.locator('[data-proposal-id][aria-hidden="false"] [role="button"][aria-expanded]')
  await expect(linked.first()).toBeVisible({ timeout: 10_000 })

  const proposal = linked.first()
  await proposal.click()
  await expect(proposal).toHaveAttribute('aria-expanded', 'true')
})

test('Propuestas groups proposals and opens one with its linked articles', async ({ page }) => {
  await open(page, `/${targetId}/detalle?vista=propuestas`)

  const proposals = page.locator('[data-proposal-id] [role="button"][aria-expanded]')
  await expect(proposals.first()).toBeVisible({ timeout: 15_000 })

  const byLinkCount = page.getByRole('button', { name: 'Nº de artículos' })
  await byLinkCount.click()
  await expect(byLinkCount).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('button', { name: 'Sin agrupar' })).toHaveAttribute('aria-pressed', 'false')

  // A proposal without linked articles only expands; one with links opens its detail
  await proposals.filter({ hasText: /vinc\. con/ }).first().click()
  await expect(page.getByRole('heading', { name: 'Artículos vinculados' })).toBeVisible()

  await page.getByRole('button', { name: 'Volver' }).click()
  await expect(page.getByRole('heading', { name: 'Artículos vinculados' })).toBeHidden()
  await expect(proposals.first()).toBeVisible()
})
