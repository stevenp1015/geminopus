import { useState } from 'react'
import { motion } from 'framer-motion'
import { Hash, Lock, Bot, Plus, Search, ChevronDown, ChevronRight } from 'lucide-react'
// import { useLegionStore } from '../../store/legionStore'; // No longer needed for these specific items
import { useChatStore } from '../../store/chatStore'; // Import useChatStore
import { Channel } from '../../types/communication'

const ChannelSidebar = () => {
  // Destructure all channel-related state and actions from useChatStore
  const { channels, selectedChannelId, selectChannel, createChannel } = useChatStore();
  console.log('[ChannelSidebar] Store values - channels:', JSON.parse(JSON.stringify(channels)), 'selectedChannelId:', selectedChannelId);
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set())
  
  // Group channels by type
  // Fallback for channels to prevent error if it's momentarily undefined or null,
  // though chatStore initializes it as {}.
  const currentChannels = channels || {};
  console.log('[ChannelSidebar] currentChannels (after fallback):', JSON.parse(JSON.stringify(currentChannels)));
  
  const allChannelsFromStore = Object.values(currentChannels);
  console.log('[ChannelSidebar] allChannelsFromStore (from Object.values):', JSON.parse(JSON.stringify(allChannelsFromStore)));

  const publicChannels = allChannelsFromStore.filter(c => c.type === 'public')
  const privateChannels = allChannelsFromStore.filter(c => c.type === 'private')
  const directMessages = allChannelsFromStore.filter(c => c.type === 'dm')
  console.log('[ChannelSidebar] Filtered - publicChannels:', JSON.parse(JSON.stringify(publicChannels)));
  console.log('[ChannelSidebar] Filtered - privateChannels:', JSON.parse(JSON.stringify(privateChannels)));
  console.log('[ChannelSidebar] Filtered - directMessages:', JSON.parse(JSON.stringify(directMessages)));
  
  // Filter channels based on search
  const filterChannels = (channelList: Channel[]) => {
    if (!searchQuery) return channelList
    return channelList.filter(c => 
      c.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }
  
  const toggleSection = (section: string) => {
    const newCollapsed = new Set(collapsedSections)
    if (newCollapsed.has(section)) {
      newCollapsed.delete(section)
    } else {
      newCollapsed.add(section)
    }
    setCollapsedSections(newCollapsed)
  }
  
  const ChannelItem = ({ channel }: { channel: Channel }) => {
    console.log('[ChannelItem] Rendering for channel:', JSON.parse(JSON.stringify(channel)), 'ID for key:', channel.id); // Changed to channel.id
    const isSelected = channel.id === selectedChannelId // Changed to channel.id
    const Icon = channel.type === 'public' ? Hash : channel.type === 'private' ? Lock : Bot
    
    return (
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => {
          console.log('[ChannelItem] Clicked. Calling selectChannel with ID:', channel.id); // Changed to channel.id
          selectChannel(channel.id); // Changed to channel.id
        }}
        className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
          isSelected 
            ? 'bg-legion-primary/20 text-white' 
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
      >
        <Icon className="w-4 h-4 flex-shrink-0" />
        <span className="truncate text-left">{channel.name}</span>
        {channel.unread_count && channel.unread_count > 0 && (
          <span className="ml-auto bg-legion-primary text-white text-xs px-2 py-0.5 rounded-full">
            {channel.unread_count}
          </span>
        )}
      </motion.button>
    )
  }
  
  const ChannelSection = ({ 
    title, 
    channels, 
    type 
  }: { 
    title: string
    channels: Channel[]
    type: string 
  }) => {
    const isCollapsed = collapsedSections.has(type)
    const filteredChannels = filterChannels(channels)
    
    if (filteredChannels.length === 0 && searchQuery) return null
    
    console.log(`[ChannelSection: ${title}] Props channels:`, JSON.parse(JSON.stringify(channels)));
    console.log(`[ChannelSection: ${title}] Filtered channels for render (length ${filteredChannels.length}):`, JSON.parse(JSON.stringify(filteredChannels)));

    if (filteredChannels.length === 0 && searchQuery) {
        console.log(`[ChannelSection: ${title}] No filtered channels to render due to search query.`);
        return null;
    }
    if (filteredChannels.length === 0 && !searchQuery) { // Log if section is empty even without search
        console.log(`[ChannelSection: ${title}] No channels in this section (even without search).`);
    }
    
    return (
      <div className="mb-4">
        <button
          onClick={() => toggleSection(type)}
          className="w-full flex items-center justify-between px-3 py-1 text-sm text-gray-500 hover:text-gray-400 transition-colors"
        >
          <span className="font-semibold">{title}</span>
          <div className="flex items-center space-x-1">
            <span className="text-xs">{filteredChannels.length}</span>
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>
        
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-1 space-y-1"
          >
            {filteredChannels.map(channel => {
              console.log(`[ChannelSection: ${title}] Mapping channel for ChannelItem:`, JSON.parse(JSON.stringify(channel)), 'Using key:', channel.id); // Changed to channel.id
              if (channel.id === undefined) { // Changed to channel.id
                console.error(`[ChannelSection: ${title}] FATAL: Rendering ChannelItem with undefined id!`, channel);
              }
              return (
                <ChannelItem key={channel.id} channel={channel} /> // Changed to channel.id
              );
            })}
          </motion.div>
        )}
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-legion-primary/10">
        <h2 className="text-lg font-bold text-white mb-3">Channels</h2>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search channels..."
            className="w-full bg-black/40 border border-legion-primary/20 rounded-lg pl-10 pr-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-legion-primary/40"
          />
        </div>
      </div>
      
      {/* Channel List */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-legion-primary/20 scrollbar-track-transparent">
        <ChannelSection title="Public Channels" channels={publicChannels} type="public" />
        <ChannelSection title="Private Channels" channels={privateChannels} type="private" />
        <ChannelSection title="Direct Messages" channels={directMessages} type="dm" />
        
        {/* No channels message */}
        {publicChannels.length === 0 && privateChannels.length === 0 && directMessages.length === 0 && (
          <div className="text-center py-8">
            <Hash className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">No channels yet</p>
          </div>
        )}
      </div>
      
      {/* Create Channel Button */}
      <div className="p-4 border-t border-legion-primary/10">
        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full flex items-center justify-center space-x-2 py-2 bg-legion-primary/20 hover:bg-legion-primary/30 text-legion-primary border border-legion-primary/40 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create Channel</span>
        </button>
      </div>
      
      {/* TODO: Add Create Channel Modal */}
    </div>
  )
}

export default ChannelSidebar