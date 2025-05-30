/**
 * Task API Service
 */

import { API_BASE_URL, API_ENDPOINTS, getHeaders, handleAPIResponse } from './config'
import type { Task, TaskStatus } from '../../types/task'

export const taskApi = {
  /**
   * List all tasks
   */
  async list(): Promise<Task[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.list}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Task[]>(response)
  },

  /**
   * Get a specific task
   */
  async get(taskId: string): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.get(taskId)}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Task>(response)
  },

  /**
   * Create a new task
   */
  async create(data: {
    title: string
    description: string
    priority: 'low' | 'medium' | 'high' | 'critical'
    assigned_to?: string[]
    parent_task_id?: string
    dependencies?: string[]
    deadline?: string
  }): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.create}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    })
    return handleAPIResponse<Task>(response)
  },

  /**
   * Update a task
   */
  async update(taskId: string, data: Partial<Task>): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.update(taskId)}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    })
    return handleAPIResponse<Task>(response)
  },

  /**
   * Update task status
   */
  async updateStatus(taskId: string, status: TaskStatus): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.updateStatus(taskId)}`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({ status }),
    })
    return handleAPIResponse<Task>(response)
  },

  /**
   * Assign task to minions
   */
  async assign(taskId: string, minionIds: string[]): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.assign(taskId)}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ minion_ids: minionIds }),
    })
    return handleAPIResponse<Task>(response)
  },

  /**
   * Delete a task
   */
  async delete(taskId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.delete(taskId)}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`)
    }
  },

  /**
   * Get task subtasks
   */
  async getSubtasks(taskId: string): Promise<Task[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.tasks.subtasks(taskId)}`, {
      method: 'GET',
      headers: getHeaders(),
    })
    return handleAPIResponse<Task[]>(response)
  },
}