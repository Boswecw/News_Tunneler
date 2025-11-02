import { createSignal, Show, onMount } from 'solid-js'

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = createSignal<any>(null)
  const [showPrompt, setShowPrompt] = createSignal(false)

  onMount(() => {
    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault()
      // Stash the event so it can be triggered later
      setDeferredPrompt(e)
      // Show the install prompt
      setShowPrompt(true)
      console.log('📱 PWA install prompt available')
    })

    // Listen for successful installation
    window.addEventListener('appinstalled', () => {
      console.log('✅ PWA installed successfully')
      setShowPrompt(false)
      setDeferredPrompt(null)
    })
  })

  const handleInstall = async () => {
    const prompt = deferredPrompt()
    if (!prompt) return

    // Show the install prompt
    prompt.prompt()

    // Wait for the user to respond to the prompt
    const { outcome } = await prompt.userChoice
    console.log(`User response to install prompt: ${outcome}`)

    // Clear the deferredPrompt
    setDeferredPrompt(null)
    setShowPrompt(false)
  }

  const handleDismiss = () => {
    setShowPrompt(false)
    // Store dismissal in localStorage to not show again for 7 days
    localStorage.setItem('pwa-install-dismissed', Date.now().toString())
  }

  // Check if user dismissed recently (within 7 days)
  const isDismissedRecently = () => {
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    if (!dismissed) return false
    const dismissedTime = parseInt(dismissed)
    const sevenDays = 7 * 24 * 60 * 60 * 1000
    return Date.now() - dismissedTime < sevenDays
  }

  return (
    <Show when={showPrompt() && !isDismissedRecently()}>
      <div class="fixed bottom-4 right-4 z-50 max-w-sm">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0">
              <img 
                src="/News_Tunneler_icon.webp" 
                alt="News Tunneler" 
                class="h-12 w-auto rounded-lg"
              />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                Install News Tunneler
              </h3>
              <p class="text-xs text-gray-600 dark:text-gray-400 mb-3">
                Install our app for faster access and offline support
              </p>
              <div class="flex gap-2">
                <button
                  onClick={handleInstall}
                  class="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                >
                  Install
                </button>
                <button
                  onClick={handleDismiss}
                  class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                >
                  Not now
                </button>
              </div>
            </div>
            <button
              onClick={handleDismiss}
              class="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Show>
  )
}

