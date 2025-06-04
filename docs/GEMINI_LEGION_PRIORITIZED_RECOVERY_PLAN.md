# Gemini Legion: Prioritized Codebase Resurrection - The "Get Shit Done" Edition

## Preamble: No More Fucking Around

This isn't just a plan; it's a goddamn war strategy. We're taking the fight to the bugs, the mismatches, and the general fuckery detailed in [`wtfdude.md`](wtfdude.md) and the grand vision of [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md). The goal is to make this beast not just functional, but formidable. Priorities are tiered: Urgent (to stop the bleeding), High (to make it usable), Medium (to make it good), and Low (to make it shine for the future).

---

## 💣 TIER 1: URGENT - Core Functionality & Stability (Get it Fucking Working NOW)

**Objective:** Address immediate, show-stopping issues. If these aren't fixed, nothing else matters because the damn thing won't even limp, let alone run. These are primarily from `wtfdude.md`'s "Critical Priority" and "Immediate Fixes" sections.

- [x] 1. **WebSocket Base URL Correction (IMMEDIATE):**
    *   **Problem Ref:** [`wtfdude.md:771-778`](wtfdude.md:771-778), [`wtfdude.md:882-884`](wtfdude.md:882-884)
    *   **Action:** In `legionStore.ts`, ensure Socket.IO initializes with `http://` (e.g., `http://localhost:8000`) and other HTTP fetches use a dedicated `API_BASE_URL`.
    *   **Why:** Basic frontend-backend communication is impossible otherwise.

- [x] 2. **Critical Minion ID Field Mismatch:**
    *   **Problem Ref:** [`wtfdude.md:652-668`](wtfdude.md:652-668)
    *   **Action:** Standardize Minion ID. **Recommendation:** Backend consistently uses and returns `minion_id`. Frontend expects `minion_id`. This aligns with [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:63-67`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:63-67) where `minion_id` is prevalent.
    *   **Why:** Minion identification is fundamental. Broken ID references mean no minion operations work.

- [x] 3. **Critical API Endpoint Mismatches (Function Breakers):**
    - [x] **Minion Creation Endpoint:**** (Path aligned: `/api/minions/spawn`)
        *   **Problem Ref:** [`wtfdude.md:685-688`](wtfdude.md:685-688) (`/api/minions/` vs. `/api/minions/spawn`)
        *   **Action:** Align frontend calls with backend. Given the `IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md` focuses on service layers, a more descriptive `spawn` seems fitting if it's distinct from a general "create record" endpoint. Pick one, implement consistently.
        *   **Why:** Can't create minions if the endpoint is wrong.
    - [x] **Missing Persona Update Endpoint:**** (Endpoint exists: `PUT /api/minions/:minion_id/persona`)
        *   **Problem Ref:** [`wtfdude.md:696-699`](wtfdude.md:696-699)
        *   **Action:** Implement `PUT /api/minions/:minion_id/persona` in the backend.
        *   **Why:** Core functionality for minion customization is broken.
    - [x] **Missing Diary/Memory Endpoints:** (Basic GET for memories implemented: `GET /api/minions/:minion_id/memories`. Diary GET/POST deferred unless critical.)
        *   **Problem Ref:** [`wtfdude.md:701-706`](wtfdude.md:701-706)
        *   **Action:** Implement basic GET/POST for diary/memories if fundamental operations depend on them. The `IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md` has extensive memory/diary systems ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:170-210`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:170-210), [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:213-270`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:213-270)).
        *   **Why:** basic emotional state or context relies on these, they are critical.

- [x] 4. **Critical Channel Creation Schema Mismatch:**
    *   **Problem Ref:** [`wtfdude.md:710-722`](wtfdude.md:710-722) (`channel_type` vs. `is_private`)
    *   **Action:** Standardize. Backend likely expects `is_private: bool`. Frontend must send this, or backend needs an adapter.
    *   **Why:** Can't create channels correctly.

- [x] 5. **Input Validation & Basic Security (SQLi/XSS Prevention):** (Largely covered by FastAPI/Pydantic. SQLi N/A for now.)
    *   **Problem Ref:** [`wtfdude.md:127-131`](wtfdude.md:127-131)
    *   **Action:** Implement basic input sanitization/validation on all API endpoints (Pydantic in FastAPI is good for this). Ensure use of parameterized queries or ORM features.
    *   **Why:** Prevents catastrophic data corruption or security breaches *from the get-go*.

---

## 🔥 TIER 2: HIGH PRIORITY - Systemic Integrity & Key Feature Enablement (Make it Usable & Less Broken)

**Objective:** Fix remaining "Amnesia Gaps" that cause significant feature malfunction or data inconsistency. Address broader systemic issues that cripple usability or lead to frequent, hard-to-debug errors.

- [x] 1. **Resolve Remaining ID Field & Non-Critical Schema Mismatches:** (Channel `members` aligned; `task_id` aligned; `message_id` aligned; `ChannelResponse` simplified to `type`; frontend `Message` type includes `type`; `OpinionScoreResponse` enriched and aligned with domain.)
    *   **Problem Ref:** Channel Members vs. Participants ([`wtfdude.md:670-673`](wtfdude.md:670-673)), Task ID ([`wtfdude.md:675-677`](wtfdude.md:675-677)), Message ID ([`wtfdude.md:679-681`](wtfdude.md:679-681)); Channel Response dual fields ([`wtfdude.md:724-732`](wtfdude.md:724-732)), Message Type Enum ([`wtfdude.md:734-745`](wtfdude.md:734-745)), OpinionScore Structure ([`wtfdude.md:747-767`](wtfdude.md:747-767) - this one is critical for emotional display, so it's high).
    *   **Action:** Systematically review and align. Consistent naming is key. The `IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md` shows well-structured `OpinionScore` ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:105-125`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:105-125)), which should be the target.
    *   **Why:** Data integrity and feature completeness depend on these.

