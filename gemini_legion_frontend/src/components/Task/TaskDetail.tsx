import { useState } from 'react'
import { 
  Clock, Users, AlertCircle, CheckCircle, XCircle, Loader,
  Edit, Trash, Plus, Link, Calendar, BarChart
} from 'lucide-react'
import { useTaskStore } from '../../store/taskStore'
import type { Task, TaskUpdate } from '../../types/task'
import type { Minion } from '../../types/minion'

interface TaskDetailProps {
  task: Task
  minions: Minion[]
}

export default function TaskDetail({ task, minions }: TaskDetailProps) {
  const { updateTask, deleteTask, decomposeTask } = useTaskStore()
  const [isEditing, setIsEditing] = useState(false)
  const [editedTask, setEditedTask] = useState(task)
  const handleUpdate = async (updates: TaskUpdate) => {
    try {
      await updateTask(task.task_id, updates)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update task:', error)
    }
  }

  const handleDecompose = async () => {
    try {
      await decomposeTask(task.task_id)
    } catch (error) {
      console.error('Failed to decompose task:', error)
    }
  }

  const getStatusIcon = () => {
    switch (task.status) {
      case 'pending':
        return <Clock className="w-5 h-5" />
      case 'in_progress':
        return <Loader className="w-5 h-5 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5" />
      case 'failed':
        return <XCircle className="w-5 h-5" />
    }
  }

  const getStatusColor = () => {
    switch (task.status) {
      case 'pending':
        return 'text-yellow-400'
      case 'in_progress':
        return 'text-blue-400'
      case 'completed':
        return 'text-green-400'
      case 'failed':
        return 'text-red-400'
    }
  }

  const assignedMinions = task.assigned_to.map(id => 
    minions.find(m => m.minion_id === id)
  ).filter(Boolean) as Minion[]

  return (
    <div className="bg-black/30 backdrop-blur-md rounded-lg border border-legion-primary/20 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {isEditing ? (
            <input
              type="text"
              value={editedTask.title}
              onChange={(e) => setEditedTask({ ...editedTask, title: e.target.value })}
              className="w-full text-2xl font-bold bg-transparent border-b border-legion-primary/50
                       text-white focus:outline-none focus:border-legion-primary"
              autoFocus
            />
          ) : (
            <h2 className="text-2xl font-bold text-white">{task.title}</h2>
          )}
          <div className={`flex items-center gap-2 mt-2 ${getStatusColor()}`}>
            {getStatusIcon()}
            <span className="capitalize">{task.status.replace('_', ' ')}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <Edit className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={() => deleteTask(task.task_id)}
            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
          >
            <Trash className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>

      {/* Description */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Description</h3>
        {isEditing ? (
          <textarea
            value={editedTask.description}
            onChange={(e) => setEditedTask({ ...editedTask, description: e.target.value })}
            className="w-full p-3 bg-white/5 border border-white/10 rounded-lg text-gray-300
                     focus:border-legion-primary/50 focus:outline-none resize-none"
            rows={4}
          />
        ) : (
          <p className="text-gray-300">{task.description}</p>
        )}
      </div>

      {/* Progress */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-400">Progress</h3>
          <span className="text-legion-accent">{task.progress}%</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-3 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-legion-primary to-legion-accent transition-all duration-500"
            style={{ width: `${task.progress}%` }}
          />
        </div>
      </div>

      {/* Assigned Minions */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Assigned Minions</h3>
        <div className="space-y-2">
          {assignedMinions.length > 0 ? (
            assignedMinions.map(minion => (
              <div
                key={minion.minion_id}
                className="flex items-center gap-3 p-2 bg-white/5 rounded-lg"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-legion-primary to-legion-accent
                              flex items-center justify-center text-sm font-bold">
                  {minion.name[0]}
                </div>
                <div>
                  <p className="text-white font-medium">{minion.name}</p>
                  <p className="text-xs text-gray-400">{minion.persona.base_personality}</p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-sm">No minions assigned yet</p>
          )}
        </div>
      </div>

      {/* Subtasks */}
      {task.subtasks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            Subtasks ({task.subtasks.length})
          </h3>
          <div className="space-y-2">
            {task.subtasks.map(subtask => (
              <div
                key={subtask.task_id}
                className="p-3 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-center justify-between">
                  <p className="text-white">{subtask.title}</p>
                  <span className={`text-xs ${
                    subtask.status === 'completed' ? 'text-green-400' : 'text-gray-400'
                  }`}>
                    {subtask.progress}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t border-white/10">
        {isEditing ? (
          <>
            <button
              onClick={() => handleUpdate(editedTask)}
              className="btn-primary flex-1"
            >
              Save Changes
            </button>
            <button
              onClick={() => {
                setEditedTask(task)
                setIsEditing(false)
              }}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            {task.status === 'pending' && task.subtasks.length === 0 && (
              <button
                onClick={handleDecompose}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                <BarChart className="w-4 h-4" />
                Decompose Task
              </button>
            )}
            <button
              onClick={() => handleUpdate({ status: 'in_progress' })}
              className="btn-secondary flex-1"
              disabled={task.status !== 'pending'}
            >
              Start Task
            </button>
          </>
        )}
      </div>
    </div>
  )
}