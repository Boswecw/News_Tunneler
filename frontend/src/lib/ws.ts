import { useStore } from './store'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'

let ws: WebSocket | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

export const connectWebSocket = (onAlert?: (data: any) => void) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return
  }

  try {
    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log('WebSocket connected')
      useStore.setState({ isConnected: true })
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'alert') {
          useStore.getState().addLiveAlert(message.data)
          onAlert?.(message.data)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      useStore.setState({ isConnected: false })
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      useStore.setState({ isConnected: false })
      attemptReconnect(onAlert)
    }
  } catch (error) {
    console.error('Failed to connect WebSocket:', error)
    attemptReconnect(onAlert)
  }
}

const attemptReconnect = (onAlert?: (data: any) => void) => {
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    reconnectAttempts++
    console.log(`Attempting to reconnect... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`)
    setTimeout(() => connectWebSocket(onAlert), RECONNECT_DELAY)
  } else {
    console.error('Max reconnection attempts reached')
  }
}

export const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

export const sendWebSocketMessage = (message: any) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message))
  }
}

export const isWebSocketConnected = () => {
  return ws && ws.readyState === WebSocket.OPEN
}

