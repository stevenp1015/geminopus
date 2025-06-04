import { motion } from 'framer-motion'
import { Brain, Zap, Activity, Heart, Shield, Star, Tag, Wrench, Quote, Settings } from 'lucide-react'
import { format } from 'date-fns'
import { Minion, MinionPersona } from '../../types' // Added MinionPersona
import { useState } from 'react' // Added useState
import MinionConfig from '../Configuration/MinionConfig' // Added MinionConfig import
import { minionApi } from '../../services/api/minionApi' // Updated API import
import clsx from 'clsx'

interface MinionDetailProps {
  minion: Minion
}

const MinionDetail = ({ minion }: MinionDetailProps) => {
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false)
  const mood = minion.emotional_state.mood
  const commanderOpinion = minion.emotional_state.opinion_scores['commander']

  const handleSavePersona = async (updatedConfig: Partial<Minion>) => {
    if (!minion?.minion_id || !updatedConfig.persona) return;
    try {
      // We only want to send the persona part for this update
      const personaToUpdate: Partial<MinionPersona> = {
        name: updatedConfig.persona.name,
        base_personality: updatedConfig.persona.base_personality,
        quirks: updatedConfig.persona.quirks,
        catchphrases: updatedConfig.persona.catchphrases,
        allowed_tools: updatedConfig.persona.allowed_tools,
        expertise_areas: updatedConfig.persona.expertise_areas,
        model_name: updatedConfig.persona.model_name,
        temperature: updatedConfig.persona.temperature,
        max_tokens: updatedConfig.persona.max_tokens,
      };
      await minionApi.updatePersona(minion.minion_id, personaToUpdate); // Use minionApi.updatePersona
      // TODO: Add toast notification for success/failure
      // TODO: Potentially refetch minion data or update local state
      setIsConfigModalOpen(false);
    } catch (error) {
      console.error("Failed to update minion persona:", error);
      // TODO: Add toast notification for error
    }
  };
  
  // Calculate mood description
  const getMoodDescription = () => {
    if (mood.valence > 0.5) return 'Elated'
    if (mood.valence > 0.2) return 'Happy'
    if (mood.valence > -0.2) return 'Neutral'
    if (mood.valence > -0.5) return 'Upset'
    return 'Distressed'
  }
  
  const getEnergyDescription = () => {
    const energy = minion.emotional_state.energy_level
    if (energy > 0.8) return 'Energized'
    if (energy > 0.6) return 'Active'
    if (energy > 0.4) return 'Normal'
    if (energy > 0.2) return 'Tired'
    return 'Exhausted'
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-legion-primary/20 space-y-6"
    >
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">{minion.persona?.name || 'Unknown Name'}</h2>
          <p className="text-sm text-gray-400">{minion.minion_id}</p>
          <p className="text-sm text-gray-500 mt-1">
            Spawned {format(new Date(minion.creation_date), 'MMM d, yyyy h:mm a')}
          </p>
        </div>
        <button
          onClick={() => setIsConfigModalOpen(true)}
          className="p-2 hover:bg-legion-primary/20 rounded-lg transition-colors text-gray-400 hover:text-legion-primary"
          title="Configure Minion"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>
      
      {/* Personality */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Personality</h3>
        <p className="text-gray-300 text-sm leading-relaxed">
          {minion.persona?.base_personality || 'No personality defined.'}
        </p>
      </div>
      
      {/* Emotional State */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Emotional State</h3>
        <div className="space-y-3">
          {/* Mood */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-400">Mood</span>
            </div>
            <span className={clsx(
              'text-sm font-medium',
              mood.valence > 0.3 ? 'text-green-400' : 
              mood.valence < -0.3 ? 'text-red-400' : 'text-yellow-400'
            )}>
              {getMoodDescription()}
            </span>
          </div>
          
          {/* Energy */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-400">Energy</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-yellow-400 transition-all"
                  style={{ width: `${minion.emotional_state.energy_level * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-400">
                {getEnergyDescription()}
              </span>
            </div>
          </div>
          
          {/* Stress */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-gray-400">Stress</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-orange-400 transition-all"
                  style={{ width: `${minion.emotional_state.stress_level * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-400">
                {(minion.emotional_state.stress_level * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Commander Opinion */}
      {commanderOpinion && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">Opinion of Commander</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Heart className="w-4 h-4 text-red-400" />
                <span className="text-sm text-gray-400">Affection</span>
              </div>
              <span className="text-sm text-white">{commanderOpinion.affection.toFixed(0)}/100</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-gray-400">Trust</span>
              </div>
              <span className="text-sm text-white">{commanderOpinion.trust.toFixed(0)}/100</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Star className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-gray-400">Respect</span>
              </div>
              <span className="text-sm text-white">{commanderOpinion.respect.toFixed(0)}/100</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Quirks */}
      {(minion.persona?.quirks || []).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-2">Quirks</h3>
          <div className="space-y-1">
            {(minion.persona?.quirks || []).map((quirk: string, index: number) => (
              <div key={index} className="flex items-start space-x-2">
                <Tag className="w-3 h-3 text-legion-accent mt-1 flex-shrink-0" />
                <p className="text-sm text-gray-300">{quirk}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Catchphrases */}
      {(minion.persona?.catchphrases || []).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-2">Catchphrases</h3>
          <div className="space-y-1">
            {(minion.persona?.catchphrases || []).map((phrase: string, index: number) => (
              <div key={index} className="flex items-start space-x-2">
                <Quote className="w-3 h-3 text-legion-primary mt-1 flex-shrink-0" />
                <p className="text-sm text-gray-300 italic">"{phrase}"</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Tools */}
      {(minion.persona?.allowed_tools || []).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-2">Allowed Tools</h3>
          <div className="flex flex-wrap gap-2">
            {(minion.persona?.allowed_tools || []).map((tool: string, index: number) => (
              <div key={index} className="flex items-center space-x-1 bg-legion-primary/20 px-2 py-1 rounded-md">
                <Wrench className="w-3 h-3 text-legion-primary" />
                <span className="text-xs text-gray-300">{tool}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {isConfigModalOpen && minion && (
        <MinionConfig
          minion={minion}
          onSave={handleSavePersona}
          onCancel={() => setIsConfigModalOpen(false)}
        />
      )}
    </motion.div>
  )
}

export default MinionDetail