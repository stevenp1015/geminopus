import { useState, useEffect } from 'react'
import { Save, X, Plus, Trash2, Brain, Zap, MessageSquare } from 'lucide-react'
import type { Minion } from '../../types/minion'
import PersonaEditor from './PersonaEditor'
import ToolSelector from './ToolSelector'
import EmotionalStateConfig from './EmotionalStateConfig'

interface MinionConfigProps {
  minion: Minion
  onSave: (config: Partial<Minion>) => void
  onCancel: () => void
}

export default function MinionConfig({ minion, onSave, onCancel }: MinionConfigProps) {
  const [config, setConfig] = useState<Partial<Minion>>({
    name: minion.name,
    persona: { ...minion.persona },
    emotional_state: { ...minion.emotional_state }
  })
  
  const [activeTab, setActiveTab] = useState<'persona' | 'tools' | 'emotional'>('persona')
  const [hasChanges, setHasChanges] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Check if there are any changes
    const hasPersonaChanges = JSON.stringify(config.persona) !== JSON.stringify(minion.persona)
    const hasEmotionalChanges = JSON.stringify(config.emotional_state) !== JSON.stringify(minion.emotional_state)
    setHasChanges(hasPersonaChanges || hasEmotionalChanges)
  }, [config, minion])

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(config)
    } finally {
      setSaving(false)
    }
  }

  const tabs = [
    { id: 'persona', label: 'Persona', icon: Brain },
    { id: 'tools', label: 'Tools & Capabilities', icon: Zap },
    { id: 'emotional', label: 'Emotional State', icon: MessageSquare }
  ]

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 rounded-lg border border-legion-primary/20 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-2xl font-bold text-white">Configure {minion.name}</h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-white/10">
          <div className="flex">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 transition-colors ${
                    activeTab === tab.id
                      ? 'bg-legion-primary/20 text-legion-primary border-b-2 border-legion-primary'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'persona' && (
            <PersonaEditor
              persona={config.persona!}
              onChange={(persona) => setConfig({ ...config, persona })}
            />
          )}
          
          {activeTab === 'tools' && (
            <ToolSelector
              selectedTools={config.persona?.allowed_tools || []}
              onChange={(tools) => setConfig({
                ...config,
                persona: { ...config.persona!, allowed_tools: tools }
              })}
            />
          )}
          
          {activeTab === 'emotional' && (
            <EmotionalStateConfig
              emotionalState={config.emotional_state!}
              onChange={(emotional_state) => setConfig({ ...config, emotional_state })}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-white/10">
          <div className="text-sm text-gray-400">
            {hasChanges && "You have unsaved changes"}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || saving}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}