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
        
        ws.on('minion_update', (data: any) => {
          get().updateMinion(data.minion_id, data.updates)
        })
        
        ws.on('new_message', (data: any) => {
          get().addMessage(data.channel_id, data.message)
        })
        
        ws.on('channel_update', (data: any) => {
          get().updateChannel(data.channel_id, data.updates)
        })
        
        ws.on('minion_spawned', (data: any) => {
          get().addMinion(data.minion)
          toast.success(`${data.minion.persona.name} has joined the Legion!`)
        })
        
        ws.on('task_update', (data: any) => {
          // Forward to task store
          if (window.__taskStore?.handleTaskUpdate) {
            window.__taskStore.handleTaskUpdate(data.task)
          }
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
          const minion = await minionApi.create(config)
          get().addMinion(minion)
          toast.success(`Spawned ${minion.persona.name}!`)
        } catch (error) {
          console.error('Failed to spawn minion:', error)
          toast.error('Failed to spawn minion')
          throw error
        }
      },
      
      sendMessage: async (channelId: string, minionId: string, content: string) => {
        try {
          const message = await channelApi.sendMessage(channelId, {
            sender_id: minionId,
            content
          })
          get().addMessage(channelId, message)
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
          const updatedState = await minionApi.updateState(minionId, state)
          get().updateMinion(minionId, { emotional_state: updatedState })
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