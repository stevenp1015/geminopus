import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { io, Socket } from 'socket.io-client'
import toast from 'react-hot-toast'
import { minionApi, channelApi, WS_BASE_URL } from '../services/api'
import type { Minion, Channel, Message } from '../types'

interface LegionState {
  // State
  minions: Record<string, Minion>
  channels: Record<string, Channel>
  messages: Record<string, Message[]>
  selectedMinionId: string | null
  selectedChannelId: string | null
  websocket: Socket | null
  loading: boolean
  error: string | null
  
  // Actions
  setMinions: (minions: Minion[]) => void
  addMinion: (minion: Minion) => void
  updateMinion: (minionId: string, updates: Partial<Minion>) => void
  removeMinion: (minionId: string) => void
  selectMinion: (minionId: string | null) => void
  
  setChannels: (channels: Channel[]) => void
  addChannel: (channel: Channel) => void
  updateChannel: (channelId: string, updates: Partial<Channel>) => void
  selectChannel: (channelId: string | null) => void
  
  addMessage: (channelId: string, message: Message) => void
  setMessages: (channelId: string, messages: Message[]) => void
  
  connectWebSocket: () => void
  disconnectWebSocket: () => void
  
  // API calls
  fetchMinions: () => Promise<void>
  fetchChannels: () => Promise<void>
  fetchMessages: (channelId: string) => Promise<void>
  spawnMinion: (config: any) => Promise<void>
  sendMessage: (channelId: string, minionId: string, content: string) => Promise<void>
  updateMinionPersona: (minionId: string, persona: any) => Promise<void>
  updateMinionEmotionalState: (minionId: string, state: any) => Promise<void>
}

