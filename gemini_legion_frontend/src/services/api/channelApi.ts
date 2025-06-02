/**
 * Channel API Service
 */

import { API_BASE_URL, API_ENDPOINTS, getHeaders, handleAPIResponse } from './config'
import type { Channel, Message } from '../../types'

export const channelApi = {
  /**
   * List all channels
   */
  async list(): Promise<Channel[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.list}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    const data = await handleAPIResponse<{ channels: Channel[], total: number }>(response)
    return data.channels
  },

  /**
   * Get a specific channel
   */
  async get(channelId: string): Promise<Channel> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.get(channelId)}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Channel>(response)
  },

  /**
   * Create a new channel
   */
  async create(data: {
    name: string
    description?: string
    channel_type: 'public' | 'private' | 'direct'
    members?: string[]
  }): Promise<Channel> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.create}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    })
    return handleAPIResponse<Channel>(response)
  },

  /**
   * Get channel messages
   */
  async getMessages(channelId: string, limit?: number, before?: string): Promise<Message[]> {
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit.toString())
    if (before) params.append('before', before)
    
    const url = `${API_BASE_URL}${API_ENDPOINTS.channels.messages(channelId)}?${params}`
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    })
    const data = await handleAPIResponse<{ messages: Message[], total: number, has_more: boolean }>(response)
    return data.messages
  },

  /**
   * Send a message to a channel
   */
  async sendMessage(channelId: string, data: {
    sender_id: string
    content: string
    message_type?: 'text' | 'system' | 'event'
  }): Promise<Message> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.sendMessage(channelId)}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    })
    return handleAPIResponse<Message>(response)
  },

  /**
   * Add a member to a channel
   */
  async addMember(channelId: string, minionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.addMember(channelId)}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ minion_id: minionId }),
    })
    if (!response.ok) {
      throw new Error(`Failed to add member: ${response.statusText}`)
    }
  },

  /**
   * Remove a member from a channel
   */
  async removeMember(channelId: string, minionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.removeMember(channelId, minionId)}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to remove member: ${response.statusText}`)
    }
  },
}