- [x] 2. **Resolve Remaining API Endpoint Mismatches:** (Emotional State `GET` endpoint benefits from richer `OpinionScoreResponse`; `POST` endpoint now uses structured `UpdateEmotionalStateRequest`.)
    *   **Problem Ref:** Emotional State Endpoints ([`wtfdude.md:690-694`](wtfdude.md:690-694)).
    *   **Action:** Align or standardize. The `IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md` implies a structured approach to emotional state ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:56-125`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:56-125)), so robust endpoints are necessary.
    *   **Why:** Key emotional features will be broken.

- [x] 3. **Address Channel Member Management Mismatch:** (Backend endpoints for add/remove member are now `POST /members` and `DELETE /members/{minion_id}`, aligned with RESTful practices and frontend API calls.)
    *   **Problem Ref:** [`wtfdude.md:795-804`](wtfdude.md:795-804) (body vs. query param).
    *   **Action:** Align frontend request with backend expectation.
    *   **Why:** Channel participation is a core feature.

- [x] 4. **Fundamental State Synchronization (Minion State):** (Per-agent `_state_lock` added to `MinionAgent` and applied to `think()` and `_update_emotional_state()` methods.)
    *   **Problem Ref:** [`wtfdude.md:109-113`](wtfdude.md:109-113)
    *   **Action:** Implement a basic locking mechanism or clear "single writer" pattern for critical, shared minion state to prevent race conditions. Defer complex solutions like full optimistic locking if simpler fixes suffice for now.
    *   **Why:** Inconsistent state leads to unpredictable behavior and data corruption.

- [x] 5. **Standardized Error Handling (API Level):** (Reviewed; FastAPI defaults and `HTTPException` usage provide a good baseline. Advanced error structuring is Tier 3+.)
    *   **Problem Ref:** [`wtfdude.md:115-119`](wtfdude.md:115-119)
    *   **Action:** Ensure all API endpoints return consistent error responses (e.g., defined HTTP status codes with JSON error bodies). Frontend needs to handle these gracefully. Start with backend services, then propagate.
    *   **Why:** Makes debugging massively easier and improves frontend stability.

- [x] 6. **Core Communication System Integration Verification:** (`ChannelService._websocket_broadcaster_callback` now persists messages from internal `InterMinionCommunicationSystem` router, ensuring they are saved and broadcast.)
    *   **Problem Ref Context:** [`wtfdude.md:807-813`](wtfdude.md:807-813), [`wtfdude.md:886-888`](wtfdude.md:886-888)
    *   **Action:** Ensure `InterMinionCommunicationSystem` callbacks robustly connect to `ChannelService` for message persistence and WebSocket broadcasting. Verify message flow end-to-end for basic chat.
    *   **Why:** Real-time communication is a cornerstone.

---

## ⭐ TIER 3: MEDIUM PRIORITY - Enhancements & Robustness (Make it Good)

**Objective:** Improve code quality, developer experience, and system resilience. Implement features that make the system more robust but are not immediate showstoppers.

- [ ] 1. **Performance Bottleneck Basics (N+1 Query Fixes):**
    *   **Problem Ref:** [`wtfdude.md:121-125`](wtfdude.md:121-125)
    *   **Action:** Identify and fix obvious N+1 query problems, especially in message loading or minion list displays. Use eager loading or data loader patterns.
    *   **Why:** Poor performance kills user experience.

- [ ] 2. **Initial Test Coverage (Critical Paths):**
    *   **Ref:** [`wtfdude.md:141`](wtfdude.md:141)
    *   **Action:** Add unit/integration tests for core API endpoints, critical service logic (e.g., minion spawning, message sending), and state update mechanisms.
    *   **Why:** Prevents regressions and builds confidence for further refactoring.

- [ ] 3. **Static Code Analysis & Formatting:**
    *   **Ref:** [`wtfdude.md:142`](wtfdude.md:142)
    *   **Action:** Implement linters (e.g., Flake8/Pylint for Python, ESLint for TS) and formatters (Black, Prettier). Enforce in CI if possible.
    *   **Why:** Improves code consistency and catches bugs early.

- [ ] 4. **Basic API Documentation:**
    *   **Ref:** [`wtfdude.md:143`](wtfdude.md:143)
    *   **Action:** Auto-generate OpenAPI/Swagger docs for FastAPI. Document key WebSocket events and their payloads.
    *   **Why:** Essential for frontend/backend alignment and new developer onboarding.

- [ ] 5. **Structured Logging (Initial Pass):**
    *   **Ref:** [`wtfdude.md:153`](wtfdude.md:153)
    *   **Action:** Implement basic structured logging (e.g., JSON logs) for key events and errors in the backend.
    *   **Why:** Vastly improves debugging and monitoring capabilities.

---

## ✨ TIER 4: LOW PRIORITY - Advanced Optimizations & Future-Proofing (Make it Shine)

**Objective:** Implement advanced architectural patterns, further optimize performance, and prepare for future scalability and features. These are "nice-to-haves" once the core is solid.

- [ ] 1. **Advanced Architectural Patterns (CQRS, Event Sourcing - If Warranted):**
    *   **Ref:** [`wtfdude.md:136-137`](wtfdude.md:136-137)
    *   **Action:** Evaluate specific areas where these patterns would bring significant benefits. Don't implement for the sake of it.
    *   **Why:** Can improve scalability and maintainability for complex systems but add overhead.

- [ ] 2. **Advanced Performance Optimizations (Caching, Indexing):**
    *   **Ref:** [`wtfdude.md:146-148`](wtfdude.md:146-148)
    *   **Action:** Implement caching for frequently accessed data. Add/optimize database indexes based on performance profiling.
    *   **Why:** For scaling under load.

- [ ] 3. **Comprehensive Monitoring & Observability (Distributed Tracing, Metrics):**
    *   **Ref:** [`wtfdude.md:151-152`](wtfdude.md:151-152)
    *   **Action:** Implement distributed tracing and detailed metrics collection.
    *   **Why:** Essential for understanding system behavior in production.

- [ ] 4. **Full Test Suite & Chaos Engineering:**
    *   **Ref:** [`wtfdude.md:172-178`](wtfdude.md:172-178)
    *   **Action:** Aim for high test coverage across all component types. Experiment with chaos engineering.
    *   **Why:** Builds a highly resilient system.

- [ ] 5. **Refactor for "Future Enhancements":**
    *   **Ref:** [`wtfdude.md:188-194`](wtfdude.md:188-194)
    *   **Action:** Review architecture with future goals in mind (multi-modal, plugins, etc.) and make preparatory refactors.
    *   **Why:** Eases future development.

---

## 🕵️ Section: Gemini API Calls, Keys, and Model Configuration

This section will detail how Gemini models are intended to be used within the system, based on the provided architectural documents and common practices with Google's ADK. *This is based on design; actual implementation needs verification.*

**Conceptual Overview (Based on [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md)):**

*   **ADK Abstraction:** The system is designed to use Google's Agent Development Kit (ADK). The ADK typically handles the direct interaction with the Gemini (or other Google) LLMs. Your `MinionAgent` ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:301`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:301)) likely inherits from an ADK base class like `LlmAgent`. also /[`adk-documentation/`] folder for more info on ADK.
*   **Model Configuration via Persona:** The specific Gemini model, generation parameters (temperature, top_p, etc.), and other LLM settings are likely configured within a `MinionPersona` object, specifically a `model_config` attribute. The `MinionAgent` would then use `persona.model_config.to_adk_model()` ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:320`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:320)) to pass this configuration to the ADK's `LlmAgent`.
*   **API Key Management:** API keys for Google AI services (including Gemini) are typically managed through environment variables (e.g., `GOOGLE_API_KEY` or `GEMINI_API_KEY`) or a dedicated configuration service. The ADK or your custom adapter code would read these keys.
*   **Making Calls:** Your `MinionAgent`'s `think()` or `predict()` methods ([`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:330`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:330), [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:418`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md:418)) would prepare the context (instruction, memory, emotional state modifiers) and then call the underlying ADK `LlmAgent`'s corresponding method. The ADK then constructs the actual API request to the Gemini API, sends it, and returns the response.

