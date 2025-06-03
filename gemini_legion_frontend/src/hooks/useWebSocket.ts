import { useEffect, useState } from 'react'
import { useLegionStore } from '../store/legionStore'
import { useChatStore } from '../store/chatStore' // Import chatStore
import type { Message as MessageType } from '../types' // Import Message type for payload

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
      const handleConnect = () => setIsConnected(true);
      const handleDisconnect = () => setIsConnected(false);

      websocket.on('connect', handleConnect);
      websocket.on('disconnect', handleDisconnect);
      
      // Set initial state
      setIsConnected(websocket.connected);
      console.log('[useWebSocket] WebSocket instance available, attempting to set up listeners.'); // <-- ADD THIS LOG

      // --- Application-specific event listeners ---
      const { handleNewMessage } = useChatStore.getState(); // Get action from chatStore

      type MessageSentPayload = {
        channel_id: string;
        message: MessageType; // This should match the structure sent by the backend
      };

      const handleMessageSent = (data: MessageSentPayload) => {
        console.log('[useWebSocket] Received "message_sent" event:', data);
        if (data && data.channel_id && data.message) {
          handleNewMessage(data.channel_id, data.message);
        } else {
          console.error('[useWebSocket] Invalid "message_sent" payload:', data);
        }
      };
      websocket.on('message_sent', handleMessageSent);

      // Wildcard listener for debugging - to see ALL events from server
      const genericEventHandler = (eventName: string, ...args: any[]) => {
        console.log(`[useWebSocket] WILDCARD EVENT: Name: '${eventName}', Data:`, args);
      };
      // @ts-ignore - onAny might not be in older socket.io-client types but often exists
      if (typeof websocket.onAny === 'function') {
        // @ts-ignore
        websocket.onAny(genericEventHandler);
        console.log('[useWebSocket] Registered wildcard event listener (onAny).');
      } else {
        console.log('[useWebSocket] websocket.onAny is not a function, cannot register wildcard listener.');
      }

      // TODO: Add listeners for other events like 'minion_status_changed', 'channel_updated', 'task_updated' etc.
      // and dispatch them to the appropriate stores (legionStore, chatStore, taskStore).

      // Cleanup function to remove listeners when component unmounts or websocket changes
      return () => {
        websocket.off('connect', handleConnect);
        websocket.off('disconnect', handleDisconnect);
        websocket.off('message_sent', handleMessageSent);
        // @ts-ignore
        if (typeof websocket.offAny === 'function') {
          // @ts-ignore
          websocket.offAny(genericEventHandler);
          console.log('[useWebSocket] Unregistered wildcard event listener (offAny).');
        }
        // TODO: Off other listeners too
      };
    }
  }, [websocket]); // Rerun if websocket instance changes
  
  return { isConnected, websocket }
}