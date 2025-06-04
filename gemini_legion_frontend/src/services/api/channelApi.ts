/**
 * Channel API Service
 */

import { API_BASE_URL, API_ENDPOINTS, getHeaders, handleAPIResponse } from './config'
import type { Channel, Message } from '@/types'

export const channelApi = {
  /**
   * List all channels
   */
  async list(): Promise<Channel[]> {
    console.log('[channelApi] list: Fetching channels...');
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.list}`, {
      method: 'GET',
      headers: getHeaders(),
    });
    console.log('[channelApi] list: Raw response status:', response.status);
    // Clone the response to log its body, as body can only be read once
    const responseCloneForLogging = response.clone();
    try {
      const rawText = await responseCloneForLogging.text();
      console.log('[channelApi] list: Raw response text:', rawText);
    } catch (e) {
      console.error('[channelApi] list: Error reading raw response text for logging:', e);
    }

    const data = await handleAPIResponse<{ channels: Channel[], total: number }>(response);
    console.log('[channelApi] list: Processed data:', data);
    if (data && data.channels) {
      console.log('[channelApi] list: Returning channels:', data.channels);
      return data.channels;
    }
    console.warn('[channelApi] list: Processed data did not contain channels or data itself was nullish. Returning empty array.');
    return []; // Fallback to empty array if data.channels is not as expected
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
    channel_type: 'public' | 'private' | 'direct' // Keep for input clarity
    members?: string[]
  }): Promise<Channel> {
    console.log('[channelApi] create CALLED. Data:', data); // Log 1: Entry and raw data
    // Transform channel_type to is_private for the backend
    const is_private = data.channel_type === 'private' || data.channel_type === 'direct';
    const payload = {
      name: data.name,
      description: data.description,
      members: data.members,
      is_private: is_private,
    };
    console.log('[channelApi] create: Attempting to POST to create channel. Payload:', payload); // Log 2: Final payload
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.channels.create}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload), // Send transformed payload
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
  async sendMessage(channelId: string, data: { // channelId from path is still used for URL construction
    sender: string       // To match backend Pydantic model: SendMessageRequest
    channel_id: string // To match backend Pydantic model (even if redundant with path)
    content: string
    message_type?: 'text' | 'system' | 'event' // Keep for potential future use, not in current backend model
  }): Promise<Message> {
    const url = `${API_BASE_URL}${API_ENDPOINTS.channels.sendMessage(channelId)}`;
    console.log('[channelApi] sendMessage: Attempting to POST to URL:', url);
    const response = await fetch(url, {
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