**How to Configure (Expected):**

1.  **API Key(s):**
    *   **Environment Variable:** Set `GOOGLE_API_KEY` (or a similar variable name the ADK expects or your `settings.py` reads) in your environment (e.g., in a `.env` file that your application loads, or directly in your deployment environment).
    *   **Multiple Keys:** If you need to use multiple keys (e.g., for different minions or rate limiting), this would require custom logic. The ADK might not support this out-of-the-box per agent. You might need to:
        *   Rotate keys at the application level before initializing agents.
        *   Modify or wrap the ADK's LLM interaction layer to select a key based on the minion or a pool. This is an advanced customization. The [`IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md`](IDEAL_ARCHITECTURE_DESIGN_DOCUMENT.md) does not explicitly detail per-minion API keys.

2.  **Specific Gemini Model:**
    *   This should be part of the `MinionPersona`'s `model_config`. You'd define which Gemini model to use (e.g., "gemini-2.5-pro-preview-05-06", "gemini-2.0-flash-lite", etc.) within this configuration object for each minion type or instance.
    *   Example (conceptual, actual structure depends on your `MinionPersona` and `ModelConfig` classes):
        ```python
        # In your persona definition or minion creation logic:
        class MyModelConfig:
            def __init__(self, model_name="gemini-2.5-pro-preview-05-06", temperature=0.7):
                self.model_name = model_name
                self.temperature = temperature
            
            def to_adk_model(self):
                # This would return an ADK-compatible model configuration object
                # from adk.llm import ModelOptions # Fictional ADK import
                # return ModelOptions(name=self.model_name, temperature=self.temperature)
                pass

        persona = MinionPersona(
            name="HelperBot",
            model_config=MyModelConfig(model_name="gemini-2.5-pro-preview-05-06")
        )
        ```

**Code Locations to Investigate (Next Steps for You/Me):**

*   **`gemini_legion_backend/core/domain/minion.py`:** For `MinionPersona` and `ModelConfig` structure.
*   **`gemini_legion_backend/core/infrastructure/adk/agents/minion_agent.py`:** To see how `LlmAgent` (or equivalent) is initialized and how `model_config` is used.
*   **`gemini_legion_backend/config/settings.py`:** For API key loading from environment variables.
*   **Root `.env` file (if it exists):** To check for `GOOGLE_API_KEY` definitions.
*   **ADK Documentation:** Refer to the specific Google ADK version's documentation for definitive details on API key setup and model configuration. [`adk-documentation/`] folder for more info on ADK.

This Gemini API section provides a high-level guide. A deep dive into the specific ADK library version you're using and your custom code is needed for exact implementation details.

---
This plan provides a structured, prioritized approach. We'll start with the URGENT fixes to get a basic, somewhat stable system, then progressively build up.