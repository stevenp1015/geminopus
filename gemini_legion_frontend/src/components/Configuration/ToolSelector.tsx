import { useState, useEffect } from 'react'
import { 
  Wrench, Globe, Terminal, FileText, Database, Search, 
  MessageSquare, Brain, Zap, Shield, Check 
} from 'lucide-react'

interface Tool {
  id: string
  name: string
  description: string
  category: 'communication' | 'filesystem' | 'web' | 'analysis' | 'automation'
  icon: any
  requiredPermissions?: string[]
}

interface ToolSelectorProps {
  selectedTools: string[]
  onChange: (tools: string[]) => void
}

const AVAILABLE_TOOLS: Tool[] = [
  {
    id: 'send_message',
    name: 'Send Message',
    description: 'Send messages to channels and other Minions',
    category: 'communication',
    icon: MessageSquare
  },
  {
    id: 'subscribe_channel',
    name: 'Subscribe to Channels',
    description: 'Listen to messages in specific channels',
    category: 'communication',
    icon: MessageSquare
  },
  {
    id: 'autonomous_communication',
    name: 'Autonomous Communication',
    description: 'Initiate conversations based on context',
    category: 'communication',
    icon: Brain
  },
  {
    id: 'read_file',
    name: 'Read Files',
    description: 'Read contents of files in allowed directories',
    category: 'filesystem',
    icon: FileText
  },
  {
    id: 'write_file',
    name: 'Write Files',
    description: 'Create and modify files',
    category: 'filesystem',
    icon: FileText,
    requiredPermissions: ['write_access']
  },
  {
    id: 'web_search',
    name: 'Web Search',
    description: 'Search the internet for information',
    category: 'web',
    icon: Search
  },
  {
    id: 'web_browse',
    name: 'Web Browse',
    description: 'Navigate and interact with web pages',
    category: 'web',
    icon: Globe
  },
  {
    id: 'execute_command',
    name: 'Execute Commands',
    description: 'Run terminal commands',
    category: 'automation',
    icon: Terminal,
    requiredPermissions: ['execute_commands']
  },
  {
    id: 'data_analysis',
    name: 'Data Analysis',
    description: 'Analyze and visualize data',
    category: 'analysis',
    icon: Database
  },
  {
    id: 'task_decomposer',
    name: 'Task Decomposer',
    description: 'Break down complex tasks into subtasks',
    category: 'analysis',
    icon: Zap
  }
]

const CATEGORY_LABELS = {
  communication: 'Communication',
  filesystem: 'File System',
  web: 'Web & Internet',
  analysis: 'Analysis & Processing',
  automation: 'Automation'
}

export default function ToolSelector({ selectedTools, onChange }: ToolSelectorProps) {
  const [filter, setFilter] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const filteredTools = AVAILABLE_TOOLS.filter(tool => {
    if (selectedCategory && tool.category !== selectedCategory) return false
    if (filter && !tool.name.toLowerCase().includes(filter.toLowerCase()) &&
        !tool.description.toLowerCase().includes(filter.toLowerCase())) return false
    return true
  })

  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      onChange(selectedTools.filter(id => id !== toolId))
    } else {
      onChange([...selectedTools, toolId])
    }
  }

  const toggleCategory = (category: string) => {
    const categoryTools = AVAILABLE_TOOLS.filter(t => t.category === category)
    const allSelected = categoryTools.every(t => selectedTools.includes(t.id))
    
    if (allSelected) {
      onChange(selectedTools.filter(id => !categoryTools.some(t => t.id === id)))
    } else {
      const newTools = categoryTools.map(t => t.id)
      onChange([...new Set([...selectedTools, ...newTools])])
    }
  }

  const groupedTools = filteredTools.reduce((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = []
    acc[tool.category].push(tool)
    return acc
  }, {} as Record<string, Tool[]>)

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search tools..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                     text-white placeholder-gray-400 focus:border-legion-primary/50 focus:outline-none"
          />
        </div>
        <select
          value={selectedCategory || ''}
          onChange={(e) => setSelectedCategory(e.target.value || null)}
          className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg
                   text-white focus:border-legion-primary/50 focus:outline-none"
        >
          <option value="">All Categories</option>
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>

      {/* Selected Count */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-400">
          {selectedTools.length} tools selected
        </span>
        <button
          onClick={() => onChange([])}
          className="text-red-400 hover:text-red-300 transition-colors"
        >
          Clear all
        </button>
      </div>

      {/* Tool Categories */}
      <div className="space-y-4">
        {Object.entries(groupedTools).map(([category, tools]) => {
          const categoryKey = category as keyof typeof CATEGORY_LABELS
          const allSelected = tools.every(t => selectedTools.includes(t.id))
          const someSelected = tools.some(t => selectedTools.includes(t.id))
          
          return (
            <div key={category} className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-white">
                  {CATEGORY_LABELS[categoryKey]}
                </h3>
                <button
                  onClick={() => toggleCategory(category)}
                  className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                    allSelected
                      ? 'bg-legion-primary text-white'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  {allSelected ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tools.map(tool => {
                  const Icon = tool.icon
                  const isSelected = selectedTools.includes(tool.id)
                  
                  return (
                    <button
                      key={tool.id}
                      onClick={() => toggleTool(tool.id)}
                      className={`flex items-start space-x-3 p-3 rounded-lg transition-all ${
                        isSelected
                          ? 'bg-legion-primary/20 border-legion-primary'
                          : 'bg-white/5 border-white/10 hover:bg-white/10'
                      } border`}
                    >
                      <div className={`mt-0.5 ${isSelected ? 'text-legion-primary' : 'text-gray-400'}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 text-left">
                        <div className="flex items-center justify-between">
                          <h4 className={`font-medium ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                            {tool.name}
                          </h4>
                          {isSelected && (
                            <Check className="w-4 h-4 text-legion-primary" />
                          )}
                        </div>
                        <p className="text-sm text-gray-400 mt-1">
                          {tool.description}
                        </p>
                        {tool.requiredPermissions && (
                          <div className="flex items-center space-x-1 mt-2">
                            <Shield className="w-3 h-3 text-yellow-500" />
                            <span className="text-xs text-yellow-500">
                              Requires: {tool.requiredPermissions.join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}