export interface Task {
  task_id: string
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
  updated_at: string
  assigned_to: string[]  // Array of minion IDs
  created_by: string
  parent_task_id?: string
  subtasks: Task[]
  dependencies: string[]  // Task IDs this task depends on
  progress: number  // 0-100
  estimated_completion?: string
  actual_completion?: string
  metadata: {
    decomposition_strategy?: string
    complexity_score?: number
    required_tools?: string[]
    [key: string]: any
  }
  execution_log?: Array<{
    timestamp: string
    message: string
    level: 'info' | 'warning' | 'error'
  }>
}

export interface CreateTaskData {
  title: string
  description: string
  priority: Task['priority']
  assigned_to?: string[]
  parent_task_id?: string
  dependencies?: string[]
  estimated_completion?: string
  metadata?: Partial<Task['metadata']>
}

export interface UpdateTaskData {
  title?: string
  description?: string
  status?: Task['status']
  priority?: Task['priority']
  progress?: number
  assigned_to?: string[]
  estimated_completion?: string
  actual_completion?: string
  metadata?: Partial<Task['metadata']>
}

export interface TaskUpdate {
  status?: Task['status']
  progress?: number
  assigned_to?: string[]
  metadata?: Partial<Task['metadata']>
}

export interface TaskDecomposition {
  original_task: Task
  subtasks: Task[]
  dependencies: Array<{
    from: string
    to: string
    type: 'blocks' | 'informs' | 'optional'
  }>
  suggested_assignments: Array<{
    task_id: string
    minion_id: string
    confidence: number
    reasoning: string
  }>
}