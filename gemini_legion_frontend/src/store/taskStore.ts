import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { taskApi } from '../services/api'
import type { Task, CreateTaskData, UpdateTaskData } from '../types/task'

interface TaskState {
  tasks: Task[]
  selectedTask: Task | null
  loading: boolean
  error: string | null
  
  // Actions
  fetchTasks: () => Promise<void>
  createTask: (data: CreateTaskData) => Promise<Task>
  updateTask: (taskId: string, data: UpdateTaskData) => Promise<void>
  deleteTask: (taskId: string) => Promise<void>
  setSelectedTask: (task: Task | null) => void
  addTaskMessage: (taskId: string, message: string) => void
  updateTaskProgress: (taskId: string, progress: number) => void
  
  // Real-time updates
  handleTaskUpdate: (task: Task) => void
  handleTaskDeleted: (taskId: string) => void
}

export const useTaskStore = create<TaskState>()(
  devtools(
    (set, get) => ({
      tasks: [],
      selectedTask: null,
      loading: false,
      error: null,

      fetchTasks: async () => {
        set({ loading: true, error: null })
        try {
          const tasks = await taskApi.list()
          set({ tasks, loading: false })
        } catch (error) {
          set({ error: (error as Error).message, loading: false })
          console.error('Failed to fetch tasks:', error)
        }
      },

      createTask: async (data: CreateTaskData) => {
        try {
          const newTask = await taskApi.create(data)
          set(state => ({ tasks: [...state.tasks, newTask] }))
          return newTask
        } catch (error) {
          set({ error: (error as Error).message })
          throw error
        }
      },

      updateTask: async (taskId: string, data: UpdateTaskData) => {
        try {
          const updatedTask = await taskApi.update(taskId, data)
          set(state => ({
            tasks: state.tasks.map(t => t.task_id === taskId ? updatedTask : t),
            selectedTask: state.selectedTask?.task_id === taskId ? updatedTask : state.selectedTask
          }))
        } catch (error) {
          set({ error: (error as Error).message })
          throw error
        }
      },

      deleteTask: async (taskId: string) => {
        try {
          await taskApi.delete(taskId)
          set(state => ({
            tasks: state.tasks.filter(t => t.task_id !== taskId),
            selectedTask: state.selectedTask?.task_id === taskId ? null : state.selectedTask
          }))
        } catch (error) {
          set({ error: (error as Error).message })
          throw error
        }
      },

      setSelectedTask: (task: Task | null) => {
        set({ selectedTask: task })
      },

      addTaskMessage: (taskId: string, message: string) => {
        set(state => ({
          tasks: state.tasks.map(t => {
            if (t.task_id === taskId) {
              return {
                ...t,
                execution_log: [...(t.execution_log || []), {
                  timestamp: new Date().toISOString(),
                  message,
                  level: 'info'
                }]
              }
            }
            return t
          })
        }))
      },

      updateTaskProgress: (taskId: string, progress: number) => {
        set(state => ({
          tasks: state.tasks.map(t => {
            if (t.task_id === taskId) {
              return {
                ...t,
                progress,
                status: progress >= 100 ? 'completed' : t.status
              }
            }
            return t
          })
        }))
      },

      // Real-time update handlers
      handleTaskUpdate: (task: Task) => {
        set(state => ({
          tasks: state.tasks.map(t => t.task_id === task.task_id ? task : t),
          selectedTask: state.selectedTask?.task_id === task.task_id ? task : state.selectedTask
        }))
      },

      handleTaskDeleted: (taskId: string) => {
        set(state => ({
          tasks: state.tasks.filter(t => t.task_id !== taskId),
          selectedTask: state.selectedTask?.task_id === taskId ? null : state.selectedTask
        }))
      }
    }),
    {
      name: 'task-store'
    }
  )
)