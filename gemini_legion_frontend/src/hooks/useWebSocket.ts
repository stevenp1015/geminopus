import { useEffect, useState } from 'react'
import { useLegionStore } from '../store/legionStore'

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false)
  const { websocket, connectWebSocket, disconnectWebSocket } = useLegionStore()
  
  useEffect(() => {
    // Connect on mount
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      disconnectWebSocket()
    }
  }, [connectWebSocket, disconnectWebSocket])
  
  useEffect(() => {
    if (websocket) {
      websocket.on('connect', () => setIsConnected(true))
      websocket.on('disconnect', () => setIsConnected(false))
      
      // Set initial state
      setIsConnected(websocket.connected)
    }
  }, [websocket])
  
  return { isConnected, websocket }
}