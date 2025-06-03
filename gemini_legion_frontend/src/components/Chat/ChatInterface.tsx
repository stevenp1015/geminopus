import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Hash, Users, Lock, Bot, ChevronLeft } from 'lucide-react'
import { useLegionStore } from '../../store/legionStore'
import { useChatStore } from '../../store/chatStore' // Added chatStore import
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import ChannelSidebar from './ChannelSidebar'
import ParticipantsList from './ParticipantsList'
import { Channel, Message } from '../../types/communication'

const ChatInterface = () => {
  const { minions, selectedMinionId: legionSelectedMinionId } = useLegionStore() // Get selectedMinionId
  const {
    channels,
    messages: chatStoreMessages,
    selectedChannelId
  } = useChatStore()
  const [showSidebar, setShowSidebar] = useState(true)
  const [showParticipants, setShowParticipants] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const selectedChannel = selectedChannelId ? channels[selectedChannelId] : null
  const channelMessages = selectedChannelId && chatStoreMessages[selectedChannelId]
    ? chatStoreMessages[selectedChannelId]
    : []
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [channelMessages])
  
  // Get channel participants
  const participants = selectedChannel?.participants || []
  const participantMinions = participants
    .map(id => minions[id])
    .filter(Boolean)
  
  // Get channel icon
  const getChannelIcon = () => {
    if (!selectedChannel) return null
    switch (selectedChannel.type) {
      case 'public':
        return <Hash className="w-5 h-5" />
      case 'private':
        return <Lock className="w-5 h-5" />
      case 'dm':
        return <Bot className="w-5 h-5" />
      default:
        return <Hash className="w-5 h-5" />
    }
  }
  
  return (
    <div className="flex h-full bg-black/20 rounded-xl border border-legion-primary/20 overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {showSidebar && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="w-64 bg-black/40 backdrop-blur-sm border-r border-legion-primary/10"
          >
            <ChannelSidebar />
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-16 bg-black/60 backdrop-blur-sm border-b border-legion-primary/10 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            {!showSidebar && (
              <button
                onClick={() => setShowSidebar(true)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-400" />
              </button>
            )}
            
            {selectedChannel ? (
              <>
                <div className="flex items-center space-x-2 text-white">
                  {getChannelIcon()}
                  <span className="font-semibold">{selectedChannel.name}</span>
                </div>
                {selectedChannel.description && (
                  <span className="text-gray-400 text-sm">
                    {selectedChannel.description}
                  </span>
                )}
              </>
            ) : (
              <span className="text-gray-500">Select a channel to start chatting</span>
            )}
          </div>
          
          {selectedChannel && (
            <button
              onClick={() => setShowParticipants(!showParticipants)}
              className="flex items-center space-x-2 px-3 py-1.5 hover:bg-white/10 rounded-lg transition-colors"
            >
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-400 text-sm">{participants.length}</span>
            </button>
          )}
        </div>
        
        {/* Messages Area */}
        <div className="flex-1 flex">
          <div className="flex-1 flex flex-col">
            {selectedChannel ? (
              <>
                <MessageList
                  messages={channelMessages}
                  minions={minions}
                  currentUserId={legionSelectedMinionId === null ? undefined : legionSelectedMinionId}
                />
                <div ref={messagesEndRef} />
                <MessageInput
                  channelId={selectedChannel.id} // Changed from channel_id to id
                  currentMinionId={legionSelectedMinionId === null ? undefined : legionSelectedMinionId}
                />
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <Hash className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">No channel selected</p>
                  <p className="text-gray-600 text-sm mt-2">
                    Choose a channel from the sidebar to start chatting
                  </p>
                </div>
              </div>
            )}
          </div>
          
          {/* Participants Sidebar */}
          <AnimatePresence mode="wait">
            {showParticipants && selectedChannel && (
              <motion.div
                initial={{ x: 300 }}
                animate={{ x: 0 }}
                exit={{ x: 300 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="w-64 bg-black/40 backdrop-blur-sm border-l border-legion-primary/10"
              >
                <ParticipantsList 
                  participants={participantMinions}
                  channelName={selectedChannel.name}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface