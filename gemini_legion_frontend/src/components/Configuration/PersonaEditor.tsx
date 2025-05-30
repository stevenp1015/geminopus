import { useState } from 'react'
import { Plus, X, Hash, Sparkles, BookOpen, Quote } from 'lucide-react'
import type { MinionPersona } from '../../types/minion'

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
    updatePersona({ quirks: persona.quirks.filter((_, i) => i !== index) })
  }

  const addCatchphrase = () => {
    if (newCatchphrase.trim()) {
      updatePersona({ catchphrases: [...persona.catchphrases, newCatchphrase.trim()] })
      setNewCatchphrase('')
    }
  }

  const removeCatchphrase = (index: number) => {
    updatePersona({ catchphrases: persona.catchphrases.filter((_, i) => i !== index) })
  }

  const addExpertise = () => {
    if (newExpertise.trim()) {
      updatePersona({ expertise_areas: [...persona.expertise_areas, newExpertise.trim()] })
      setNewExpertise('')
    }
  }

  const removeExpertise = (index: number) => {
    updatePersona({ expertise_areas: persona.expertise_areas.filter((_, i) => i !== index) })
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
          {persona.quirks.map((quirk, i) => (
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
          {persona.catchphrases.map((phrase, i) => (
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
          {persona.expertise_areas.map((area, i) => (
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
          <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
          <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
          <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
        </select>
      </div>
    </div>
  )
}