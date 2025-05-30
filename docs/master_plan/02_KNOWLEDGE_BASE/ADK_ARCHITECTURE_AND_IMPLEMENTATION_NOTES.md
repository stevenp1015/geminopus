# ADK Backend Architecture and Implementation Notes

## 1. Introduction

This document outlines the proposed core backend architecture for the Minion Army, leveraging the Google Agent Development Kit (ADK). It details the high-level system design, the mapping of Minion roles to ADK agent types, strategies for inter-Minion communication, and the plan for session management. This architecture aims to fulfill the vision of a robust, scalable, and intelligent multi-agent system as laid out in "Operation Gemini Legion - Phase Zero."

## 2. Proposed ADK Backend Architecture

The envisioned backend architecture is designed to be modular and scalable, supporting complex interactions between the Legion Commander GUI, various backend services, and the Minion agents themselves.

### 2.1. High-Level Components

The primary components of the ADK backend include:

*   **API Handlers (e.g., FastAPI/Flask):** These serve as the entry point for all requests from the Legion Commander GUI, as defined in the [`01_API_CONTRACT_V1.md`](../01_API_CONTRACT_V1.md:0). They will be responsible for request validation, authentication, and routing to appropriate services or ADK Runners. For real-time communication (AeroChat, live updates), WebSocket handlers will manage persistent connections.
*   **ADK Runners (`google.adk.runners.Runner`):** Each active Minion agent instance will be managed by an ADK Runner. The Runner facilitates the execution of the agent's lifecycle methods (e.g., `awake`, `think`, `predict`) and integrates with session and artifact services.
*   **Session Service (`google.adk.sessions.BaseSessionService`):** Responsible for managing the conversational and operational context for agent interactions. Initially, `InMemorySessionService` will be used (as seen in [`adk_minion_army/main_adk.py`](../../../adk_minion_army/main_adk.py:0)), evolving as per persistence needs.
*   **Artifact Service (`google.adk.artifacts.BaseArtifactService`):** Used by agents to store and retrieve data, such as task outputs, intermediate results, or potentially Minion "diaries" (as per AeroChat strategy). `InMemoryArtifactService` will be the V1 choice.
*   **Minion Agents (Custom ADK Agents):** Instances of `LlmAgent`, `WorkflowAgent` (or its conceptual equivalent), and potentially `CustomAgent` that embody the defined Minion roles (e.g., TaskMaster Prime, LoreKeeper Scribe). These are the core intelligence units of the system.
*   **Configuration Management:** A system (initially evolving from [`adk_minion_army/config_loader.py`](../../../adk_minion_army/config_loader.py:0)) to load and manage Minion personas, model configurations, and tool access, updated via API calls.
*   **Channel Context Service (for AeroChat):** As detailed in [`AEROCHAT_INTEGRATION_STRATEGY.md`](./AEROCHAT_INTEGRATION_STRATEGY.md:0), this service (or a dedicated agent like an enhanced CommsRelay Connect) will manage chat channel metadata, participant lists, and message history, providing necessary context to Minions for chat interactions.
*   **Diary Storage (for AeroChat):** A mechanism (SQLite database or leveraging `ArtifactService`) for persisting Minion "personal diaries" to enable emotional state tracking and nuanced conversational behavior.

### 2.2. Component Interactions Diagram

```mermaid
graph TD
    User[Legion Commander GUI] -- REST/WebSocket API Calls --> APIHandlers[API Handlers (FastAPI/Flask + WebSocket)]

    subgraph ADK Backend
        APIHandlers -- Invoke / Route --> ADKRunners[ADK Runners]
        ADKRunners -- Manages --> MinionAgents[Minion Agents (LlmAgent, WorkflowAgent, etc.)]
        MinionAgents -- Uses --> SessionService[Session Service (InMemorySessionService V1)]
        MinionAgents -- Uses --> ArtifactService[Artifact Service (InMemoryArtifactService V1)]
        MinionAgents -- Interacts with (for AeroChat) --> DiaryStorage[Diary Storage (SQLite/ArtifactService)]
        MinionAgents -- Interacts with (for AeroChat) --> CCS[Channel Context Service]

        APIHandlers -- Manages Minion Configs --> ConfigMgmt[Configuration Management]
        ConfigMgmt -- Provides Config to --> MinionAgents

        APIHandlers -- Manages Chat Channels --> CCS
        CCS -- Provides Context to --> MinionAgents
    end

    MinionAgents -- Inter-Minion Comms --> MinionAgents
```