export const useLegionStore = create<LegionState>()(
  devtools(
    (set, get) => ({
      // Initial state
      minions: {},
      channels: {},
      messages: {},
      selectedMinionId: null,
      selectedChannelId: null,
      websocket: null,
      loading: false,
      error: null,
      
      // Minion actions
      setMinions: (minions) => set({
        minions: minions.reduce((acc, minion) => {
          acc[minion.minion_id] = minion
          return acc
        }, {} as Record<string, Minion>)
      }),
      
      addMinion: (minion) => set((state) => ({
        minions: { ...state.minions, [minion.minion_id]: minion }
      })),
      
      updateMinion: (minionId, updates) => set((state) => ({
        minions: {
          ...state.minions,
          [minionId]: { ...state.minions[minionId], ...updates }
        }
      })),
      
      removeMinion: (minionId) => set((state) => {
        const newMinions = { ...state.minions }
        delete newMinions[minionId]
        return { minions: newMinions }
      }),
      
      selectMinion: (minionId) => set({ selectedMinionId: minionId }),
      
      // Channel actions
      setChannels: (channels) => set({
        channels: channels.reduce((acc, channel) => {
          acc[channel.channel_id] = channel
          return acc
        }, {} as Record<string, Channel>)
      }),
      
      addChannel: (channel) => set((state) => ({
        channels: { ...state.channels, [channel.channel_id]: channel }
      })),
      
      updateChannel: (channelId, updates) => set((state) => ({
        channels: {
          ...state.channels,
          [channelId]: { ...state.channels[channelId], ...updates }
        }
      })),
      
      selectChannel: (channelId) => set({ selectedChannelId: channelId }),
      
      // Message actions
      addMessage: (channelId, message) => set((state) => ({
        messages: {
          ...state.messages,
          [channelId]: [...(state.messages[channelId] || []), message]
        }
      })),
      
      setMessages: (channelId, messages) => set((state) => ({
        messages: { ...state.messages, [channelId]: messages }
      })),
      
      // WebSocket management
      connectWebSocket: () => {
        const ws = io(`${WS_BASE_URL}/ws`, {
          transports: ['websocket'],
          reconnection: true,
          reconnectionAttempts: 5,
          reconnectionDelay: 1000,
        })
        
        ws.on('connect', () => {
          console.log('WebSocket connected')
          toast.success('Connected to Legion Server')
        })
        
        ws.on('disconnect', () => {
          console.log('WebSocket disconnected')
          toast.error('Disconnected from Legion Server')
        })
        
        // Minion events
        ws.on('minion_spawned', (data: any) => {
          get().addMinion(data.minion)
          toast.success(`${data.minion.name} has joined the Legion!`)
        })
        
        ws.on('minion_despawned', (data: any) => {
          get().removeMinion(data.minion_id)
          toast.info(`${data.minion_name} has left the Legion`)
        })
        
        ws.on('minion_emotional_state_updated', (data: any) => {
          get().updateMinion(data.minion_id, { 
            emotional_state: data.emotional_state 
          })
        })
        
        ws.on('minion_status_changed', (data: any) => {
          get().updateMinion(data.minion_id, { 
            status: data.status 
          })
        })
        
        // Message events (forward to chat store)
        ws.on('message_sent', (data: any) => {
          // Import chat store dynamically to avoid circular dependency
          import('./chatStore').then(({ useChatStore }) => {
            useChatStore.getState().handleNewMessage(data.channel_id, data.message)
          })
        })
        
        // Channel events (forward to chat store)
        ws.on('channel_created', (data: any) => {
          import('./chatStore').then(({ useChatStore }) => {
            useChatStore.getState().addChannel(data.channel)
          })
        })
        
        ws.on('channel_updated', (data: any) => {
          import('./chatStore').then(({ useChatStore }) => {
            useChatStore.getState().handleChannelUpdate(data.channel_id, data.updates)
          })
        })
        
        ws.on('channel_member_added', (data: any) => {
          import('./chatStore').then(({ useChatStore }) => {
            const chatStore = useChatStore.getState()
            const channel = chatStore.channels[data.channel_id]
            if (channel) {
              chatStore.updateChannel(data.channel_id, {
                members: [...channel.members, data.minion_id]
              })
            }
          })
        })
        
        ws.on('channel_member_removed', (data: any) => {
          import('./chatStore').then(({ useChatStore }) => {
            const chatStore = useChatStore.getState()
            const channel = chatStore.channels[data.channel_id]
            if (channel) {
              chatStore.updateChannel(data.channel_id, {
                members: channel.members.filter(id => id !== data.minion_id)
              })
            }
          })
        })
        
        // Task events (forward to task store)
        ws.on('task_created', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            useTaskStore.getState().handleTaskUpdate(data.task)
          })
        })
        
        ws.on('task_updated', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            useTaskStore.getState().handleTaskUpdate(data.task)
          })
        })
        
        ws.on('task_status_changed', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            const taskStore = useTaskStore.getState()
            const task = taskStore.tasks.find(t => t.task_id === data.task_id)
            if (task) {
              taskStore.handleTaskUpdate({ ...task, status: data.status })
            }
          })
        })
        
        ws.on('task_assigned', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            const taskStore = useTaskStore.getState()
            const task = taskStore.tasks.find(t => t.task_id === data.task_id)
            if (task) {
              taskStore.handleTaskUpdate({ 
                ...task, 
                assigned_to: [...task.assigned_to, data.minion_id]
              })
            }
          })
          toast.info(`Task assigned to ${data.minion_id}`)
        })
        
        ws.on('task_completed', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            useTaskStore.getState().handleTaskUpdate(data.task)
          })
          toast.success(`Task "${data.task.title}" completed!`)
        })
        
        ws.on('task_deleted', (data: any) => {
          import('./taskStore').then(({ useTaskStore }) => {
            useTaskStore.getState().handleTaskDeleted(data.task_id)
          })
        })
        
        set({ websocket: ws })
      },
      
      disconnectWebSocket: () => {
        const ws = get().websocket
        if (ws) {
          ws.disconnect()
          set({ websocket: null })
        }
      },
      
      // API calls
      fetchMinions: async () => {
        set({ loading: true, error: null })
        try {
          const minions = await minionApi.list()
          get().setMinions(minions)
        } catch (error) {
          console.error('Failed to fetch minions:', error)
          toast.error('Failed to fetch minions')
          set({ error: (error as Error).message })
        } finally {
          set({ loading: false })
        }
      },
      
      fetchChannels: async () => {
        set({ loading: true, error: null })
        try {
          const channels = await channelApi.list()
          get().setChannels(channels)
        } catch (error) {
          console.error('Failed to fetch channels:', error)
          toast.error('Failed to fetch channels')
          set({ error: (error as Error).message })
        } finally {
          set({ loading: false })
        }
      },
      
      fetchMessages: async (channelId: string) => {
        try {
          const messages = await channelApi.getMessages(channelId, 100)
          get().setMessages(channelId, messages)
        } catch (error) {
          console.error('Failed to fetch messages:', error)
          toast.error('Failed to fetch messages')
        }
      },
      
      spawnMinion: async (config: any) => {
        try {
          // Call the /spawn endpoint with the correct payload structure
          const response = await fetch(`${WS_BASE_URL}/api/minions/spawn`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: config.name,
              personality: config.base_personality || config.personality,
              quirks: config.quirks || [],
              catchphrases: config.catchphrases || [],
              expertise: config.expertise_areas || config.expertise || [],
              tools: config.allowed_tools || config.tools || []
            })
          })
          
          if (!response.ok) {
            throw new Error(`Failed to spawn minion: ${response.statusText}`)
          }
          
          const result = await response.json()
          
          // Fetch the newly created minion
          const minion = await minionApi.get(result.id)
          get().addMinion(minion)
          toast.success(`Spawned ${config.name}! ${result.message}`)
        } catch (error) {
          console.error('Failed to spawn minion:', error)
          toast.error('Failed to spawn minion')
          throw error
        }
      },
      
      sendMessage: async (channelId: string, minionId: string, content: string) => {
        try {
          // Use the minion's send-message endpoint
          const response = await fetch(`${WS_BASE_URL}/api/minions/${minionId}/send-message`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              channel: channelId,
              message: content
            })
          })
          
          if (!response.ok) {
            throw new Error(`Failed to send message: ${response.statusText}`)
          }
          
          // The message will come through WebSocket events
          toast.success('Message sent!')
        } catch (error) {
          console.error('Failed to send message:', error)
          toast.error('Failed to send message')
          throw error
        }
      },
      
      updateMinionPersona: async (minionId: string, persona: any) => {
        try {
          const updatedPersona = await minionApi.updatePersona(minionId, persona)
          get().updateMinion(minionId, { persona: updatedPersona })
          toast.success('Persona updated!')
        } catch (error) {
          console.error('Failed to update persona:', error)
          toast.error('Failed to update persona')
          throw error
        }
      },
      
      updateMinionEmotionalState: async (minionId: string, state: any) => {
        try {
          // Use the update-emotional-state endpoint
          const response = await fetch(`${WS_BASE_URL}/api/minions/${minionId}/update-emotional-state`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(state)
          })
          
          if (!response.ok) {
            throw new Error(`Failed to update emotional state: ${response.statusText}`)
          }
          
          // Fetch the updated minion to get the new state
          const minion = await minionApi.get(minionId)
          get().updateMinion(minionId, minion)
          toast.success('Emotional state updated!')
        } catch (error) {
          console.error('Failed to update emotional state:', error)
          toast.error('Failed to update emotional state')
          throw error
        }
      }
    }),
    {
      name: 'legion-store'
    }
  )
)

// Global reference for WebSocket event forwarding
declare global {
  interface Window {
    __taskStore?: any
  }
}