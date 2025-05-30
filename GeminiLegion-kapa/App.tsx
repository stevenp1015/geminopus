
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MinionConfig, ChatMessageData, MessageSender, Channel, ModelOption } from './types';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import MinionsPanel from './components/ConfigPanel'; // Renamed to MinionsPanel
// Fix: Added CpuChipIcon import
import { CogIcon, HashtagIcon as ChannelIcon, CpuChipIcon } from './components/Icons'; // Using Hashtag for channels
import {
  APP_TITLE, LEGION_COMMANDER_NAME, MINION_CONFIGS_STORAGE_KEY, 
  CHAT_HISTORY_STORAGE_KEY, ACTIVE_CHANNEL_STORAGE_KEY,
  EMOTIONAL_ENGINE_SYSTEM_PROMPT_TEMPLATE, 
  META_PROMPT_TASK_INSTRUCTIONS_TEMPLATE,
  formatChatHistoryForLLM,
  UI_API_KEY 
} from './constants';
import { extractDiaryAndContent } from './services/geminiService'; // Still useful for diary
// Fix: Corrected import for legionApiService (default import)
import legionApiService from './services/legionApiService'; // New API service

// Placeholder for ChannelList component
const ChannelList: React.FC<{ 
  channels: Channel[]; 
  currentChannelId: string | null; 
  onSelectChannel: (channelId: string) => void;
  onAddChannel: (name: string) => void; // Basic add channel functionality
}> = ({ channels, currentChannelId, onSelectChannel, onAddChannel }) => {
  const [newChannelName, setNewChannelName] = useState('');

  const handleAdd = () => {
    if (newChannelName.trim()) {
      onAddChannel(newChannelName.trim());
      setNewChannelName('');
    }
  };

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex-shrink-0 flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-gray-100">Channels</h2>
      </div>
      <div className="flex-grow p-2 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-700">
        {channels.map(channel => (
          <button
            key={channel.id}
            onClick={() => onSelectChannel(channel.id)}
            className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-md transition-colors ${
              currentChannelId === channel.id 
                ? 'bg-sky-600 text-white font-medium' 
                : 'text-gray-300 hover:bg-gray-700 hover:text-gray-100'
            }`}
          >
            <ChannelIcon className="w-5 h-5 flex-shrink-0" />
            <span className="truncate">{channel.name}</span>
          </button>
        ))}
      </div>
      <div className="p-2 border-t border-gray-700">
        <input 
          type="text"
          value={newChannelName}
          onChange={(e) => setNewChannelName(e.target.value)}
          placeholder="New channel name..."
          className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded-md text-sm text-gray-200 placeholder-gray-500 mb-1"
        />
        <button 
          onClick={handleAdd}
          className="w-full px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-md"
        >
          Add Channel
        </button>
      </div>
    </div>
  );
};


const App: React.FC = () => {
  const [minionConfigs, setMinionConfigs] = useState<MinionConfig[]>([]);
  const [messages, setMessages] = useState<Record<string, ChatMessageData[]>>({}); // channelId -> messages
  const [channels, setChannels] = useState<Channel[]>([]);
  const [currentChannelId, setCurrentChannelId] = useState<string | null>(null);
  
  const [isMinionsPanelOpen, setIsMinionsPanelOpen] = useState(true);
  const [isProcessingMessage, setIsProcessingMessage] = useState(false);
  // Tracks which Minions are "typing" or processing a response for the current message interaction
  const [activeMinionProcessors, setActiveMinionProcessors] = useState<Record<string, boolean>>({}); 

  const chatHistoryRef = useRef<HTMLDivElement>(null);
  const service = useRef(legionApiService).current; // Use the singleton instance


  // Initial data loading (Minions, Channels, Messages for active channel)
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const fetchedMinions = await service.getMinions();
        setMinionConfigs(fetchedMinions);

        const fetchedChannels = await service.getChannels();
        setChannels(fetchedChannels);

        let activeChannelId = localStorage.getItem(ACTIVE_CHANNEL_STORAGE_KEY);
        if (!activeChannelId && fetchedChannels.length > 0) {
          activeChannelId = fetchedChannels[0].id;
        }
        
        if (activeChannelId) {
          setCurrentChannelId(activeChannelId);
          const channelMessages = await service.getMessages(activeChannelId);
          setMessages(prev => ({ ...prev, [activeChannelId!]: channelMessages }));
        } else if (fetchedChannels.length === 0) {
          // Create a default #general channel if none exist
          const generalChannel = await service.addChannel({ name: 'general', type: 'user_minion_group', id: 'general', members: [LEGION_COMMANDER_NAME]});
          setChannels([generalChannel]);
          setCurrentChannelId(generalChannel.id);
          setMessages(prev => ({...prev, [generalChannel.id]: []}));
        }
      } catch (error) {
        console.error("Failed to load initial data:", error);
        // Add a system error message to a default/error channel?
      }
    };
    loadInitialData();
  }, [service]);

  // Save Minion configs to storage (via service which mocks localStorage)
  useEffect(() => {
    // This effect implicitly relies on service.addMinion etc. updating its internal store
    // In a real app, this might not be needed if all writes go through service and it handles persistence.
  }, [minionConfigs]);

  // Save messages to storage (via service) & scroll
  useEffect(() => {
    // Same as above, persistence is handled by the service.
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [messages]);

  // Save active channel
  useEffect(() => {
    if (currentChannelId) {
      localStorage.setItem(ACTIVE_CHANNEL_STORAGE_KEY, currentChannelId);
    }
  }, [currentChannelId]);

  const addMinionConfig = async (config: MinionConfig) => {
    try {
      const newMinion = await service.addMinion(config);
      setMinionConfigs(prev => [...prev, newMinion]);
      // Initialize opinion scores in backend/mock
    } catch (error) {
      console.error("Failed to add Minion:", error);
    }
  };

  const updateMinionConfig = async (updatedConfig: MinionConfig) => {
     try {
      const changedMinion = await service.updateMinion(updatedConfig);
      setMinionConfigs(prev => prev.map(m => m.id === changedMinion.id ? changedMinion : m));
    } catch (error) {
      console.error("Failed to update Minion:", error);
    }
  };

  const deleteMinionConfig = async (id: string) => {
    try {
      await service.deleteMinion(id);
      setMinionConfigs(prev => prev.filter(m => m.id !== id));
    } catch (error) {
      console.error("Failed to delete Minion:", error);
    }
  };

  const addMessageToChannel = useCallback((channelId: string, message: ChatMessageData) => {
    setMessages(prev => ({
      ...prev,
      [channelId]: [...(prev[channelId] || []), message]
    }));
  }, []);
  
  const updateMessageInChannel = useCallback((channelId: string, messageId: string, updates: Partial<ChatMessageData>) => {
    setMessages(prev => ({
      ...prev,
      [channelId]: (prev[channelId] || []).map(m => m.id === messageId ? { ...m, ...updates } : m)
    }));
  }, []);


  const deleteMessageFromChannel = async (channelId: string, messageId: string) => {
     try {
      await service.deleteMessage(channelId, messageId);
      setMessages(prev => ({
        ...prev,
        [channelId]: (prev[channelId] || []).filter(m => m.id !== messageId)
      }));
    } catch (error) {
      console.error("Failed to delete message:", error);
    }
  };

  const editMessageContent = async (channelId: string, messageId: string, newContent: string) => {
    try {
      await service.editMessage(channelId, messageId, newContent);
      updateMessageInChannel(channelId, messageId, { content: newContent });
    } catch (error) {
      console.error("Failed to edit message:", error);
    }
  };
  
  const selectChannel = async (channelId: string) => {
    if (!messages[channelId]) { // Lazy load messages for channel
        try {
            const channelMessages = await service.getMessages(channelId);
            setMessages(prev => ({...prev, [channelId]: channelMessages}));
        } catch (error) {
            console.error(`Failed to load messages for channel ${channelId}:`, error);
            addMessageToChannel(channelId, {
                id: `sys-err-${Date.now()}`, channelId, senderType: MessageSender.System, senderName: 'System',
                content: `Error loading messages for this channel.`, timestamp: Date.now(), isError: true,
            });
        }
    }
    setCurrentChannelId(channelId);
  };

  const handleAddNewChannel = async (name: string) => {
    try {
      const newChannel = await service.addChannel({ 
        id: `chan-${Date.now()}`, // ID generation would be backend's job
        name, 
        type: 'user_minion_group', // Default type
        members: [LEGION_COMMANDER_NAME] 
      });
      setChannels(prev => [...prev, newChannel]);
      if (!currentChannelId) {
        setCurrentChannelId(newChannel.id);
      }
      if (!messages[newChannel.id]) {
        setMessages(prev => ({...prev, [newChannel.id]: []}));
      }
    } catch (error) {
      console.error("Failed to add channel:", error);
    }
  };

  const handleSendMessage = async (userInput: string) => {
    if (!currentChannelId) {
      console.error("No active channel selected."); // TODO: Show UI error
      addMessageToChannel(channels[0]?.id || 'general', { // Try to add to first channel or a default
         id: `err-nochannel-${Date.now()}`, channelId: channels[0]?.id || 'general', senderType: MessageSender.System, senderName: 'System',
         content: 'Error: No channel selected to send message.', timestamp: Date.now(), isError: true,
      });
      return;
    }
    if (minionConfigs.length === 0 && !currentChannelId.startsWith('system_')) { // Don't block system channels
      addMessageToChannel(currentChannelId, {
        id: `sys-nominion-${Date.now()}`, channelId: currentChannelId, senderType: MessageSender.System, senderName: 'System',
        content: 'No Minions deployed. Please deploy a Minion to interact.', timestamp: Date.now(),
      });
      return;
    }

    const userMessage: ChatMessageData = {
      id: `user-${Date.now()}`, channelId: currentChannelId, senderType: MessageSender.User,
      senderName: LEGION_COMMANDER_NAME, content: userInput, timestamp: Date.now(),
    };
    addMessageToChannel(currentChannelId, userMessage);
    setIsProcessingMessage(true);

    // Simulate backend processing and Minion responses via legionApiService
    // The service will handle how Minions respond (e.g., using geminiService for mock)
    try {
      await service.handleUserMessage({
        channelId: currentChannelId,
        message: userMessage,
        allMinions: minionConfigs, // Pass available Minions for the service to decide who responds
        currentMessages: messages[currentChannelId] || [], // Pass current channel messages for context
        onMinionResponseChunk: (minionId, tempMessageId, chunk, isFinal) => {
          if (!isFinal) {
            updateMessageInChannel(currentChannelId, tempMessageId, { content: (messages[currentChannelId]?.find(m=>m.id === tempMessageId)?.content || "") + chunk });
          } else {
            // Final processing already handled by the legionApiService mock potentially
            // It would call onMinionResponse to add/finalize the message
          }
        },
        onMinionResponse: (responseMessage) => { // Full message from Minion
          // Check if temp message exists and update, otherwise add new
          const existingMsg = (messages[currentChannelId] || []).find(m => m.id === responseMessage.id && m.content === "");
          if(existingMsg) {
            updateMessageInChannel(currentChannelId, responseMessage.id, responseMessage);
          } else {
            addMessageToChannel(currentChannelId, responseMessage);
          }
        },
        onMinionProcessingUpdate: (minionId, isProcessing) => {
          setActiveMinionProcessors(prev => ({ ...prev, [minionId]: isProcessing }));
        },
        onSystemMessage: (systemMessage) => { // For [SILENT] notifications etc.
            addMessageToChannel(currentChannelId, systemMessage);
        }
      });
    } catch (error: any) {
      console.error("Error processing user message via service:", error);
      addMessageToChannel(currentChannelId, {
        id: `err-proc-${Date.now()}`, channelId: currentChannelId, senderType: MessageSender.System, senderName: 'System',
        content: `Error sending message: ${error.message || 'Unknown service error'}`, timestamp: Date.now(), isError: true,
      });
    } finally {
      setIsProcessingMessage(false);
      setActiveMinionProcessors({}); // Clear all after full exchange
    }
  };
  
  const currentChannelMessages = messages[currentChannelId || ''] || [];

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-200 selection:bg-sky-500 selection:text-white">
      <header className="p-4 bg-gray-800 border-b border-gray-700 shadow-md flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <img src="https://picsum.photos/seed/legionicon/40/40" alt="Legion Icon" className="w-10 h-10 rounded-full ring-2 ring-sky-500" />
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">{APP_TITLE}</h1>
            <p className="text-xs text-sky-400">Legion Commander: {LEGION_COMMANDER_NAME}</p>
          </div>
        </div>
        <button
          onClick={() => setIsMinionsPanelOpen(!isMinionsPanelOpen)}
          className="p-2 rounded-md text-gray-400 hover:text-sky-400 hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500"
          title="Toggle Minions Roster"
        >
          <CogIcon className="w-6 h-6" />
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <ChannelList 
            channels={channels} 
            currentChannelId={currentChannelId}
            onSelectChannel={selectChannel}
            onAddChannel={handleAddNewChannel}
        />
        <MinionsPanel
          minionConfigs={minionConfigs}
          onAddMinion={addMinionConfig}
          onUpdateMinion={updateMinionConfig}
          onDeleteMinion={deleteMinionConfig}
          isOpen={isMinionsPanelOpen}
          onToggle={() => setIsMinionsPanelOpen(!isMinionsPanelOpen)}
        />

        <main className="flex-1 flex flex-col overflow-hidden">
          {currentChannelId ? (
            <>
              <div className="p-2 border-b border-gray-700 bg-gray-800/50">
                <h3 className="text-lg font-semibold text-gray-200">
                    {channels.find(c => c.id === currentChannelId)?.name || "Selected Channel"}
                </h3>
                <p className="text-xs text-gray-400">
                    {channels.find(c => c.id === currentChannelId)?.description || "Messages for this channel."}
                </p>
              </div>
              <div ref={chatHistoryRef} className="flex-1 p-4 space-y-2 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800/50">
                {currentChannelMessages.length === 0 && (
                  <div className="text-center text-gray-500 pt-10">
                    <img src="https://picsum.photos/seed/channel_empty/100/100" alt="Empty Channel" className="mx-auto mb-4 rounded-lg opacity-50" />
                    <p>No messages in <span className="font-semibold">{channels.find(c => c.id === currentChannelId)?.name || "this channel"}</span> yet.</p>
                    <p>Send a message to start the conversation!</p>
                  </div>
                )}
                {currentChannelMessages.map(msg => (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    onDelete={deleteMessageFromChannel}
                    onEdit={editMessageContent}
                    isProcessing={activeMinionProcessors[msg.senderName] && msg.content === ""} // Simplified processing indicator
                  />
                ))}
                 {/* Display "Minion is thinking..." indicators for current interaction */}
                {Object.entries(activeMinionProcessors).map(([minionId, isTyping]) => {
                  if (isTyping) {
                    const minion = minionConfigs.find(c => c.id === minionId || c.name === minionId); // Try matching by ID or name
                    // Check if there's already a streaming message for this Minion in this channel
                    const existingStreamingMsg = currentChannelMessages.find(m => m.senderType === MessageSender.AI && m.senderName === minion?.name && m.content === "" && !m.isError);
                    if (minion && !existingStreamingMsg) {
                      return (
                        <div key={`typing-${minion.id}`} className="flex items-center gap-2 px-4 py-1 text-xs text-gray-400 italic">
                          {/* Fix: CpuChipIcon is now correctly imported */}
                          <CpuChipIcon className="w-4 h-4 text-emerald-400 animate-pulse" />
                          <span>{minion.name} is processing...</span>
                        </div>
                      );
                    }
                  }
                  return null;
                })}
              </div>
              <ChatInput onSendMessage={handleSendMessage} isSending={isProcessingMessage} />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                    <img src="https://picsum.photos/seed/legion_idle/128/128" alt="Legion Idle" className="mx-auto mb-4 rounded-lg opacity-60" />
                    <p className="text-lg">Select a channel to begin.</p>
                    <p>Or, deploy Minions and create channels from the respective panels.</p>
                </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
