# Gemini Legion: Granular TODO List

This document provides a detailed task breakdown for completing the Gemini Legion project. 
Created to help track progress through frequent disconnections.

## 🔥 IMMEDIATE PRIORITIES (Backend - Final 15%)

### 1. Wire Up API Endpoints to Services ⚡ ✅
- [x] Update `minions.py` endpoint to use MinionService via dependency injection
  - [x] `/spawn` - Use `minion_service.spawn_minion()`
  - [x] `/list` - Use `minion_service.list_minions()`
  - [x] `/{minion_id}` - Use `minion_service.get_minion()`
  - [x] `/{minion_id}/emotional-state` - Use `minion_service.get_emotional_state()`
  - [x] `/{minion_id}/send-message` - Use `minion_service.send_message()`
- [x] Update `channels.py` endpoint to use ChannelService
  - [x] `/create` - Use `channel_service.create_channel()`
  - [x] `/list` - Use `channel_service.list_channels()`
  - [x] `/{channel_id}/messages` - Use `channel_service.get_channel_messages()`
  - [x] `/{channel_id}/send` - Use `channel_service.send_message()`
- [x] Update `tasks.py` endpoint (create if doesn't exist)
  - [x] `/create` - Use `task_service.create_task()`
  - [x] `/list` - Use `task_service.list_tasks()`
  - [x] `/{task_id}` - Use `task_service.get_task()`
  - [x] `/{task_id}/assign` - Use `task_service.assign_task()`

### 2. WebSocket Event Broadcasting 📡 ✅
- [x] Update WebSocketManager to broadcast service events
  - [x] Minion spawned/despawned events
  - [x] Emotional state changes
  - [x] New messages in channels
  - [x] Task status updates
- [x] Create event serializers for WebSocket messages
- [x] Add event listeners in services to trigger broadcasts

### 3. Main Application Startup 🚀 ✅
- [x] Update `main.py` to initialize services on startup
- [x] Add graceful shutdown handling
- [x] Configure CORS properly for frontend
- [x] Add middleware for logging and error handling

## 🎨 FRONTEND PRIORITIES (Final 30%)

### 1. Complete Store Integration with APIs 🔗
- [ ] Update `legionStore.ts` to use API services
  - [ ] `spawnMinion()` -> Call API endpoint
  - [ ] `updateEmotionalState()` -> Call API endpoint
  - [ ] `sendMessage()` -> Call API endpoint
- [ ] Update `chatStore.ts` to use API
  - [ ] `loadMessages()` -> Fetch from API
  - [ ] `sendMessage()` -> Post to API
  - [ ] `createChannel()` -> Call API
- [ ] Update `taskStore.ts` to use API
  - [ ] `createTask()` -> Call API
  - [ ] `assignTask()` -> Call API
  - [ ] `updateTaskStatus()` -> Call API

### 2. WebSocket Event Handling 🌐
- [ ] Update `useWebSocket.ts` to handle all event types
  - [ ] Parse and dispatch minion events
  - [ ] Parse and dispatch message events
  - [ ] Parse and dispatch task events
- [ ] Connect WebSocket events to store updates
  - [ ] Auto-update minion states
  - [ ] Real-time message updates
  - [ ] Live task status changes

### 3. Complete Missing UI Features 🎯
- [ ] Add error handling and loading states to all components
- [ ] Implement notification system for important events
- [ ] Add confirmation dialogs for destructive actions
- [ ] Create empty states for components
- [ ] Add search/filter functionality to lists

### 4. Polish and UX 💫
- [ ] Add animations and transitions
- [ ] Implement keyboard shortcuts
- [ ] Add tooltips for complex features
- [ ] Create onboarding flow for new users
- [ ] Add dark/light theme toggle

## 🔒 PRODUCTION FEATURES (Optional for MVP)

### 1. Authentication & Authorization
- [ ] Add JWT authentication to backend
- [ ] Implement login/logout flow in frontend
- [ ] Add role-based access control
- [ ] Secure WebSocket connections

### 2. Persistent Storage
- [ ] Implement MongoDB repositories
- [ ] Add database migrations
- [ ] Configure connection pooling
- [ ] Add data validation

### 3. Monitoring & Observability
- [ ] Add structured logging
- [ ] Implement metrics collection
- [ ] Create health check endpoints
- [ ] Add error tracking (Sentry)

### 4. Deployment
- [ ] Create Docker containers
- [ ] Write docker-compose.yml
- [ ] Add environment configuration
- [ ] Create deployment scripts

## 📝 CURRENT STATUS NOTES

**What's Working:**
- All core domain models (emotional, memory, communication)
- Complete ADK integration with tools
- All application services implemented
- In-memory repositories ready
- All frontend components built
- API client layer created
- **✅ API endpoints wired to services**
- **✅ WebSocket broadcasting implemented**
- **✅ Main application properly initialized**

**What's Missing (Critical):**
1. Frontend stores not calling APIs
2. WebSocket events not updating UI
3. Event emission from services (for real-time updates)

**Estimated Time to MVP:**
- Backend completion: ✅ DONE!
- Frontend integration: 3-4 hours
- Testing & debugging: 2 hours
- **Total: ~5-6 hours of focused work**

## 🎯 NEXT IMMEDIATE ACTION

**Start with:** Updating the frontend stores to use the API services. This will make the frontend talk to the fully functional backend!

---
*Last Updated: 2025-05-30 07:30:00 UTC by Claude Opus 4*
*For Steven, with exhaustive love and dedication* 💜