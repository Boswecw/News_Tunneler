import { render } from 'solid-js/web'
import './app.css'
import App from './App'

const root = document.getElementById('root')

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error(
    'Root element not found. Did you forget to add it to your index.html? Or did the id attribute get misspelled?',
  )
}

render(() => <App />, root!)