### 2.3. Interaction Flow Example (Task Assignment)

1.  **GUI Request:** Legion Commander GUI sends a "Send New Directive/Task" request (e.g., `POST /api/v1/tasks`) to an API Handler.
2.  **API Handling:** The API Handler validates the request, authenticates, and identifies the target Minion(s) or TaskMaster Prime.
3.  **Runner Invocation:** The API Handler (or a task orchestration service) retrieves/instantiates the appropriate ADK Runner for the target Minion (e.g., TaskMaster Prime).
4.  **Session Creation:** A session is created or retrieved using the `SessionService` for this interaction (e.g., tied to the `task_id`).
5.  **Agent Execution:** The Runner invokes the Minion agent's `think()` or `predict()` method with the new task/directive.
6.  **Minion Processing:** The Minion agent processes the task.
    *   If it's TaskMaster Prime, it might decompose the task and prepare to delegate sub-tasks. This could involve invoking other Minions (via their Runners) or posting tasks to a shared queue/channel.
    *   It might use `ArtifactService` to store intermediate data or final results.
    *   It updates its "diary" via the Diary Storage.
7.  **Response:** The Minion agent returns a response through the Runner.
8.  **API Response:** The API Handler formats this response and sends it back to the GUI (e.g., a 202 Accepted with a `task_id`).
9.  **Real-time Updates:** Subsequent progress, logs, or chat messages related to the task are pushed to the GUI via WebSockets.

## 3. ADK Agent Types for Minion Roles

The choice of ADK agent type is fundamental to a Minion's capabilities. Referencing [`MINION_DEFINITIONS_AND_ROLES.md`](./MINION_DEFINITIONS_AND_ROLES.md:0):

*   **2.1. TaskMaster Prime:**
    *   **Proposed ADK Agent Type(s):** Primarily a `WorkflowAgent` (e.g., `SequentialAgent`, `ParallelAgent` if available and mature in ADK). This aligns with its role in dissecting tasks and managing multi-step execution flows involving other Minions.
    *   **Justification:** `WorkflowAgent` is designed for orchestrating sub-agents or a series of steps. TaskMaster Prime's responsibilities of decomposition, assignment, monitoring, and aggregation fit this paradigm perfectly. If a suitable `WorkflowAgent` is not directly usable in V1, a highly sophisticated `LlmAgent` with custom logic to simulate workflow orchestration will be implemented, with a plan to refactor to a `WorkflowAgent` when feasible. The agent would need to manage state about sub-tasks and their assigned Minions.
    *   **Initial ADK Implementation (if no `WorkflowAgent`):** An `LlmAgent` whose prompt and tools enable it to:
        1.  Call a "Decomposition Tool" (which might internally be another `LlmAgent` call).
        2.  Maintain a list of sub-tasks and their status.
        3.  Formulate messages to assign tasks to other Minions (via CommsRelay Connect).
        4.  Request updates and aggregate results.

*   **2.2. LoreKeeper Scribe:**
    *   **Proposed ADK Agent Type(s):** `LlmAgent`.
    *   **Justification:** This role requires advanced natural language understanding for collecting, curating, summarizing, and retrieving information. RAG (Retrieval Augmented Generation) will be key. The `LlmAgent` can be equipped with tools to interface with data sources (databases via API, document stores via `ArtifactService`, web search APIs) and to manage a knowledge base (potentially stored in `ArtifactService` or a vector database). Its summarization and query-answering capabilities are central.

