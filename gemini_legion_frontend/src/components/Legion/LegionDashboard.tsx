import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Users, Activity, Brain, Zap } from 'lucide-react'
import { useLegionStore } from '../../store/legionStore'
import MinionCard from './MinionCard'
import MinionDetail from './MinionDetail'
import SpawnMinionModal from './SpawnMinionModal'

const LegionDashboard = () => {
  const { minions, selectedMinionId } = useLegionStore()
  const [showSpawnModal, setShowSpawnModal] = useState(false)
  
  const minionList = Object.values(minions)
  const selectedMinion = selectedMinionId ? minions[selectedMinionId] : null
  
  // Calculate stats
  const activeMinions = minionList.filter(m => m.status === 'active').length
  const totalTasks = minionList.reduce((sum, m) => sum + (m.current_task ? 1 : 0), 0)
  const avgEnergyLevel = minionList.reduce((sum, m) => sum + m.emotional_state.energy_level, 0) / (minionList.length || 1)
  const avgStressLevel = minionList.reduce((sum, m) => sum + m.emotional_state.stress_level, 0) / (minionList.length || 1)
  
  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-legion-primary/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Minions</p>
              <p className="text-3xl font-bold text-white mt-1">{minionList.length}</p>
            </div>
            <Users className="w-8 h-8 text-legion-primary" />
          </div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-legion-primary/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active Now</p>
              <p className="text-3xl font-bold text-white mt-1">{activeMinions}</p>
            </div>
            <Activity className="w-8 h-8 text-green-400" />
          </div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-legion-primary/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Energy</p>
              <p className="text-3xl font-bold text-white mt-1">{(avgEnergyLevel * 100).toFixed(0)}%</p>
            </div>
            <Zap className="w-8 h-8 text-yellow-400" />
          </div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-legion-primary/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Stress</p>
              <p className="text-3xl font-bold text-white mt-1">{(avgStressLevel * 100).toFixed(0)}%</p>
            </div>
            <Brain className="w-8 h-8 text-purple-400" />
          </div>
        </motion.div>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Minion List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">Legion Members</h2>
            <button
              onClick={() => setShowSpawnModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-legion-primary hover:bg-legion-primary/80 text-white rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>Spawn Minion</span>
            </button>
          </div>
          
          <AnimatePresence mode="popLayout">
            {minionList.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center py-12 bg-black/20 rounded-xl border border-legion-primary/10"
              >
                <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No minions spawned yet</p>
                <p className="text-gray-500 text-sm mt-2">Click "Spawn Minion" to begin building your Legion</p>
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {minionList.map((minion) => (
                  <MinionCard key={minion.minion_id} minion={minion} />
                ))}
              </div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Minion Detail */}
        <div className="lg:col-span-1">
          {selectedMinion ? (
            <MinionDetail minion={selectedMinion} />
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-black/40 backdrop-blur-sm rounded-xl p-8 border border-legion-primary/20 text-center"
            >
              <Brain className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Select a minion to view details</p>
            </motion.div>
          )}
        </div>
      </div>
      
      {/* Spawn Modal */}
      <AnimatePresence>
        {showSpawnModal && (
          <SpawnMinionModal onClose={() => setShowSpawnModal(false)} />
        )}
      </AnimatePresence>
    </div>
  )
}

export default LegionDashboard