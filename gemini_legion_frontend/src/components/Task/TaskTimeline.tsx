import { useMemo } from 'react'
import { Calendar, Clock, Users } from 'lucide-react'
import type { Task } from '../../types/task'

interface TaskTimelineProps {
  tasks: Task[]
  onTaskClick: (task: Task) => void
}

export default function TaskTimeline({ tasks, onTaskClick }: TaskTimelineProps) {
  // Group tasks by date
  const groupedTasks = useMemo(() => {
    const groups: Record<string, Task[]> = {}
    
    tasks.forEach(task => {
      const date = new Date(task.created_at).toLocaleDateString()
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(task)
    })
    
    // Sort groups by date
    return Object.entries(groups).sort((a, b) => 
      new Date(b[0]).getTime() - new Date(a[0]).getTime()
    )
  }, [tasks])

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-400'
      case 'in_progress':
        return 'bg-blue-400'
      case 'completed':
        return 'bg-green-400'
      case 'failed':
        return 'bg-red-400'
    }
  }

  const getPriorityIcon = (priority: Task['priority']) => {
    switch (priority) {
      case 'critical':
        return '🔥'
      case 'high':
        return '⚡'
      case 'medium':
        return '📌'
      case 'low':
        return '📋'
    }
  }

  return (
    <div className="space-y-8">
      {groupedTasks.map(([date, dateTasks]) => (
        <div key={date}>
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="w-5 h-5 text-legion-primary" />
            <h3 className="text-lg font-semibold text-white">{date}</h3>
            <div className="flex-1 h-px bg-white/10" />
          </div>
          
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-legion-primary/20" />
            
            {/* Tasks */}
            <div className="space-y-4">
              {dateTasks.map((task, index) => (
                <div key={task.task_id} className="relative flex items-start gap-4">
                  {/* Timeline dot */}
                  <div className={`absolute left-3 w-3 h-3 rounded-full ${getStatusColor(task.status)}
                                 ring-4 ring-black/50 z-10`} />
                  
                  {/* Task card */}
                  <div
                    onClick={() => onTaskClick(task)}
                    className="ml-10 flex-1 bg-black/30 backdrop-blur-md rounded-lg border border-legion-primary/20
                             p-4 hover:border-legion-primary/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{getPriorityIcon(task.priority)}</span>
                          <h4 className="text-white font-semibold group-hover:text-legion-accent transition-colors">
                            {task.title}
                          </h4>
                        </div>
                        <p className="text-gray-400 text-sm mt-1 line-clamp-2">
                          {task.description}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(task.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {/* Progress */}
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-white/5 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-legion-primary to-legion-accent"
                              style={{ width: `${task.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400">{task.progress}%</span>
                        </div>
                        
                        {/* Assigned count */}
                        {task.assigned_to.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-gray-400">
                            <Users className="w-3 h-3" />
                            <span>{task.assigned_to.length}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Status */}
                      <span className={`text-xs capitalize ${
                        task.status === 'completed' ? 'text-green-400' :
                        task.status === 'in_progress' ? 'text-blue-400' :
                        task.status === 'failed' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}