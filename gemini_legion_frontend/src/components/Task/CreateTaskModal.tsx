import { useState } from 'react'
import { X } from 'lucide-react'
import { useTaskStore } from '../../store/taskStore'
import type { Minion } from '../../types/minion'

interface CreateTaskModalProps {
  onClose: () => void
  minions: Minion[]
}

export default function CreateTaskModal({ onClose, minions }: CreateTaskModalProps) {
  const { createTask } = useTaskStore()
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as const,
    assigned_to: [] as string[],
    estimated_completion: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createTask({
        ...formData,
        status: 'pending',
        progress: 0,
        subtasks: [],
        dependencies: [],
        metadata: {}
      })
      onClose()
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  const toggleAssignment = (minionId: string) => {
    setFormData(prev => ({
      ...prev,
      assigned_to: prev.assigned_to.includes(minionId)
        ? prev.assigned_to.filter(id => id !== minionId)
        : [...prev.assigned_to, minionId]
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-legion-dark border border-legion-primary/20 rounded-lg p-6 w-full max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Create New Task</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Task Title
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                       text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
              placeholder="Enter task title..."
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                       text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none resize-none"
              rows={4}
              placeholder="Describe the task in detail..."
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Priority
            </label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                       text-white focus:border-legion-primary/50 focus:outline-none"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Assign to Minions */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Assign to Minions
            </label>
            <div className="grid grid-cols-2 gap-2">
              {minions.map(minion => (
                <button
                  key={minion.minion_id}
                  type="button"
                  onClick={() => toggleAssignment(minion.minion_id)}
                  className={`p-3 rounded-lg border transition-all ${
                    formData.assigned_to.includes(minion.minion_id)
                      ? 'bg-legion-primary/20 border-legion-primary text-white'
                      : 'bg-white/5 border-white/10 text-gray-300 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-legion-primary to-legion-accent
                                  flex items-center justify-center text-xs font-bold">
                      {minion.name[0]}
                    </div>
                    <span className="text-sm">{minion.name}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Estimated Completion */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Estimated Completion (Optional)
            </label>
            <input
              type="datetime-local"
              value={formData.estimated_completion}
              onChange={(e) => setFormData({ ...formData, estimated_completion: e.target.value })}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                       text-white focus:border-legion-primary/50 focus:outline-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn-primary flex-1">
              Create Task
            </button>
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}