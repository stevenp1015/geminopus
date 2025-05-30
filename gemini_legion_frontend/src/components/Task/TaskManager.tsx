import { useState, useEffect } from 'react'
import { Plus, Filter, Search, ChevronDown } from 'lucide-react'
import { useLegionStore } from '../../store/legionStore'
import { useTaskStore } from '../../store/taskStore'
import TaskCard from './TaskCard'
import TaskDetail from './TaskDetail'
import CreateTaskModal from './CreateTaskModal'
import TaskTimeline from './TaskTimeline'
import type { Task } from '../../types/task'

type ViewMode = 'grid' | 'list' | 'timeline'
type FilterStatus = 'all' | Task['status']
type FilterPriority = 'all' | Task['priority']

export default function TaskManager() {
  const { minions } = useLegionStore()
  const { tasks, fetchTasks, selectedTask, setSelectedTask } = useTaskStore()
  
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [filterPriority, setFilterPriority] = useState<FilterPriority>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const filteredTasks = tasks.filter(task => {
    if (filterStatus !== 'all' && task.status !== filterStatus) return false
    if (filterPriority !== 'all' && task.priority !== filterPriority) return false
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !task.description.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev)
      if (newSet.has(taskId)) {
        newSet.delete(taskId)
      } else {
        newSet.add(taskId)
      }
      return newSet
    })
  }

  const renderTaskHierarchy = (tasks: Task[], parentId?: string) => {
    const rootTasks = tasks.filter(t => t.parent_task_id === parentId)
    
    return rootTasks.map(task => (
      <div key={task.task_id} className="mb-4">
        <div className="flex items-start">
          {task.subtasks.length > 0 && (
            <button
              onClick={() => toggleTaskExpansion(task.task_id)}
              className="mr-2 mt-1 p-1 hover:bg-white/10 rounded transition-colors"
            >
              <ChevronDown 
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  expandedTasks.has(task.task_id) ? 'rotate-180' : ''
                }`}
              />
            </button>
          )}
          <div className="flex-1">
            <TaskCard
              task={task}
              onClick={() => setSelectedTask(task)}
              minions={minions}
              expanded={expandedTasks.has(task.task_id)}
            />
          </div>
        </div>
        {expandedTasks.has(task.task_id) && task.subtasks.length > 0 && (
          <div className="ml-8 mt-2 border-l-2 border-legion-primary/20 pl-4">
            {renderTaskHierarchy(task.subtasks, task.task_id)}
          </div>
        )}
      </div>
    ))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-white">Task Management</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Create Task</span>
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-black/30 backdrop-blur-md rounded-lg border border-legion-primary/20 p-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg
                         text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
              />
            </div>
          </div>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white
                     focus:border-legion-primary/50 focus:outline-none"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          {/* Priority Filter */}
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value as FilterPriority)}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white
                     focus:border-legion-primary/50 focus:outline-none"
          >
            <option value="all">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          {/* View Mode */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <div className="flex rounded-lg border border-white/10 overflow-hidden">
              {(['grid', 'list', 'timeline'] as ViewMode[]).map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-1 text-sm capitalize transition-colors ${
                    viewMode === mode
                      ? 'bg-legion-primary text-white'
                      : 'bg-white/5 text-gray-300 hover:bg-white/10'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Task Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task List */}
        <div className="lg:col-span-2">
          {viewMode === 'timeline' ? (
            <TaskTimeline tasks={filteredTasks} onTaskClick={setSelectedTask} />
          ) : viewMode === 'list' ? (
            <div className="space-y-2">
              {renderTaskHierarchy(filteredTasks)}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTasks.map(task => (
                <TaskCard
                  key={task.task_id}
                  task={task}
                  onClick={() => setSelectedTask(task)}
                  minions={minions}
                />
              ))}
            </div>
          )}
        </div>

        {/* Task Detail */}
        <div className="lg:col-span-1">
          {selectedTask ? (
            <TaskDetail task={selectedTask} minions={minions} />
          ) : (
            <div className="bg-black/30 backdrop-blur-md rounded-lg border border-legion-primary/20 p-8">
              <div className="text-center text-gray-400">
                <p>Select a task to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Task Modal */}
      {showCreateModal && (
        <CreateTaskModal
          onClose={() => setShowCreateModal(false)}
          minions={minions}
        />
      )}
    </div>
  )
}