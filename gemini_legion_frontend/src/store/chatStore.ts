export const COMMANDER_ID = 'COMMANDER_PRIME'; // All hail the Commander!
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import toast from 'react-hot-toast'
import { channelApi } from '../services/api'
import type { Channel, Message } from '@/types'

interface ChatState {
  // State
  channels: Record<string, Channel>
  messages: Record<string, Message[]>
  selectedChannelId: string | null
  loadingMessages: boolean
  error: string | null
  commanderCanSendMessages: boolean
  
  // Actions
  setChannels: (channels: Channel[]) => void
  addChannel: (channel: Channel) => void
  updateChannel: (channelId: string, updates: Partial<Channel>) => void
  removeChannel: (channelId: string) => void
  selectChannel: (channelId: string | null) => void
  
  addMessage: (channelId: string, message: Message) => void
  setMessages: (channelId: string, messages: Message[]) => void
  
  // API calls
  fetchChannels: () => Promise<void>
  fetchMessages: (channelId: string) => Promise<void>
  createChannel: (name: string, type: 'public' | 'private', memberIds?: string[]) => Promise<void>
  sendMessage: (channelId: string, senderId: string, content: string) => Promise<void>
  sendCommanderMessage: (channelId: string, content: string) => Promise<void>
  addMemberToChannel: (channelId: string, minionId: string) => Promise<void>
  removeMemberFromChannel: (channelId: string, minionId: string) => Promise<void>
  
  // Real-time updates
  handleNewMessage: (channelId: string, message: Message) => void
  handleChannelUpdate: (channelId: string, updates: Partial<Channel>) => void
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      // Initial state
      channels: {},
      messages: {},
      selectedChannelId: null,
      loadingMessages: false,
      error: null,
      commanderCanSendMessages: true,
      
      // Channel actions
      setChannels: (channels) => set({
        channels: channels.reduce((acc, channel) => {
          acc[channel.id] = channel // Changed from channel_id
          return acc
        }, {} as Record<string, Channel>)
      }),
      
      addChannel: (channel) => set((state) => ({
        channels: { ...state.channels, [channel.id]: channel } // Changed from channel_id
      })),
      
      updateChannel: (channelId, updates) => set((state) => ({
        channels: {
          ...state.channels,
          [channelId]: { ...state.channels[channelId], ...updates }
        }
      })),
      
      removeChannel: (channelId) => set((state) => {
        const newChannels = { ...state.channels }
        delete newChannels[channelId]
        const newMessages = { ...state.messages }
        delete newMessages[channelId]
        return { 
          channels: newChannels,
          messages: newMessages,
          selectedChannelId: state.selectedChannelId === channelId ? null : state.selectedChannelId
        }
      }),
      
      selectChannel: (channelId) => {
        const oldSelectedChannelId = get().selectedChannelId;
        console.log(`[ChatStore] selectChannel called. Old ID: ${oldSelectedChannelId}, New ID: ${channelId}`);
        set({ selectedChannelId: channelId });
        console.log(`[ChatStore] selectChannel: selectedChannelId has been set to: ${get().selectedChannelId}`);
      },
      
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
      
      // API calls
      fetchChannels: async () => {
        set({ error: null })
        try {
          const channels = await channelApi.list()
          get().setChannels(channels)
          
          // Auto-select first channel if none selected
          if (!get().selectedChannelId && channels.length > 0 && channels[0]) { // Added channels[0] check
            set({ selectedChannelId: channels[0].id }) // Changed from channel_id
          }
        } catch (error) {
          console.error('Failed to fetch channels:', error)
          toast.error('Failed to fetch channels')
          set({ error: (error as Error).message })
        }
      },
      
      fetchMessages: async (channelId: string) => {
        set({ loadingMessages: true })
        try {
          const messages = await channelApi.getMessages(channelId, 100)
          get().setMessages(channelId, messages)
        } catch (error) {
          console.error('Failed to fetch messages:', error)
          toast.error('Failed to fetch messages')
        } finally {
          set({ loadingMessages: false })
        }
      },
      
      createChannel: async (name: string, type: 'public' | 'private', memberIds?: string[]) => {
        console.log(`[ChatStore] createChannel CALLED. Name: "${name}", Type: "${type}", Members:`, memberIds);
        try {
          const channel = await channelApi.create({
            name,
            channel_type: type, // Corrected: 'type' to 'channel_type' for the API call
            members: memberIds || []
          })
          get().addChannel(channel)
          toast.success(`Channel #${name} created!`)
          
          // Auto-select the new channel
          set({ selectedChannelId: channel.id }) // Changed from channel_id
        } catch (error) {
          console.error('Failed to create channel:', error)
          toast.error('Failed to create channel')
          throw error
        }
      },
      
      sendMessage: async (channelId: string, senderId: string, content: string) => {
        console.log(`[ChatStore] sendMessage CALLED. Channel ID: ${channelId}, Sender ID: ${senderId}, Content: "${content}"`);
        try {
          // Send via channel endpoint
          const message = await channelApi.sendMessage(channelId, {
            sender: senderId,      // Changed from sender_id
            channel_id: channelId, // Added channel_id
            content
          })
          
          // Add message optimistically (will be updated by WebSocket)
          get().addMessage(channelId, message)
        } catch (error) {
          console.error('Failed to send message:', error)
          toast.error('Failed to send message')
          throw error
        }
      },

      sendCommanderMessage: async (channelId: string, content: string) => {
        console.log(`[ChatStore] sendCommanderMessage CALLED. Channel ID: ${channelId}, Content: "${content}"`);
        if (!get().commanderCanSendMessages) {
          toast.error('Commander messaging is currently disabled')
          throw new Error('Commander messaging disabled')
        }
        
        try {
          // Delegate to the main sendMessage method
          return await get().sendMessage(channelId, COMMANDER_ID, content)
        } catch (error) {
          console.error('Failed to send commander message:', error)
          toast.error('Failed to send commander message')
          throw error
        }
      },
      
      addMemberToChannel: async (channelId: string, minionId: string) => {
        try {
          await channelApi.addMember(channelId, minionId)
          
          // Update local state
          const channel = get().channels[channelId]
          if (channel) {
            get().updateChannel(channelId, {
              members: [...channel.members, minionId] // Changed participants to members
            })
          }
          
          toast.success('Member added to channel')
        } catch (error) {
          console.error('Failed to add member:', error)
          toast.error('Failed to add member to channel')
          throw error
        }
      },
      
      removeMemberFromChannel: async (channelId: string, minionId: string) => {
        try {
          await channelApi.removeMember(channelId, minionId)
          
          // Update local state
          const channel = get().channels[channelId]
          if (channel) {
            get().updateChannel(channelId, {
              members: channel.members.filter((id: string) => id !== minionId) // Changed participants to members
            })
          }
          
          toast.success('Member removed from channel')
        } catch (error) {
          console.error('Failed to remove member:', error)
          toast.error('Failed to remove member from channel')
          throw error
        }
      },
      
      // Real-time update handlers
      handleNewMessage: (channelId: string, message: Message) => {
        get().addMessage(channelId, message)
      },
      
      handleChannelUpdate: (channelId: string, updates: Partial<Channel>) => {
        get().updateChannel(channelId, updates)
      }
    }),
    {
      name: 'chat-store'
    }
  )
)