import { motion } from 'framer-motion'
import { Activity, Brain, Zap, MessageCircle } from 'lucide-react'
import { useLegionStore } from '../../store/legionStore'
import { Minion } from '../../store/legionStore'
import clsx from 'clsx'

interface MinionCardProps {
  minion: Minion
}

const MinionCard = ({ minion }: MinionCardProps) => {
  const { selectMinion, selectedMinionId } = useLegionStore()
  const isSelected = selectedMinionId === minion.minion_id
  
  // Calculate mood color based on valence
  const moodColor = minion.emotional_state.mood.valence > 0.3 
    ? 'text-green-400' 
    : minion.emotional_state.mood.valence < -0.3 
    ? 'text-red-400' 
    : 'text-yellow-400'
  
  const statusColors: Record<Minion['status'], string> = {
    active: 'bg-green-400',
    idle: 'bg-yellow-400',
    busy: 'bg-orange-400',
    error: 'bg-red-500',
    rebooting: 'bg-blue-500',
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => selectMinion(minion.minion_id)}
      className={clsx(
        'bg-black/40 backdrop-blur-sm rounded-xl p-6 border cursor-pointer transition-all',
        isSelected 
          ? 'border-legion-primary shadow-lg shadow-legion-primary/20' 
          : 'border-legion-primary/20 hover:border-legion-primary/40'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white">{minion.persona?.name}</h3>
          <p className="text-sm text-gray-400 mt-1">{minion.minion_id}</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={clsx('w-2 h-2 rounded-full', statusColors[minion.status])} />
          <span className="text-xs text-gray-400 capitalize">{minion.status}</span>
        </div>
      </div>
      
      {/* Personality */}
      <p className="text-sm text-gray-300 mb-4 line-clamp-2">
        {minion.persona?.base_personality}
      </p>
      
      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex items-center space-x-2">
          <Brain className={clsx('w-4 h-4', moodColor)} />
          <span className="text-xs text-gray-400">
            Mood: {(minion.emotional_state.mood.valence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span className="text-xs text-gray-400">
            Energy: {(minion.emotional_state.energy_level * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-purple-400" />
          <span className="text-xs text-gray-400">
            Stress: {(minion.emotional_state.stress_level * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <MessageCircle className="w-4 h-4 text-blue-400" />
          <span className="text-xs text-gray-400">
            Memory: {minion.memory_stats?.working_memory_items || 0}
          </span>
        </div>
      </div>
      
      {/* Current Task */}
      {minion.current_task && (
        <div className="mt-4 pt-4 border-t border-legion-primary/10">
          <p className="text-xs text-gray-400">Current Task:</p>
          <p className="text-sm text-white mt-1 line-clamp-1">{minion.current_task.title}</p>
        </div>
      )}
    </motion.div>
  )
}

export default MinionCard