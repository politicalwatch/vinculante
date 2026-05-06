/**
 * Golden-path e2e test: home → target → analysis → section → match selection
 *
 * Prerequisites:
 *   - Engine running on localhost:8000 (docker compose up)
 *   - DB has at least one target with sections that have matches
 *
 * Note: The final highlight (<mark> in selected section content) is covered by unit tests
 * for highlight.ts. The e2e flow stops at match selection — verifying the routing,
 * data fetching, tab switching, section selection, and match selection wiring.
 */

import { test, expect } from '@playwright/test'

test('navigates from home through target analysis and selects a match', async ({ page }) => {
  // Surface page-level errors so failures show the actual cause
  page.on('pageerror', err => console.log('[page:error]', err.message))

  // 1. Home loads target cards
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // First TargetCard: direct child of the responsive grid in <main>, contains "propuestas"
  const firstCard = page
    .locator('main [class*="grid"] > *')
    .filter({ hasText: 'propuestas' })
    .first()
  await expect(firstCard).toBeVisible({ timeout: 10_000 })

  // 2. Navigate into a target.
  // dispatchEvent('click') fires the DOM event directly — bypasses any pointer intercepts
  // (Nuxt DevTools overlay) that can swallow .click() in headless.
  await Promise.all([
    page.waitForURL(/\/targets\/\d+/, { timeout: 10_000 }),
    firstCard.dispatchEvent('click')
  ])

  // 3. Switch to the Análisis tab
  await page.getByRole('tab', { name: 'Análisis' }).click()

  // 4. Find the first matchable section that has a match-count badge.
  //    SectionItem renders matchable sections as <button data-section-id="...">.
  const sectionWithMatches = page
    .locator('button[data-section-id]')
    .filter({ has: page.locator('span').filter({ hasText: /^\d+$/ }) })
    .first()
  await expect(sectionWithMatches).toBeVisible({ timeout: 15_000 })

  // 5. Select the section
  await sectionWithMatches.click()

  // The selected section should pick up the active styling (bg-primary/10).
  await expect(sectionWithMatches).toHaveClass(/bg-primary/, { timeout: 5_000 })

  // 6. Wait for a MatchCard (UCard with cursor-pointer + Alto/Medio degree badge)
  const matchCard = page
    .locator('main')
    .locator('[class*="cursor-pointer"]')
    .filter({ hasText: /Alto|Medio/ })
    .first()
  await expect(matchCard).toBeVisible({ timeout: 10_000 })

  // 7. Select the match
  await matchCard.scrollIntoViewIfNeeded()
  await matchCard.evaluate(el => (el as HTMLElement).click())

  // The selected match card gets the ring-primary indicator.
  await expect(matchCard).toHaveClass(/ring-primary/, { timeout: 5_000 })
})
