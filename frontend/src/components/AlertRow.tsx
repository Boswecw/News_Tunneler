import { formatDistanceToNow } from 'date-fns'
import type { Article } from '../lib/store'

interface AlertRowProps {
  article: Article
}

export default function AlertRow(props: AlertRowProps) {
  const scoreColor = () => {
    const score = props.article.score || 0
    if (score >= 18) return 'text-green-600 dark:text-green-400'
    if (score >= 15) return 'text-blue-600 dark:text-blue-400'
    if (score >= 12) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  return (
    <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <td class="px-4 py-3">
        <a
          href={props.article.url}
          target="_blank"
          rel="noopener noreferrer"
          class="text-blue-600 dark:text-blue-400 hover:underline font-medium"
        >
          {props.article.title}
        </a>
      </td>
      <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {props.article.summary?.substring(0, 100)}...
      </td>
      <td class="px-4 py-3 text-sm">
        <span class="inline-block bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
          {props.article.source_name}
        </span>
      </td>
      <td class="px-4 py-3 text-sm">
        {props.article.ticker_guess && (
          <span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded font-medium">
            {props.article.ticker_guess}
          </span>
        )}
      </td>
      <td class={`px-4 py-3 text-sm font-bold ${scoreColor()}`}>
        {props.article.score?.toFixed(1)}
      </td>
      <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {formatDistanceToNow(new Date(props.article.published_at), { addSuffix: true })}
      </td>
    </tr>
  )
}

