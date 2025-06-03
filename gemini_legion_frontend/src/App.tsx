import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import LegionDashboard from './components/Legion/LegionDashboard'
import ChatInterface from './components/Chat/ChatInterface'
import { useWebSocket } from './hooks/useWebSocket'
import { useLegionStore } from './store/legionStore'
import { useChatStore } from './store/chatStore' // Added import for chatStore
import './App.css'

function App() {
  const [activeView, setActiveView] = useState<'dashboard' | 'chat'>('dashboard')
  const { isConnected } = useWebSocket()
  const { fetchMinions } = useLegionStore() // Removed fetchChannels from legionStore
  const { fetchChannels: fetchChatChannels } = useChatStore() // Get fetchChannels from chatStore

  useEffect(() => {
    // Initial data fetch
    fetchMinions()
    fetchChatChannels() // Call fetchChannels from chatStore
  }, [fetchMinions, fetchChatChannels])

  return (
    <div className="min-h-screen bg-gradient-to-br from-legion-darker via-legion-dark to-purple-950">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e1b4b',
            color: '#fff',
            border: '1px solid #6366f1',
          },
        }}
      />
      
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-legion-primary/20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-legion-primary to-legion-accent bg-clip-text text-transparent">
                Gemini Legion
              </h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-sm text-gray-400">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveView('dashboard')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  activeView === 'dashboard'
                    ? 'bg-legion-primary text-white'
                    : 'text-gray-300 hover:text-white hover:bg-white/10'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveView('chat')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  activeView === 'chat'
                    ? 'bg-legion-primary text-white'
                    : 'text-gray-300 hover:text-white hover:bg-white/10'
                }`}
              >
                Chat
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeView === 'dashboard' ? <LegionDashboard /> : <ChatInterface />}
      </main>
    </div>
  )
}

export default App