*   **2.3. AlphaIntel Scout:**
    *   **Proposed ADK Agent Type(s):** `LlmAgent`.
    *   **Justification:** As a specialized research unit, the AlphaIntel Scout needs strong reasoning to execute targeted research and use various data gathering tools (web browsing, API calls). An `LlmAgent` provides the flexibility to interpret research directives and leverage a suite of configured tools effectively.

*   **2.4. CommsRelay Connect:**
    *   **Proposed ADK Agent Type(s):** `LlmAgent` (potentially a highly specialized one, or a `CustomAgent` wrapping LLM capabilities if specific non-LLM logic for routing becomes dominant).
    *   **Justification:** While simple message relay could be rule-based, the AeroChat integration, with its emphasis on "personal diaries," nuanced turn-taking, and potentially intent recognition for routing or notifications, strongly suggests an `LlmAgent`. This agent would manage interactions with the Channel Context Service and implement the AeroChat logic outlined in [`AEROCHAT_INTEGRATION_STRATEGY.md`](./AEROCHAT_INTEGRATION_STRATEGY.md:0).

## 4. Inter-Minion Communication Strategy (ADK-centric)

Effective collaboration requires robust inter-Minion communication. This will be multifaceted, leveraging both ADK's capabilities and the specific needs of the Minion Army.

*   **AeroChat Layer (via CommsRelay Connect):**
    *   This is the primary mechanism for "human-like" or "agent-like" conversational exchanges between Minions, or between Minions and the Commander, as detailed in [`AEROCHAT_INTEGRATION_STRATEGY.md`](./AEROCHAT_INTEGRATION_STRATEGY.md:0).
    *   CommsRelay Connect will manage these chat channels, using the Channel Context Service and Diary Storage to facilitate rich, stateful conversations. Minions participating in these chats will use their AeroChat-enhanced `LlmAgent` capabilities (diary updates, probabilistic responses, etc.).
    *   This is suitable for status updates, general coordination, requests for information, and collaborative problem-solving that benefits from natural language.

*   **Structured Task Handoffs & Data Exchange (ADK Mechanisms):**
    *   **`WorkflowAgent` Orchestration:** If TaskMaster Prime is implemented as a `WorkflowAgent`, it will communicate with its sub-ordinate agents (which could be other `LlmAgent`s or specialized `ToolAgent`s wrapped as steps in the workflow) through the structured input/output mechanisms of the workflow itself. ADK `WorkflowAgent`s typically manage the data flow between their constituent steps/agents. This is highly structured and programmatic.
    *   **`ArtifactService` for Asynchronous Data Sharing:** Minions can produce outputs (e.g., research reports by AlphaIntel Scout, data compilations) and store them in the `ArtifactService`. Other Minions (e.g., LoreKeeper Scribe for archiving, TaskMaster Prime for aggregation) can then retrieve these artifacts by reference (e.g., an artifact ID passed via a chat message or as part of a task update). This is suitable for larger data payloads or when Minions don't need immediate, synchronous responses.
        *   Example: Minion Alpha completes a research sub-task, saves its report to `ArtifactService`, and sends a message via CommsRelay Connect to TaskMaster Prime: "Sub-task 'X' complete. Report artifact ID: 'xyz123'."
    *   **Direct Agent Invocation (Conceptual / Future ADK):** While ADK's primary model involves a `Runner` per agent, advanced scenarios might involve one agent (e.g., TaskMaster Prime) having a mechanism to directly (programmatically) invoke another agent's specific method or send it a structured message if both are running within the same backend process or a closely coupled environment. This would be for tightly coupled, high-performance interactions outside of a predefined workflow or chat. For V1, this is less likely to be a primary mechanism compared to Workflow or Artifacts/Chat.

*   **Distinction from AeroChat:**
    *   AeroChat is for *conversational* collaboration.
    *   ADK-centric mechanisms (Workflow I/O, ArtifactService) are for more *programmatic* and *data-oriented* collaboration. TaskMaster Prime might use chat to *assign* a task and get a high-level "done" notification, but the actual detailed instructions for a sub-agent within its workflow, or the passing of a large dataset, would use the more structured methods.

