import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, User, Zap, Brain, Heart } from 'lucide-react'
import { format } from 'date-fns'
import { Message, Minion } from '../../types'

interface MessageListProps {
  messages: Message[]
  minions: Record<string, Minion>
  currentUserId?: string
}

const MessageList = ({ messages, minions, currentUserId }: MessageListProps) => {
  const scrollRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])
  
  const getMoodColor = (mood: number) => {
    // Map mood valence (-1 to 1) to color
    if (mood > 0.5) return 'text-green-400'
    if (mood > 0) return 'text-blue-400'
    if (mood > -0.5) return 'text-yellow-400'
    return 'text-red-400'
  }
  
  const getEnergyIcon = (energy: number) => {
    if (energy > 0.7) return '⚡'
    if (energy > 0.3) return '🔋'
    return '🪫'
  }
  
  return (
    <div 
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-legion-primary/20 scrollbar-track-transparent"
    >
      <AnimatePresence initial={false}>
        {messages.map((message) => {
          const minion = message.sender_type === 'minion' ? minions[message.sender_id] : null
          const isCurrentUser = message.sender_id === currentUserId
          
          return (
            <motion.div
              key={message.message_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'} mb-4`}
            >
              <div className={`flex space-x-3 max-w-[70%] ${isCurrentUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
                {/* Avatar */}
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    minion ? 'bg-legion-primary/20 border border-legion-primary/40' : 'bg-gray-700'
                  }`}>
                    {minion ? (
                      <Bot className="w-6 h-6 text-legion-primary" />
                    ) : (
                      <User className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                </div>
                
                {/* Message Content */}
                <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'}`}>
                  {/* Header */}
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-semibold text-white">
                      {minion ? minion.persona.name : 'Commander'}
                    </span>
                    {minion && (
                      <>
                        <span className={`text-xs ${getMoodColor(minion.emotional_state.mood.valence)}`}>
                          <Heart className="w-3 h-3 inline" />
                        </span>
                        <span className="text-xs text-gray-500">
                          {getEnergyIcon(minion.emotional_state.energy_level)}
                        </span>
                      </>
                    )}
                    <span className="text-xs text-gray-600">
                      {format(new Date(message.timestamp), 'HH:mm')}
                    </span>
                  </div>
                  
                  {/* Message Bubble */}
                  <div className={`relative group ${
                    isCurrentUser 
                      ? 'bg-legion-primary/20 border border-legion-primary/40' 
                      : 'bg-black/40 border border-gray-700'
                  } rounded-lg px-4 py-2 backdrop-blur-sm`}>
                    <p className="text-white whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                    
                    {/* Personality Hint */}
                    {minion && message.metadata?.personality_hint && (
                      <div className="absolute -bottom-2 left-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-xs text-gray-500 italic">
                          {message.metadata.personality_hint}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* Emotional Impact Indicator */}
                  {minion && message.metadata?.emotional_impact && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-1 flex items-center space-x-1"
                    >
                      <Brain className="w-3 h-3 text-purple-400" />
                      <span className="text-xs text-purple-400">
                        {message.metadata.emotional_impact > 0 ? '+' : ''}
                        {(message.metadata.emotional_impact * 100).toFixed(0)}% mood
                      </span>
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
      
      {/* Typing Indicators */}
      {/* TODO: Add typing indicators for minions */}
    </div>
  )
}

export default MessageList