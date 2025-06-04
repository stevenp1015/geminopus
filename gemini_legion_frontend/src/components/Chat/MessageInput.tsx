import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Send, Zap, Heart, AlertCircle, Sparkles } from 'lucide-react'
import { useChatStore, COMMANDER_ID } from '@/store/chatStore'
import { useLegionStore } from '../../store/legionStore' // Keep for personality hints

interface MessageInputProps {
  channelId: string
  // currentMinionId is still used for displaying personality hints if a minion is selected
  currentMinionId?: string
}

const MessageInput = ({ channelId, currentMinionId }: MessageInputProps) => {
  const [message, setMessage] = useState('')
  const [priority, setPriority] = useState<'low' | 'normal' | 'high' | 'urgent'>('normal')
  const [showPersonalityHints, setShowPersonalityHints] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { sendMessage: sendChatMessage } = useChatStore()
  const { minions } = useLegionStore() // Get minions for personality hints
  
  const currentMinion = currentMinionId ? minions[currentMinionId] : null
  
  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [message])
  
  const handleSend = async () => {
    if (!message.trim() || !channelId) {
      console.warn('[MessageInput] handleSend: Message empty or channelId missing.', { message: message.trim(), channelId });
      // Optionally, provide user feedback e.g., toast.error("Cannot send empty message or no channel selected.");
      return;
    }
    
    try {
      // Call sendMessage from chatStore with channelId, COMMANDER_ID, and message
      console.log(`[MessageInput] handleSend: Preparing to call sendChatMessage. Channel ID: ${channelId}, Sender ID: ${COMMANDER_ID}, Message: "${message.trim()}"`);
      await sendChatMessage(
        channelId,
        COMMANDER_ID,
        message.trim()
        // Future: Pass priority or other metadata if chatStore.sendMessage supports it
      );
      
      setMessage('');
      setPriority('normal'); // Reset UI priority
    } catch (error) {
      console.error('[MessageInput] Error calling sendChatMessage:', error);
      // Error handling, perhaps a toast notification
    }
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const getPersonalityHint = () => {
    if (!currentMinion) return undefined
    
    // Generate personality hint based on emotional state
    const mood = currentMinion.emotional_state.mood
    const energy = currentMinion.emotional_state.energy_level
    
    if (mood.valence > 0.5 && energy > 0.7) {
      return "Enthusiastic and energetic"
    } else if (mood.valence < -0.5 && energy < 0.3) {
      return "Tired and stressed"
    } else if (mood.curiosity > 0.7) {
      return "Curious and inquisitive"
    }
    
    return undefined
  }
  
  const getPriorityColor = () => {
    switch (priority) {
      case 'urgent': return 'text-red-400 border-red-400'
      case 'high': return 'text-orange-400 border-orange-400'
      case 'low': return 'text-gray-400 border-gray-400'
      default: return 'text-legion-primary border-legion-primary'
    }
  }
  
  return (
    <div className="p-4 border-t border-legion-primary/10">
      {/* Personality Status */}
      {currentMinion && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-3 flex items-center justify-between"
        >
          <div className="flex items-center space-x-3 text-sm">
            <div className="flex items-center space-x-1">
              <Heart className="w-4 h-4 text-pink-400" />
              <span className="text-gray-400">
                Mood: <span className={`font-medium ${
                  currentMinion.emotional_state.mood.valence > 0 ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {currentMinion.emotional_state.mood.valence > 0 ? 'Positive' : 'Neutral'}
                </span>
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-gray-400">
                Energy: <span className="font-medium text-yellow-400">
                  {(currentMinion.emotional_state.energy_level * 100).toFixed(0)}%
                </span>
              </span>
            </div>
          </div>
          
          <button
            onClick={() => setShowPersonalityHints(!showPersonalityHints)}
            className="text-xs text-gray-500 hover:text-gray-400 flex items-center space-x-1"
          >
            <Sparkles className="w-3 h-3" />
            <span>Personality hints</span>
          </button>
        </motion.div>
      )}
      
      {/* Personality Hints */}
      {showPersonalityHints && currentMinion && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mb-3 p-3 bg-black/40 rounded-lg border border-legion-primary/20"
        >
          <p className="text-xs text-gray-400 mb-2">Current personality traits:</p>
          <div className="flex flex-wrap gap-2">
            {currentMinion.persona.quirks.slice(0, 3).map((quirk: string, i: number) => (
              <span key={i} className="text-xs bg-legion-primary/20 text-legion-primary px-2 py-1 rounded">
                {quirk.split(' ').slice(0, 3).join(' ')}...
              </span>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Input Area */}
      <div className="flex items-end space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message as Commander..."
            disabled={!channelId}
            className="w-full bg-black/40 border border-legion-primary/20 rounded-lg px-4 py-3 text-white placeholder-gray-500
                     focus:outline-none focus:border-legion-primary/40 resize-none min-h-[48px] max-h-[120px]
                     disabled:opacity-50 disabled:cursor-not-allowed"
            rows={1}
          />
          
          {/* Character Count */}
          {message.length > 200 && (
            <span className="absolute bottom-2 right-2 text-xs text-gray-500">
              {message.length}/500
            </span>
          )}
        </div>
        
        {/* Priority Selector */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              const priorities: Array<'low' | 'normal' | 'high' | 'urgent'> = ['low', 'normal', 'high', 'urgent']
              const currentIndex = priorities.indexOf(priority)
              setPriority(priorities[(currentIndex + 1) % priorities.length])
            }}
            className={`p-2 border rounded-lg transition-colors ${getPriorityColor()}`}
            title={`Priority: ${priority}`}
          >
            {priority === 'urgent' ? <AlertCircle className="w-5 h-5" /> : <Zap className="w-5 h-5" />}
          </button>
          
          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!message.trim() || !channelId}
            className="p-3 bg-legion-primary hover:bg-legion-primary/80 disabled:bg-gray-700 disabled:cursor-not-allowed
                     text-white rounded-lg transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default MessageInput