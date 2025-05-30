import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Plus, Trash2, Sparkles } from 'lucide-react'
import { useLegionStore } from '../../store/legionStore'
import toast from 'react-hot-toast'

interface SpawnMinionModalProps {
  onClose: () => void
}

const SpawnMinionModal = ({ onClose }: SpawnMinionModalProps) => {
  const { spawnMinion } = useLegionStore()
  
  const [formData, setFormData] = useState({
    name: '',
    base_personality: '',
    quirks: [''],
    catchphrases: [''],
    expertise_areas: [''],
    allowed_tools: ['']
  })
  
  const [isSpawning, setIsSpawning] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name || !formData.base_personality) {
      toast.error('Name and personality are required!')
      return
    }
    
    setIsSpawning(true)
    
    try {
      const cleanedData = {
        name: formData.name,
        base_personality: formData.base_personality,
        quirks: formData.quirks.filter(q => q.trim()),
        catchphrases: formData.catchphrases.filter(c => c.trim()),
        expertise_areas: formData.expertise_areas.filter(e => e.trim()),
        allowed_tools: formData.allowed_tools.filter(t => t.trim())
      }
      
      await spawnMinion(cleanedData)
      onClose()
    } catch (error) {
      console.error('Failed to spawn minion:', error)
    } finally {
      setIsSpawning(false)
    }
  }
  
  const addField = (field: 'quirks' | 'catchphrases' | 'expertise_areas' | 'allowed_tools') => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }))
  }
  
  const removeField = (field: 'quirks' | 'catchphrases' | 'expertise_areas' | 'allowed_tools', index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }))
  }
  
  const updateField = (field: 'quirks' | 'catchphrases' | 'expertise_areas' | 'allowed_tools', index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }))
  }
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-legion-dark rounded-xl border border-legion-primary/20 p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-6 h-6 text-legion-primary" />
              <span>Spawn New Minion</span>
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full bg-black/50 border border-legion-primary/30 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-legion-primary"
                placeholder="e.g. TaskMaster Prime"
                required
              />
            </div>
            
            {/* Base Personality */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Base Personality *
              </label>
              <textarea
                value={formData.base_personality}
                onChange={(e) => setFormData(prev => ({ ...prev, base_personality: e.target.value }))}
                className="w-full bg-black/50 border border-legion-primary/30 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-legion-primary min-h-[100px]"
                placeholder="e.g. Obsessively organized task orchestrator who breaks down complex problems with surgical precision"
                required
              />
            </div>
            
            {/* Quirks */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Quirks
              </label>
              {formData.quirks.map((quirk, index) => (
                <div key={index} className="flex items-center space-x-2 mb-2">
                  <input
                    type="text"
                    value={quirk}
                    onChange={(e) => updateField('quirks', index, e.target.value)}
                    className="flex-1 bg-black/50 border border-legion-primary/30 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-legion-primary"
                    placeholder="e.g. Creates detailed task breakdowns even for simple requests"
                  />
                  <button
                    type="button"
                    onClick={() => removeField('quirks', index)}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => addField('quirks')}
                className="flex items-center space-x-1 text-legion-primary hover:text-legion-primary/80 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm">Add Quirk</span>
              </button>
            </div>
            
            {/* Catchphrases */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Catchphrases
              </label>
              {formData.catchphrases.map((phrase, index) => (
                <div key={index} className="flex items-center space-x-2 mb-2">
                  <input
                    type="text"
                    value={phrase}
                    onChange={(e) => updateField('catchphrases', index, e.target.value)}
                    className="flex-1 bg-black/50 border border-legion-primary/30 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-legion-primary"
                    placeholder="e.g. By any means necessary!"
                  />
                  <button
                    type="button"
                    onClick={() => removeField('catchphrases', index)}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => addField('catchphrases')}
                className="flex items-center space-x-1 text-legion-primary hover:text-legion-primary/80 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm">Add Catchphrase</span>
              </button>
            </div>
            
            {/* Buttons */}
            <div className="flex items-center justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSpawning}
                className="px-6 py-2 bg-legion-primary hover:bg-legion-primary/80 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSpawning ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span>Spawning...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Spawn Minion</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default SpawnMinionModal