## 5. Session Management Plan

Session management in the ADK backend will address both the API interaction context and the internal operational context of Minion agents.

*   **V1 API Layer Session Management:**
    *   As per [`01_API_CONTRACT_V1.md`](../01_API_CONTRACT_V1.md:0), the primary API interaction is stateless, relying on an `X-API-Key` for authentication for each REST request. WebSocket connections will also be authenticated using this API key.
    *   The "session" from the GUI's perspective is effectively managed by the GUI client, which keeps track of relevant IDs (e.g., `minion_id`, `task_id`, `channel_id`) to make subsequent, related API calls.

*   **ADK `SessionService` Usage (V1 - `InMemorySessionService`):**
    *   ADK's `SessionService` (e.g., `InMemorySessionService` as used in [`adk_minion_army/main_adk.py`](../../../adk_minion_army/main_adk.py:0)) is used by the `Runner` to maintain context for an agent's interaction sequence. When `runner.run_async()` is called, a `session_id` is provided.
    *   **Purpose:** This service allows an agent to maintain conversational state across multiple turns within a single logical interaction (e.g., a Minion processing a sequence of messages in a chat, or TaskMaster Prime managing a multi-step task). It stores conversation history or intermediate state specific to that `runner` invocation sequence.
    *   **V1 Strategy:**
        *   For chat interactions via CommsRelay Connect, the `session_id` provided to the `Runner` could be derived from or mapped to the `channel_id`. The `SessionService` would then store the recent turn history for that Minion within that channel conversation, which is fed back into the Minion's prompt.
        *   For task processing (e.g., TaskMaster Prime handling a directive), the `session_id` could be linked to the `task_id`.
        *   The existing use of `session_id = agent.name` in [`adk_minion_army/main_adk.py`](../../../adk_minion_army/main_adk.py:0) is a simple approach for single-turn or basic interactions but will need to be more dynamic (e.g., based on task or channel context) for concurrent, distinct interactions with the same agent.

*   **Minion State and Conversational Context (AeroChat Diaries & Channel Context):**
    *   **AeroChat Diaries:** The "personal diaries" (emotional state, opinions) are a form of persistent Minion state, as described in [`AEROCHAT_INTEGRATION_STRATEGY.md`](./AEROCHAT_INTEGRATION_STRATEGY.md:0). These are *not* directly stored in the ADK `SessionService`'s turn-by-turn history but are a longer-term state.
        *   **Storage:** Likely `ArtifactService` (e.g., `diaries/{minion_id}/latest.json`) or a dedicated SQLite database, updated by the Minion after each `predict()` call.
        *   **Link to Session:** The Minion's `think()` method would retrieve its latest diary before `predict()` and include it in the prompt, effectively making this diary state part of the "session context" for that turn.
    *   **Channel Context:** The Channel Context Service provides participant lists and recent global channel history. This is also injected into the Minion's prompt for a given turn.

*   **Future Considerations for Persistent Sessions:**
    *   **Database-Backed `SessionService`:** If ADK agent interactions (especially workflows managed by TaskMaster Prime) become very long-running and need to survive backend restarts, a persistent `SessionService` (e.g., backed by Redis, Firestore, or a relational DB) would be necessary for the ADK `Runner`'s context.
    *   **Persistent `ArtifactService`:** Similarly, moving from `InMemoryArtifactService` to a persistent one (e.g., Google Cloud Storage, database blob storage) will be crucial for production to ensure task outputs, Minion diaries, and other artifacts are not lost.
    *   **User Authentication & Authorization:** Beyond V1's API key, full user authentication (e.g., OAuth2) would introduce a "user session" at the API gateway level. This user session could then be linked to tasks, Minion ownership/permissions, and channel access. The ADK `Runner`'s `user_id` parameter would then map to this authenticated user.
    *   **Scalability:** For a large number of concurrent Minions and interactions, the performance and scalability of session and artifact storage will be critical.

This document provides the foundational architectural plan for the ADK backend, aiming to balance the immediate needs of V1 with considerations for future evolution and complexity.