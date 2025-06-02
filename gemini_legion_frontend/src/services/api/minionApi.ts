/**
 * Minion API Service
 */

import { API_BASE_URL, API_ENDPOINTS, getHeaders, handleAPIResponse } from './config'
import type { Minion, MinionPersona, EmotionalState, DiaryEntry, Memory } from '../../types'

export const minionApi = {
  /**
   * List all minions
   */
  async list(): Promise<Minion[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.list}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    const data = await handleAPIResponse<{ minions: Minion[], total: number }>(response)
    return data.minions
  },

  /**
   * Get a specific minion
   */
  async get(minionId: string): Promise<Minion> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.get(minionId)}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Minion>(response)
  },

  /**
   * Create a new minion
   */
  async create(data: {
    name: string
    base_personality: string
    quirks: string[]
    catchphrases?: string[]
    expertise_areas?: string[]
    allowed_tools?: string[]
    model_name?: string
  }): Promise<Minion> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.create}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    })
    return handleAPIResponse<Minion>(response)
  },

  /**
   * Update minion emotional state
   */
  async updateState(minionId: string, state: Partial<EmotionalState>): Promise<EmotionalState> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.updateState(minionId)}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(state),
    })
    return handleAPIResponse<EmotionalState>(response)
  },

  /**
   * Update minion persona
   */
  async updatePersona(minionId: string, persona: Partial<MinionPersona>): Promise<MinionPersona> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.updatePersona(minionId)}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(persona),
    })
    return handleAPIResponse<MinionPersona>(response)
  },

  /**
   * Delete a minion
   */
  async delete(minionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.minions.delete(minionId)}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to delete minion: ${response.statusText}`)
    }
  },

  /**
   * Get minion diary entries
   */
  async getDiaryEntries(minionId: string, limit?: number, offset?: number): Promise<DiaryEntry[]> {
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit.toString())
    if (offset) params.append('offset', offset.toString())
    
    const url = `${API_BASE_URL}${API_ENDPOINTS.minions.diaryEntries(minionId)}?${params}`
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<DiaryEntry[]>(response)
  },

  /**
   * Get minion memories
   */
  async getMemories(minionId: string, type?: 'working' | 'episodic' | 'semantic'): Promise<Memory[]> {
    const params = new URLSearchParams()
    if (type) params.append('type', type)
    
    const url = `${API_BASE_URL}${API_ENDPOINTS.minions.memories(minionId)}?${params}`
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Memory[]>(response)
  },
}