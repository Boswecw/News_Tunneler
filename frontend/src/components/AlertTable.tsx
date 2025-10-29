import { createSignal, For } from 'solid-js'
import type { Article } from '../lib/store'
import type { ArticlePlan } from '../lib/api'
import { analyzeArticle, fetchPlan } from '../lib/api'
import AlertRow from './AlertRow'
import PlanDrawer from './PlanDrawer'

interface AlertTableProps {
  articles: Article[]
  isLoading?: boolean
}

export default function AlertTable(props: AlertTableProps) {
  const [page, setPage] = createSignal(0)
  const itemsPerPage = 20
  const [drawerOpen, setDrawerOpen] = createSignal(false)
  const [currentPlan, setCurrentPlan] = createSignal<ArticlePlan | null>(null)
  const [planLoading, setPlanLoading] = createSignal(false)

  const paginatedArticles = () => {
    const start = page() * itemsPerPage
    return props.articles.slice(start, start + itemsPerPage)
  }

  const totalPages = () => Math.ceil(props.articles.length / itemsPerPage)

  const handleAnalyze = async (articleId: number) => {
    try {
      setPlanLoading(true)
      setDrawerOpen(true)
      setCurrentPlan(null)

      // Trigger analysis
      await analyzeArticle(articleId)

      // Poll for the plan with retries (OpenAI can take 30-40 seconds)
      const maxRetries = 20 // 20 retries * 3 seconds = 60 seconds max
      let retries = 0
      let plan = null

      while (retries < maxRetries && !plan) {
        await new Promise(resolve => setTimeout(resolve, 3000)) // Wait 3 seconds between retries

        try {
          plan = await fetchPlan(articleId)
          setCurrentPlan(plan)
          break
        } catch (error) {
          retries++
          console.log(`Waiting for analysis... (attempt ${retries}/${maxRetries})`)

          if (retries >= maxRetries) {
            throw new Error('Analysis timed out. Please try again.')
          }
        }
      }
    } catch (error) {
      console.error('Error analyzing article:', error)
      alert('Analysis failed or timed out. The article may still be processing. Please try refreshing in a moment.')
    } finally {
      setPlanLoading(false)
    }
  }

  const closeDrawer = () => {
    setDrawerOpen(false)
    setCurrentPlan(null)
  }

  return (
    <div class="card">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="w-full">
          <thead class="bg-white/40 dark:bg-white/5 backdrop-blur-md">
            <tr>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Title
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Summary
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Source
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Ticker
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Score
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Published
              </th>
              <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {props.isLoading && (
              <tr>
                <td colSpan={7} class="px-4 py-12 text-center">
                  <div class="flex flex-col items-center justify-center">
                    <div class="spinner h-10 w-10 mb-3"></div>
                    <p class="text-gray-600 dark:text-gray-400 font-medium">Loading articles...</p>
                  </div>
                </td>
              </tr>
            )}
            {!props.isLoading && paginatedArticles().length === 0 && (
              <tr>
                <td colSpan={7} class="px-4 py-12 text-center">
                  <div class="flex flex-col items-center justify-center">
                    <svg class="w-16 h-16 text-gray-400 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p class="text-gray-600 dark:text-gray-400 font-medium">No articles found</p>
                    <p class="text-sm text-gray-500 dark:text-gray-500 mt-1">Try adjusting your filters</p>
                  </div>
                </td>
              </tr>
            )}
            <For each={paginatedArticles()}>
              {(article) => <AlertRow article={article} onAnalyze={handleAnalyze} />}
            </For>
          </tbody>
        </table>
      </div>

      {totalPages() > 1 && (
        <div class="flex items-center justify-between mt-6 pt-4 border-t border-white/10 dark:border-white/5">
          <div class="text-sm font-medium text-gray-600 dark:text-gray-400">
            Page <span class="text-blue-600 dark:text-blue-400 font-bold">{page() + 1}</span> of <span class="font-bold">{totalPages()}</span>
          </div>
          <div class="flex space-x-2">
            <button
              onClick={() => setPage(Math.max(0, page() - 1))}
              disabled={page() === 0}
              class="btn-secondary text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              ← Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages() - 1, page() + 1))}
              disabled={page() === totalPages() - 1}
              class="btn-secondary text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Plan Drawer */}
      <PlanDrawer
        isOpen={drawerOpen()}
        onClose={closeDrawer}
        plan={currentPlan()}
        loading={planLoading()}
      />
    </div>
  )
}

