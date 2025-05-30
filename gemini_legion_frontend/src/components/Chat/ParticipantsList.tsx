import { motion } from 'framer-motion'
import { Bot, Zap, Heart, Brain, Crown } from 'lucide-react'
import { Minion } from '../../types'

interface ParticipantsListProps {
  participants: Minion[]
  channelName: string
}

const ParticipantsList = ({ participants, channelName }: ParticipantsListProps) => {
  const getMoodIndicator = (mood: number) => {
    if (mood > 0.5) return { color: 'text-green-400', label: 'Happy' }
    if (mood > 0) return { color: 'text-blue-400', label: 'Content' }
    if (mood > -0.5) return { color: 'text-yellow-400', label: 'Neutral' }
    return { color: 'text-red-400', label: 'Stressed' }
  }
  
  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'active':
        return { color: 'bg-green-400', pulse: true }
      case 'idle':
        return { color: 'bg-yellow-400', pulse: false }
      case 'busy':
        return { color: 'bg-red-400', pulse: false }
      default:
        return { color: 'bg-gray-400', pulse: false }
    }
  }
  
  // Sort participants by status (active first) then by name
  const sortedParticipants = [...participants].sort((a, b) => {
    if (a.status === 'active' && b.status !== 'active') return -1
    if (a.status !== 'active' && b.status === 'active') return 1
    return a.persona.name.localeCompare(b.persona.name)
  })
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-legion-primary/10">
        <h3 className="font-semibold text-white">Participants</h3>
        <p className="text-sm text-gray-400 mt-1">{participants.length} in #{channelName}</p>
      </div>
      
      {/* Participants List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-legion-primary/20 scrollbar-track-transparent">
        {sortedParticipants.map((minion) => {
          const mood = getMoodIndicator(minion.emotional_state.mood.valence)
          const status = getStatusIndicator(minion.status)
          
          return (
            <motion.div
              key={minion.minion_id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start space-x-3 p-3 bg-black/20 rounded-lg hover:bg-black/30 transition-colors"
            >
              {/* Avatar with Status */}
              <div className="relative flex-shrink-0">
                <div className="w-10 h-10 bg-legion-primary/20 border border-legion-primary/40 rounded-full flex items-center justify-center">
                  <Bot className="w-6 h-6 text-legion-primary" />
                </div>
                <div className={`absolute -bottom-1 -right-1 w-3 h-3 ${status.color} rounded-full border-2 border-black`}>
                  {status.pulse && (
                    <div className={`absolute inset-0 ${status.color} rounded-full animate-ping`} />
                  )}
                </div>
              </div>
              
              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <p className="font-medium text-white truncate">{minion.persona.name}</p>
                  {minion.minion_id === 'commander' && (
                    <Crown className="w-4 h-4 text-yellow-400" />
                  )}
                </div>
                
                {/* Role/Personality */}
                <p className="text-xs text-gray-400 truncate mt-0.5">
                  {minion.persona.base_personality.split(' ').slice(0, 5).join(' ')}...
                </p>
                
                {/* Stats */}
                <div className="flex items-center space-x-3 mt-2">
                  <div className="flex items-center space-x-1">
                    <Heart className={`w-3 h-3 ${mood.color}`} />
                    <span className={`text-xs ${mood.color}`}>{mood.label}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Zap className="w-3 h-3 text-yellow-400" />
                    <span className="text-xs text-yellow-400">
                      {(minion.emotional_state.energy_level * 100).toFixed(0)}%
                    </span>
                  </div>
                  {minion.emotional_state.stress_level > 0.5 && (
                    <div className="flex items-center space-x-1">
                      <Brain className="w-3 h-3 text-red-400" />
                      <span className="text-xs text-red-400">Stressed</span>
                    </div>
                  )}
                </div>
                
                {/* Current Task */}
                {minion.current_task && (
                  <div className="mt-2 text-xs text-gray-500">
                    Working on: <span className="text-gray-400">{minion.current_task.title}</span>
                  </div>
                )}
              </div>
            </motion.div>
          )
        })}
        
        {participants.length === 0 && (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">No participants yet</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ParticipantsList