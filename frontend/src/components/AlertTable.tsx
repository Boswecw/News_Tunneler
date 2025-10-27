import { createSignal, For } from 'solid-js'
import type { Article } from '../lib/store'
import AlertRow from './AlertRow'

interface AlertTableProps {
  articles: Article[]
  isLoading?: boolean
}

export default function AlertTable(props: AlertTableProps) {
  const [page, setPage] = createSignal(0)
  const itemsPerPage = 20

  const paginatedArticles = () => {
    const start = page() * itemsPerPage
    return props.articles.slice(start, start + itemsPerPage)
  }

  const totalPages = () => Math.ceil(props.articles.length / itemsPerPage)

  return (
    <div class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Title
              </th>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Summary
              </th>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Source
              </th>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Ticker
              </th>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Score
              </th>
              <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                Published
              </th>
            </tr>
          </thead>
          <tbody>
            {props.isLoading && (
              <tr>
                <td colSpan={6} class="px-4 py-8 text-center text-gray-600 dark:text-gray-400">
                  Loading...
                </td>
              </tr>
            )}
            {!props.isLoading && paginatedArticles().length === 0 && (
              <tr>
                <td colSpan={6} class="px-4 py-8 text-center text-gray-600 dark:text-gray-400">
                  No articles found
                </td>
              </tr>
            )}
            <For each={paginatedArticles()}>
              {(article) => <AlertRow article={article} />}
            </For>
          </tbody>
        </table>
      </div>

      {totalPages() > 1 && (
        <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Page {page() + 1} of {totalPages()}
          </div>
          <div class="flex space-x-2">
            <button
              onClick={() => setPage(Math.max(0, page() - 1))}
              disabled={page() === 0}
              class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages() - 1, page() + 1))}
              disabled={page() === totalPages() - 1}
              class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

