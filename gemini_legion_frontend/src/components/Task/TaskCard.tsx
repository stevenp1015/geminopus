import { Clock, Users, AlertCircle, CheckCircle, XCircle, Loader } from 'lucide-react'
import type { Task } from '../../types/task'
import type { Minion } from '../../types/minion'

interface TaskCardProps {
  task: Task
  onClick: (task: Task) => void
  minions: Minion[]
  expanded?: boolean
}

export default function TaskCard({ task, onClick, minions, expanded }: TaskCardProps) {
  const getStatusIcon = () => {
    switch (task.status) {
      case 'pending':
        return <Clock className="w-4 h-4" />
      case 'in_progress':
        return <Loader className="w-4 h-4 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-4 h-4" />
      case 'failed':
        return <XCircle className="w-4 h-4" />
    }
  }

  const getStatusColor = () => {
    switch (task.status) {
      case 'pending':
        return 'text-yellow-400 bg-yellow-400/10'
      case 'in_progress':
        return 'text-blue-400 bg-blue-400/10'
      case 'completed':
        return 'text-green-400 bg-green-400/10'
      case 'failed':
        return 'text-red-400 bg-red-400/10'
    }
  }

  const getPriorityColor = () => {
    switch (task.priority) {
      case 'low':
        return 'text-gray-400 border-gray-400/30'
      case 'medium':
        return 'text-yellow-400 border-yellow-400/30'
      case 'high':
        return 'text-orange-400 border-orange-400/30'
      case 'critical':
        return 'text-red-400 border-red-400/30'
    }
  }

  const assignedMinions = task.assigned_to.map(id => 
    minions.find(m => m.minion_id === id)
  ).filter(Boolean) as Minion[]

  return (
    <div
      onClick={() => onClick(task)}
      className="bg-black/30 backdrop-blur-md rounded-lg border border-legion-primary/20 p-4
               hover:border-legion-primary/40 transition-all cursor-pointer group"
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-white group-hover:text-legion-accent transition-colors">
            {task.title}
          </h3>
          <div className={`px-2 py-1 rounded-full text-xs ${getStatusColor()} flex items-center gap-1`}>
            {getStatusIcon()}
            <span className="capitalize">{task.status.replace('_', ' ')}</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-gray-300 text-sm line-clamp-2">
          {task.description}
        </p>

        {/* Progress Bar */}
        <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-legion-primary to-legion-accent transition-all duration-500"
            style={{ width: `${task.progress}%` }}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs">
          {/* Priority */}
          <div className={`px-2 py-1 border rounded-full ${getPriorityColor()}`}>
            {task.priority} priority
          </div>

          {/* Assigned Minions */}
          <div className="flex items-center gap-2">
            {assignedMinions.length > 0 && (
              <>
                <Users className="w-3 h-3 text-gray-400" />
                <div className="flex -space-x-2">
                  {assignedMinions.slice(0, 3).map(minion => (
                    <div
                      key={minion.minion_id}
                      className="w-6 h-6 rounded-full bg-gradient-to-br from-legion-primary to-legion-accent
                               border border-black/50 flex items-center justify-center text-[10px] font-bold"
                      title={minion.name}
                    >
                      {minion.name[0]}
                    </div>
                  ))}
                  {assignedMinions.length > 3 && (
                    <div 
                      className="w-6 h-6 rounded-full bg-white/10 border border-black/50 
                               flex items-center justify-center text-[10px] text-gray-300"
                    >
                      +{assignedMinions.length - 3}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Subtasks indicator */}
        {task.subtasks.length > 0 && (
          <div className="pt-2 border-t border-white/10 text-xs text-gray-400">
            {task.subtasks.length} subtask{task.subtasks.length !== 1 ? 's' : ''}
            {expanded && ' (expanded)'}
          </div>
        )}
      </div>
    </div>
  )
}