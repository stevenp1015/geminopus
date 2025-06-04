/**
 * API Configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  // Health
  health: '/health',
  
  // Minions
  minions: {
    list: '/api/minions/',
    get: (id: string) => `/api/minions/${id}`,
    create: '/api/minions/',
    updateState: (id: string) => `/api/minions/${id}/state`,
    updatePersona: (id: string) => `/api/minions/${id}/persona`,
    delete: (id: string) => `/api/minions/${id}`,
    diaryEntries: (id: string) => `/api/minions/${id}/diary`,
    memories: (id: string) => `/api/minions/${id}/memories`,
  },
  
  // Channels
  channels: {
    list: '/api/channels/',
    get: (id: string) => `/api/channels/${id}`,
    create: '/api/channels/create',
    messages: (id: string) => `/api/channels/${id}/messages`,
    sendMessage: (id: string) => `/api/channels/${id}/send`,
    members: (id: string) => `/api/channels/${id}/members`,
    addMember: (id: string) => `/api/channels/${id}/members`,
    removeMember: (id: string, minionId: string) => `/api/channels/${id}/members/${minionId}`,
  },
  
  // Tasks
  tasks: {
    list: '/api/tasks/',
    get: (id: string) => `/api/tasks/${id}`,
    create: '/api/tasks/',
    update: (id: string) => `/api/tasks/${id}`,
    updateStatus: (id: string) => `/api/tasks/${id}/status`,
    assign: (id: string) => `/api/tasks/${id}/assign`,
    delete: (id: string) => `/api/tasks/${id}`,
    subtasks: (id: string) => `/api/tasks/${id}/subtasks`,
  },
  
  // Tools
  tools: {
    list: '/api/tools/',
    get: (id: string) => `/api/tools/${id}`,
    execute: (id: string) => `/api/tools/${id}/execute`,
  },
} as const

// Request headers
export const getHeaders = (token?: string) => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

// Generic API error class
export class APIError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(`${status}: ${statusText}`)
    this.name = 'APIError'
  }
}

// Generic API response handler
export async function handleAPIResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new APIError(response.status, response.statusText, errorData)
  }
  
  return response.json()
}