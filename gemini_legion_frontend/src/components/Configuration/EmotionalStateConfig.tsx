import { useState } from 'react'
import { 
  Heart, Zap, Brain, Users, Sparkles, TrendingUp, 
  Frown, Smile, Meh, AlertCircle, Activity 
} from 'lucide-react'
import type { EmotionalState, MoodVector } from '../../types/minion'

interface EmotionalStateConfigProps {
  emotionalState: EmotionalState
  onChange: (state: EmotionalState) => void
}

interface MoodSliderProps {
  label: string
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  icon: any
  color: string
  description?: string
}

function MoodSlider({ label, value, onChange, min, max, icon: Icon, color, description }: MoodSliderProps) {
  const percentage = ((value - min) / (max - min)) * 100

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Icon className={`w-4 h-4 ${color}`} />
          <span className="text-sm font-medium text-gray-300">{label}</span>
        </div>
        <span className="text-sm text-gray-400">{value.toFixed(1)}</span>
      </div>
      <div className="relative">
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div 
            className={`h-full ${color.replace('text-', 'bg-')} transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={0.1}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />
      </div>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
    </div>
  )
}

export default function EmotionalStateConfig({ emotionalState, onChange }: EmotionalStateConfigProps) {
  const updateMood = (updates: Partial<MoodVector>) => {
    onChange({
      ...emotionalState,
      mood: { ...emotionalState.mood, ...updates }
    })
  }

  const updateEnergyLevel = (energy_level: number) => {
    onChange({ ...emotionalState, energy_level })
  }

  const updateStressLevel = (stress_level: number) => {
    onChange({ ...emotionalState, stress_level })
  }

  const getValenceIcon = () => {
    if (emotionalState.mood.valence > 0.3) return Smile
    if (emotionalState.mood.valence < -0.3) return Frown
    return Meh
  }

  const ValenceIcon = getValenceIcon()

  return (
    <div className="space-y-6">
      {/* Mood State Overview */}
      <div className="bg-white/5 rounded-lg p-4">
        <h3 className="text-lg font-medium text-white mb-4">Current Emotional State</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="text-center">
            <ValenceIcon className="w-8 h-8 mx-auto mb-2 text-legion-primary" />
            <p className="text-sm text-gray-300">
              {emotionalState.mood.valence > 0.3 ? 'Positive' : 
               emotionalState.mood.valence < -0.3 ? 'Negative' : 'Neutral'}
            </p>
          </div>
          <div className="text-center">
            <Activity className={`w-8 h-8 mx-auto mb-2 ${
              emotionalState.energy_level > 0.7 ? 'text-yellow-400' : 
              emotionalState.energy_level < 0.3 ? 'text-gray-500' : 'text-blue-400'
            }`} />
            <p className="text-sm text-gray-300">
              {emotionalState.energy_level > 0.7 ? 'High Energy' : 
               emotionalState.energy_level < 0.3 ? 'Low Energy' : 'Moderate Energy'}
            </p>
          </div>
          <div className="text-center">
            <AlertCircle className={`w-8 h-8 mx-auto mb-2 ${
              emotionalState.stress_level > 0.7 ? 'text-red-400' : 
              emotionalState.stress_level < 0.3 ? 'text-green-400' : 'text-yellow-400'
            }`} />
            <p className="text-sm text-gray-300">
              {emotionalState.stress_level > 0.7 ? 'High Stress' : 
               emotionalState.stress_level < 0.3 ? 'Low Stress' : 'Moderate Stress'}
            </p>
          </div>
        </div>
      </div>

      {/* Core Mood Dimensions */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Core Mood Dimensions</h3>
        <div className="space-y-4">
          <MoodSlider
            label="Valence"
            value={emotionalState.mood.valence}
            onChange={(v) => updateMood({ valence: v })}
            min={-1}
            max={1}
            icon={Heart}
            color="text-pink-400"
            description="Emotional positivity/negativity (-1 = very negative, 1 = very positive)"
          />
          
          <MoodSlider
            label="Arousal"
            value={emotionalState.mood.arousal}
            onChange={(v) => updateMood({ arousal: v })}
            min={0}
            max={1}
            icon={Zap}
            color="text-yellow-400"
            description="Level of activation/excitement (0 = calm, 1 = highly activated)"
          />
          
          <MoodSlider
            label="Dominance"
            value={emotionalState.mood.dominance}
            onChange={(v) => updateMood({ dominance: v })}
            min={0}
            max={1}
            icon={TrendingUp}
            color="text-purple-400"
            description="Feeling of control/influence (0 = submissive, 1 = dominant)"
          />
        </div>
      </div>

      {/* Secondary Dimensions */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Secondary Dimensions</h3>
        <div className="space-y-4">
          <MoodSlider
            label="Curiosity"
            value={emotionalState.mood.curiosity}
            onChange={(v) => updateMood({ curiosity: v })}
            min={0}
            max={1}
            icon={Brain}
            color="text-blue-400"
          />
          
          <MoodSlider
            label="Creativity"
            value={emotionalState.mood.creativity}
            onChange={(v) => updateMood({ creativity: v })}
            min={0}
            max={1}
            icon={Sparkles}
            color="text-indigo-400"
          />
          
          <MoodSlider
            label="Sociability"
            value={emotionalState.mood.sociability}
            onChange={(v) => updateMood({ sociability: v })}
            min={0}
            max={1}
            icon={Users}
            color="text-green-400"
          />
        </div>
      </div>

      {/* Energy and Stress */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Energy & Stress Levels</h3>
        <div className="space-y-4">
          <MoodSlider
            label="Energy Level"
            value={emotionalState.energy_level}
            onChange={updateEnergyLevel}
            min={0}
            max={1}
            icon={Activity}
            color="text-orange-400"
            description="Overall energy and capacity for action"
          />
          
          <MoodSlider
            label="Stress Level"
            value={emotionalState.stress_level}
            onChange={updateStressLevel}
            min={0}
            max={1}
            icon={AlertCircle}
            color="text-red-400"
            description="Current stress and pressure levels"
          />
        </div>
      </div>

      {/* Emotional State Presets */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Quick Presets</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => onChange({
              ...emotionalState,
              mood: {
                valence: 0.7,
                arousal: 0.6,
                dominance: 0.5,
                curiosity: 0.8,
                creativity: 0.7,
                sociability: 0.7
              },
              energy_level: 0.8,
              stress_level: 0.2
            })}
            className="p-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 rounded-lg transition-colors"
          >
            <Smile className="w-5 h-5 mx-auto mb-1 text-green-400" />
            <span className="text-sm text-green-300">Enthusiastic</span>
          </button>
          
          <button
            onClick={() => onChange({
              ...emotionalState,
              mood: {
                valence: 0.0,
                arousal: 0.3,
                dominance: 0.3,
                curiosity: 0.5,
                creativity: 0.5,
                sociability: 0.5
              },
              energy_level: 0.5,
              stress_level: 0.3
            })}
            className="p-3 bg-gray-500/20 hover:bg-gray-500/30 border border-gray-500/50 rounded-lg transition-colors"
          >
            <Meh className="w-5 h-5 mx-auto mb-1 text-gray-400" />
            <span className="text-sm text-gray-300">Neutral</span>
          </button>
          
          <button
            onClick={() => onChange({
              ...emotionalState,
              mood: {
                valence: -0.3,
                arousal: 0.7,
                dominance: 0.2,
                curiosity: 0.3,
                creativity: 0.2,
                sociability: 0.2
              },
              energy_level: 0.4,
              stress_level: 0.8
            })}
            className="p-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg transition-colors"
          >
            <AlertCircle className="w-5 h-5 mx-auto mb-1 text-red-400" />
            <span className="text-sm text-red-300">Stressed</span>
          </button>
          
          <button
            onClick={() => onChange({
              ...emotionalState,
              mood: {
                valence: 0.2,
                arousal: 0.8,
                dominance: 0.6,
                curiosity: 0.9,
                creativity: 0.8,
                sociability: 0.6
              },
              energy_level: 0.7,
              stress_level: 0.4
            })}
            className="p-3 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/50 rounded-lg transition-colors"
          >
            <Brain className="w-5 h-5 mx-auto mb-1 text-purple-400" />
            <span className="text-sm text-purple-300">Focused</span>
          </button>
        </div>
      </div>
    </div>
  )
}