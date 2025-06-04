import { useState } from 'react'
import { Plus, X, Hash, Sparkles, BookOpen, Quote } from 'lucide-react'
import type { MinionPersona } from '@/types'

interface PersonaEditorProps {
  persona: MinionPersona
  onChange: (persona: MinionPersona) => void
}

export default function PersonaEditor({ persona, onChange }: PersonaEditorProps) {
  const [newQuirk, setNewQuirk] = useState('')
  const [newCatchphrase, setNewCatchphrase] = useState('')
  const [newExpertise, setNewExpertise] = useState('')

  const updatePersona = (updates: Partial<MinionPersona>) => {
    onChange({ ...persona, ...updates })
  }

  const addQuirk = () => {
    if (newQuirk.trim()) {
      updatePersona({ quirks: [...persona.quirks, newQuirk.trim()] })
      setNewQuirk('')
    }
  }

  const removeQuirk = (index: number) => {
    updatePersona({ quirks: persona.quirks.filter((_: string, i: number) => i !== index) })
  }

  const addCatchphrase = () => {
    if (newCatchphrase.trim()) {
      updatePersona({ catchphrases: [...persona.catchphrases, newCatchphrase.trim()] })
      setNewCatchphrase('')
    }
  }

  const removeCatchphrase = (index: number) => {
    updatePersona({ catchphrases: persona.catchphrases.filter((_: string, i: number) => i !== index) })
  }

  const addExpertise = () => {
    if (newExpertise.trim()) {
      updatePersona({ expertise_areas: [...persona.expertise_areas, newExpertise.trim()] })
      setNewExpertise('')
    }
  }

  const removeExpertise = (index: number) => {
    updatePersona({ expertise_areas: persona.expertise_areas.filter((_: string, i: number) => i !== index) })
  }

  return (
    <div className="space-y-6">
      {/* Base Personality */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Base Personality
        </label>
        <textarea
          value={persona.base_personality}
          onChange={(e) => updatePersona({ base_personality: e.target.value })}
          className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-lg
                   text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none resize-none"
          placeholder="Describe the core personality traits..."
        />
      </div>

      {/* Quirks */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <Sparkles className="w-4 h-4 text-legion-primary" />
          <label className="text-sm font-medium text-gray-300">Personality Quirks</label>
        </div>
        <div className="space-y-2 mb-3">
          {persona.quirks.map((quirk: string, i: number) => (
            <div key={i} className="flex items-center space-x-2 bg-white/5 px-3 py-2 rounded-lg">
              <span className="flex-1 text-sm text-gray-300">{quirk}</span>
              <button
                onClick={() => removeQuirk(i)}
                className="p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <X className="w-4 h-4 text-red-400" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newQuirk}
            onChange={(e) => setNewQuirk(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addQuirk()}
            placeholder="Add a personality quirk..."
            className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg
                     text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
          />
          <button
            onClick={addQuirk}
            className="p-2 bg-legion-primary/20 hover:bg-legion-primary/30 text-legion-primary rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Catchphrases */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <Quote className="w-4 h-4 text-legion-primary" />
          <label className="text-sm font-medium text-gray-300">Catchphrases</label>
        </div>
        <div className="space-y-2 mb-3">
          {persona.catchphrases.map((phrase: string, i: number) => (
            <div key={i} className="flex items-center space-x-2 bg-white/5 px-3 py-2 rounded-lg">
              <span className="flex-1 text-sm text-gray-300 italic">"{phrase}"</span>
              <button
                onClick={() => removeCatchphrase(i)}
                className="p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <X className="w-4 h-4 text-red-400" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newCatchphrase}
            onChange={(e) => setNewCatchphrase(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCatchphrase()}
            placeholder="Add a catchphrase..."
            className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg
                     text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
          />
          <button
            onClick={addCatchphrase}
            className="p-2 bg-legion-primary/20 hover:bg-legion-primary/30 text-legion-primary rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Expertise Areas */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <BookOpen className="w-4 h-4 text-legion-primary" />
          <label className="text-sm font-medium text-gray-300">Areas of Expertise</label>
        </div>
        <div className="space-y-2 mb-3">
          {persona.expertise_areas.map((area: string, i: number) => (
            <div key={i} className="flex items-center space-x-2 bg-white/5 px-3 py-2 rounded-lg">
              <Hash className="w-3 h-3 text-legion-primary" />
              <span className="flex-1 text-sm text-gray-300">{area}</span>
              <button
                onClick={() => removeExpertise(i)}
                className="p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <X className="w-4 h-4 text-red-400" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newExpertise}
            onChange={(e) => setNewExpertise(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addExpertise()}
            placeholder="Add an area of expertise..."
            className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg
                     text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
          />
          <button
            onClick={addExpertise}
            className="p-2 bg-legion-primary/20 hover:bg-legion-primary/30 text-legion-primary rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          AI Model
        </label>
        <select
          value={persona.model_name}
          onChange={(e) => updatePersona({ model_name: e.target.value })}
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                   text-white focus:border-legion-primary/50 focus:outline-none"
        >
          <option value="gemini-2.5-pro-preview-05-06">Gemini 2.5 Pro Preview 05-06</option>
          <option value="gemini-2.5-flash-preview-05-20">Gemini 2.5 Flash Preview 05-20</option>
          <option value="gemini-2.5-flash-preview-04-17">Gemini 2.5 Flash Preview 04-17</option>
          <option value="gemini-2.0-flash-lite">Gemini 2.0 Flash Lite</option>
        </select>
      </div>

      {/* Temperature */}
      <div className="mt-4">
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-300 mb-2">
          Temperature
        </label>
        <input
          type="number"
          id="temperature"
          name="temperature"
          value={persona.temperature ?? 0.7}
          onChange={(e) => updatePersona({ temperature: parseFloat(e.target.value) })}
          step="0.1"
          min="0"
          max="2"
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                   text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
        />
        <p className="text-xs text-gray-500 mt-1">Controls randomness. Lower is more deterministic. (0.0 - 2.0)</p>
      </div>

      {/* Max Tokens */}
      <div className="mt-4">
        <label htmlFor="max_tokens" className="block text-sm font-medium text-gray-300 mb-2">
          Max Tokens
        </label>
        <input
          type="number"
          id="max_tokens"
          name="max_tokens"
          value={persona.max_tokens ?? 4096}
          onChange={(e) => updatePersona({ max_tokens: parseInt(e.target.value, 10) })}
          step="1"
          min="1"
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                   text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
        />
        <p className="text-xs text-gray-500 mt-1">Maximum number of tokens to generate in the response.</p>
      </div>
    </div>
  )
}