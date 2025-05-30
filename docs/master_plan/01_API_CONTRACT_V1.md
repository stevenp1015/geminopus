# API Contract V1: Legion Commander GUI & Minion Army

## 1. Introduction

This document defines the V1 API contract for communication between the **Legion Commander GUI** (Next.js/React frontend) and the **Minion Army** (Python ADK backend). The primary goal is to establish a clear, detailed, and robust interface for managing Minions, orchestrating tasks, and facilitating real-time communication via AeroChat.

**Chosen Protocol: RESTful API with WebSockets**

**Justification:**

*   **Ease of Use & Familiarity:** REST is ubiquitously supported by web browsers and frameworks like Next.js/React. This simplifies frontend integration and leverages widespread developer expertise.
*   **Standardization & Tooling:** HTTP methods (GET, POST, PUT, DELETE) and status codes provide a well-understood convention. Rich tooling like Postman, OpenAPI/Swagger for documentation and client generation is readily available.
*   **Statelessness:** REST's stateless nature simplifies backend scaling and request handling for many operations.
*   **WebSocket for Real-time:** For functionalities requiring real-time, bidirectional communication (chat, live log streaming, instant Minion status updates), WebSockets will be employed. This complements REST by handling stateful, persistent connections where needed, without the overhead of gRPC-Web for all interactions.
*   **Type Safety:** While gRPC enforces type safety via Protobuf, a combination of OpenAPI specifications, TypeScript on the frontend, and Pydantic models on the Python backend will provide robust type checking and validation for REST endpoints.
*   **Flexibility for V1:** This hybrid approach allows for rapid development of standard CRUD operations via REST, while specifically addressing real-time needs with WebSockets, offering a balanced and pragmatic solution for V1.

## 2. Authentication & Authorization

*   **Authentication:** For V1, a simple API Key-based authentication will be considered. The API key will be passed in a custom HTTP header (e.g., `X-API-Key: <your_api_key>`).
*   **Authorization:** Specific roles or permissions are not defined for V1 but will be a consideration for future iterations. All authenticated requests are currently assumed to have full access.
*   **WebSocket Authentication:** The WebSocket connection handshake will likely require the same API key, potentially passed as a query parameter or during an initial HTTP upgrade request.

## 3. Common Data Structures & Enums

### Enums

```json
{
  "MinionStatus": [
    "IDLE",        // Waiting for tasks
    "ACTIVE",      // Actively working on a task
    "CONFIGURING", // Being updated by Commander
    "ERROR",       // Encountered an unrecoverable error
    "OFFLINE",     // Not reachable
    "STARTING",    // In the process of initializing
    "STOPPED"      // Intentionally stopped
  ],
  "TaskState": [
    "PENDING",     // Submitted, not yet started
    "RUNNING",     // Actively being processed
    "PAUSED",      // Temporarily suspended
    "COMPLETED",   // Successfully finished
    "FAILED",      // Ended due to an error
    "CANCELLED"    // Terminated by user/system
  ],
  "LogLevel": [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
  ],
  "ChatParticipantType": [
    "USER",
    "MINION"
  ],
  "ModelProvider": [
    "OPENAI",
    "ANTHROPIC",
    "GOOGLE_GEMINI",
    "OPENROUTER",
    "LOCAL_LLM" // For future expansion
  ]
}
```

### Common Schemas

**`ErrorResponse`**
```json
{
  "type": "object",
  "properties": {
    "error_code": { "type": "string", "description": "A machine-readable error code" },
    "message": { "type": "string", "description": "A human-readable error message" },
    "details": { "type": "object", "additionalProperties": true, "description": "Optional additional error details" }
  },
  "required": ["error_code", "message"]
}
```

**`Timestamp`**
```json
{
  "type": "string",
  "format": "date-time",
  "description": "ISO 8601 timestamp"
}
```

**`PaginationInfo`**
```json
{
  "type": "object",
  "properties": {
    "page": { "type": "integer", "minimum": 1 },
    "per_page": { "type": "integer", "minimum": 1, "maximum": 100 },
    "total_items": { "type": "integer" },
    "total_pages": { "type": "integer" }
  },
  "required": ["page", "per_page", "total_items", "total_pages"]
}
```

## 4. Minion Management Endpoints

### 4.1. List Minions

*   **Method:** `GET`
*   **URL:** `/api/v1/minions`
*   **Query Parameters:**
    *   `status` (string, optional): Filter by `MinionStatus`
    *   `page` (integer, optional, default: 1)
    *   `per_page` (integer, optional, default: 20)
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "minions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string", "format": "uuid" },
              "name": { "type": "string" },
              "status": { "$ref": "#/components/schemas/MinionStatus" },
              "current_task_snippet": { "type": "string", "nullable": true, "description": "A brief summary of the current task" },
              "last_seen": { "$ref": "#/components/schemas/Timestamp" }
            },
            "required": ["id", "name", "status", "last_seen"]
          }
        },
        "pagination": { "$ref": "#/components/schemas/PaginationInfo" }
      },
      "required": ["minions", "pagination"]
    }
    ```
*   **Common Error Responses:** 400, 401, 500

### 4.2. Get Minion Details

*   **Method:** `GET`
*   **URL:** `/api/v1/minions/{minion_id}`
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string" },
        "status": { "$ref": "#/components/schemas/MinionStatus" },
        "persona_prompt": { "type": "string" },
        "model_config": {
          "type": "object",
          "properties": {
            "provider": { "$ref": "#/components/schemas/ModelProvider" },
            "model_id": { "type": "string", "description": "e.g., 'gpt-4-turbo', 'claude-3-opus-20240229'" },
            "params": {
              "type": "object",
              "additionalProperties": true,
              "description": "Model-specific parameters like temperature, max_tokens, etc."
            }
          },
          "required": ["provider", "model_id"]
        },
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "description": { "type": "string" },
              "enabled": { "type": "boolean" }
            },
            "required": ["name", "enabled"]
          }
        },
        "current_task": {
          "type": "object",
          "nullable": true,
          "properties": {
            "task_id": { "type": "string", "format": "uuid" },
            "description": { "type": "string" },
            "state": { "$ref": "#/components/schemas/TaskState" },
            "started_at": { "$ref": "#/components/schemas/Timestamp" }
          }
        },
        "recent_logs_snippet": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/LogEntry" },
          "description": "A small snippet of the most recent logs"
        },
        "created_at": { "$ref": "#/components/schemas/Timestamp" },
        "updated_at": { "$ref": "#/components/schemas/Timestamp" }
      },
      "required": ["id", "name", "status", "persona_prompt", "model_config", "tools", "created_at", "updated_at"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404, 500

### 4.3. Fetch Minion Logs

*   **Method:** `GET`
*   **URL:** `/api/v1/minions/{minion_id}/logs`
*   **Query Parameters:**
    *   `page` (integer, optional, default: 1)
    *   `per_page` (integer, optional, default: 50)
    *   `level` (string, optional): Filter by `LogLevel`
    *   `start_time` (`Timestamp`, optional): Filter logs after this time
    *   `end_time` (`Timestamp`, optional): Filter logs before this time
    *   `search_term` (string, optional): Full-text search in log messages
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "logs": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/LogEntry" }
        },
        "pagination": { "$ref": "#/components/schemas/PaginationInfo" }
      },
      "required": ["logs", "pagination"]
    }
    ```
    **`LogEntry` Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "timestamp": { "$ref": "#/components/schemas/Timestamp" },
        "level": { "$ref": "#/components/schemas/LogLevel" },
        "message": { "type": "string" },
        "source": { "type": "string", "description": "e.g., 'MinionCore', 'ToolManager'" }
      },
      "required": ["timestamp", "level", "message"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404, 500
*   **WebSocket Alternative:** A WebSocket endpoint `/ws/v1/minions/{minion_id}/logs/stream` could provide real-time log streaming.
    *   Client sends: `{ "action": "subscribe_logs", "filters": { "level": "INFO" } }`
    *   Server sends: `LogEntry` objects as they occur.

### 4.4. Fetch Minion Personal Diaries

*   **Method:** `GET`
*   **URL:** `/api/v1/minions/{minion_id}/diaries`
*   **Query Parameters:**
    *   `page` (integer, optional, default: 1)
    *   `per_page` (integer, optional, default: 10)
    *   `start_date` (string, format: date, optional): Filter entries on or after this date
    *   `end_date` (string, format: date, optional): Filter entries on or before this date
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "diaries": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/DiaryEntry" }
        },
        "pagination": { "$ref": "#/components/schemas/PaginationInfo" }
      },
      "required": ["diaries", "pagination"]
    }
    ```
    **`DiaryEntry` Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "entry_id": { "type": "string", "format": "uuid" },
        "minion_id": { "type": "string", "format": "uuid" },
        "timestamp": { "$ref": "#/components/schemas/Timestamp" },
        "title": { "type": "string", "nullable": true },
        "content": { "type": "string", "description": "The diary entry text, likely markdown." },
        "mood_tags": { "type": "array", "items": { "type": "string" }, "nullable": true },
        "related_task_id": { "type": "string", "format": "uuid", "nullable": true }
      },
      "required": ["entry_id", "minion_id", "timestamp", "content"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404, 500

### 4.5. Update Minion Configuration (Commander "God-Mode")

*   **Method:** `PUT`
*   **URL:** `/api/v1/minions/{minion_id}/config`
*   **Request Payload:**
    ```json
    {
      "type": "object",
      "properties": {
        "name": { "type": "string", "description": "New Minion name" },
        "persona_prompt": { "type": "string", "description": "New persona prompt" },
        "model_config": {
          "type": "object",
          "properties": {
            "provider": { "$ref": "#/components/schemas/ModelProvider" },
            "model_id": { "type": "string" },
            "params": { "type": "object", "additionalProperties": true }
          }
        },
        "tools": {
          "type": "array",
          "description": "List of tools with their enabled status. Only tools present in this list will be considered; tools not listed might be disabled or retain their current state based on backend logic (clarify).",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "enabled": { "type": "boolean" }
            },
            "required": ["name", "enabled"]
          }
        }
      },
      "minProperties": 1, // At least one field must be provided for update
      "description": "Backend handles applying these changes. May trigger Minion reload/restart. Response indicates success/failure of applying changes. Real-time updates pushed via WebSocket."
    }
    ```
*   **Response Payload (200 OK):** Returns the updated Minion details (see 4.2 Get Minion Details).
    ```json
    // Same as 4.2 Get Minion Details response
    ```
*   **Response Payload (202 Accepted):** If changes require a reload and are processed asynchronously.
    ```json
    {
      "type": "object",
      "properties": {
        "message": { "type": "string", "example": "Minion configuration update initiated. See WebSocket for status." },
        "minion_id": { "type": "string", "format": "uuid" }
      }
    }
    ```
*   **Common Error Responses:** 400 (Validation Error), 401, 404, 500
*   **WebSocket for Real-time Status:** `/ws/v1/minions/{minion_id}/status`
    *   Server sends: Updated Minion details or status changes (e.g., `CONFIGURING` -> `IDLE` / `ACTIVE`).

### 4.6. Spawn New Minion

*   **Method:** `POST`
*   **URL:** `/api/v1/minions`
*   **Request Payload:**
    ```json
    {
      "type": "object",
      "properties": {
        "name": { "type": "string", "description": "Minion name" },
        "persona_prompt": { "type": "string", "description": "Initial persona prompt" },
        "model_config": {
          "type": "object",
          "properties": {
            "provider": { "$ref": "#/components/schemas/ModelProvider" },
            "model_id": { "type": "string" },
            "params": { "type": "object", "additionalProperties": true }
          },
          "required": ["provider", "model_id"]
        },
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "enabled": { "type": "boolean" }
            },
            "required": ["name", "enabled"]
          },
          "description": "Initial tool configuration"
        }
        // "template_id": { "type": "string", "format": "uuid", "nullable": true, "description": "Optional ID of a Minion template to spawn from" }
      },
      "required": ["name", "persona_prompt", "model_config"]
    }
    ```
*   **Response Payload (201 Created):** Returns the newly created Minion details (see 4.2 Get Minion Details).
    ```json
    // Same as 4.2 Get Minion Details response, with 'status' likely 'STARTING' or 'IDLE'
    ```
*   **Common Error Responses:** 400 (Validation Error), 401, 500

## 5. Task Management Endpoints

### 5.1. Send New Directive/Task

*   **Method:** `POST`
*   **URL:** `/api/v1/tasks`
*   **Request Payload:**
    ```json
    {
      "type": "object",
      "properties": {
        "minion_ids": {
          "type": "array",
          "items": { "type": "string", "format": "uuid" },
          "description": "List of Minion IDs to assign this task. If empty or null, may go to a TaskMaster or be queued for general assignment (TBD)."
        },
        // "target_group_id": { "type": "string", "description": "Alternative to minion_ids, for targeting a pre-defined group"},
        "directive": { "type": "string", "description": "The main instruction or goal for the task." },
        "priority": { "type": "integer", "default": 0, "description": "Task priority (higher is more important)" },
        "context_data": {
          "type": "object",
          "additionalProperties": true,
          "description": "Any relevant data or files needed for the task. Structure TBD, could include file references or inline data."
        },
        "metadata": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Optional key-value pairs for task metadata (e.g., source, user_id)."
        }
      },
      "required": ["directive"],
      "oneOf": [ // Either minion_ids or potentially a TaskMaster target should be defined
        { "required": ["minion_ids"] }
        // { "description": "Logic for TaskMaster assignment or unassigned queue" }
      ]
    }
    ```
*   **Response Payload (202 Accepted):**
    ```json
    {
      "type": "object",
      "properties": {
        "task_id": { "type": "string", "format": "uuid" },
        "message": { "type": "string", "example": "Task submitted successfully." },
        "status_url": { "type": "string", "format": "url", "example": "/api/v1/tasks/{task_id}" },
        "initial_state": { "$ref": "#/components/schemas/TaskState" }
      },
      "required": ["task_id", "message", "status_url", "initial_state"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404 (if specified Minion ID doesn't exist), 500

### 5.2. Fetch Task Progress Update

*   **Method:** `GET`
*   **URL:** `/api/v1/tasks/{task_id}`
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "task_id": { "type": "string", "format": "uuid" },
        "directive": { "type": "string" },
        "state": { "$ref": "#/components/schemas/TaskState" },
        "assigned_minions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "minion_id": { "type": "string", "format": "uuid" },
              "name": { "type": "string" },
              "status_on_task": { "type": "string", "description": "e.g., 'Processing step 1', 'Awaiting user input'" }
            }
          }
        },
        "progress_percentage": { "type": "number", "format": "float", "minimum": 0, "maximum": 100, "nullable": true },
        "current_step_description": { "type": "string", "nullable": true },
        "sub_tasks": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/SubTaskInfo" }, // Recursive definition if needed
          "nullable": true
        },
        "logs": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/LogEntry" },
          "description": "Relevant logs for this task. Could be paginated if extensive."
        },
        "created_at": { "$ref": "#/components/schemas/Timestamp" },
        "started_at": { "$ref": "#/components/schemas/Timestamp", "nullable": true },
        "updated_at": { "$ref": "#/components/schemas/Timestamp" },
        "completed_at": { "$ref": "#/components/schemas/Timestamp", "nullable": true },
        "metadata": { "type": "object", "additionalProperties": { "type": "string" } }
      },
      "required": ["task_id", "directive", "state", "created_at", "updated_at"]
    }
    ```
    **`SubTaskInfo` Schema (Example):**
    ```json
    {
        "type": "object",
        "properties": {
            "sub_task_id": {"type": "string", "format": "uuid"},
            "description": {"type": "string"},
            "state": {"$ref": "#/components/schemas/TaskState"},
            "assigned_minion_id": {"type": "string", "format": "uuid", "nullable": true}
        },
        "required": ["sub_task_id", "description", "state"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404, 500
*   **WebSocket for Real-time Progress:** `/ws/v1/tasks/{task_id}/updates`
    *   Server sends updates to the Task object as its state or progress changes.

### 5.3. Fetch Task Final Results/Artifacts

*   **Method:** `GET`
*   **URL:** `/api/v1/tasks/{task_id}/results`
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "task_id": { "type": "string", "format": "uuid" },
        "state": { "$ref": "#/components/schemas/TaskState", "description": "Should be COMPLETED or FAILED" },
        "summary": { "type": "string", "nullable": true, "description": "A human-readable summary of the outcome." },
        "artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "artifact_id": { "type": "string", "format": "uuid" },
              "name": { "type": "string" },
              "type": { "type": "string", "description": "e.g., 'text/plain', 'image/png', 'application/json', 'reference/url'" },
              "size_bytes": { "type": "integer", "nullable": true },
              "content": { "type": "string", "description": "Inline content for small artifacts, or a reference/URL for larger ones." },
              "download_url": { "type": "string", "format": "url", "nullable": true, "description": "URL to download larger artifacts" },
              "created_at": { "$ref": "#/components/schemas/Timestamp" }
            },
            "required": ["artifact_id", "name", "type", "created_at"]
          }
        },
        "error_details": { "$ref": "#/components/schemas/ErrorResponse", "nullable": true, "description": "Present if state is FAILED" }
      },
      "required": ["task_id", "state", "artifacts"]
    }
    ```
*   **Common Error Responses:** 400, 401, 404 (Task not found or not completed), 500

## 6. Real-time Chat (AeroChat Integration) Endpoints (via WebSocket)

AeroChat primarily uses WebSockets for real-time message exchange. A base WebSocket endpoint will be `/ws/v1/chat`.
After connection, messages are exchanged in a JSON format.

**WebSocket Connection:**
*   **URL:** `/ws/v1/chat`
*   **Authentication:** Via query parameter `apiKey=<your_api_key>` during handshake.

**Common WebSocket Message Structure:**
```json
{
  "type": "string", // e.g., "send_message", "receive_message", "join_channel", "error"
  "payload": {
    // Structure varies based on 'type'
  },
  "request_id": { "type": "string", "format": "uuid", "nullable": true, "description": "Client-generated ID to correlate requests and responses/acks" }
}
```

### 6.1. Send Chat Message (Client -> Server)

*   **Message `type`:** `send_message`
*   **Payload:**
    ```json
    {
      "channel_id": { "type": "string", "format": "uuid" },
      "content": { "type": "string", "description": "The message text. Can include markdown." },
      "sender_id": { "type": "string", "description": "User ID or Minion ID sending the message (implicitly User if from GUI)" },
      "sender_type": { "$ref": "#/components/schemas/ChatParticipantType", "description": "Typically USER from GUI" },
      "mentions": { // Optional
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"}, // User ID or Minion ID
                "type": {"$ref": "#/components/schemas/ChatParticipantType"}
            },
            "required": ["id", "type"]
        }
      }
    }
    ```
*   **Server Acknowledgement (Optional):**
    *   `type`: `message_sent_ack`
    *   `payload`: `{ "message_id": "uuid", "timestamp": "iso_timestamp", "status": "delivered_to_server" }`
    *   `request_id`: (mirrors client's `request_id`)

### 6.2. Receive Chat Message (Server -> Client)

*   **Message `type`:** `receive_message`
*   **Payload:**
    ```json
    {
      "message_id": { "type": "string", "format": "uuid" },
      "channel_id": { "type": "string", "format": "uuid" },
      "sender": {
        "type": "object",
        "properties": {
          "id": { "type": "string" }, // User ID or Minion ID
          "name": { "type": "string" },
          "type": { "$ref": "#/components/schemas/ChatParticipantType" },
          "avatar_url": { "type": "string", "format": "url", "nullable": true }
        },
        "required": ["id", "name", "type"]
      },
      "content": { "type": "string" },
      "timestamp": { "$ref": "#/components/schemas/Timestamp" },
      "mentions": { /* same as in send_message */ },
      "is_diary_entry_link": {"type": "boolean", "default": false}, // If this message is a special link to a diary entry
      "diary_entry_details": { // Present if is_diary_entry_link is true
        "type": "object",
        "properties": {
            "minion_id": {"type": "string", "format": "uuid"},
            "entry_id": {"type": "string", "format": "uuid"},
            "title_snippet": {"type": "string"}
        }
      }
    }
    ```

### 6.3. List Available Chat Channels (REST)

*   **Method:** `GET`
*   **URL:** `/api/v1/chat/channels`
*   **Query Parameters:**
    *   `page` (integer, optional, default: 1)
    *   `per_page` (integer, optional, default: 20)
    *   `member_id` (string, optional): Filter channels by a specific member (user or minion) ID.
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "channels": {
          "type": "array",
          "items": { "$ref": "#/components/schemas/ChatChannelSummary" }
        },
        "pagination": { "$ref": "#/components/schemas/PaginationInfo" }
      },
      "required": ["channels", "pagination"]
    }
    ```
    **`ChatChannelSummary` Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string", "nullable": true, "description": "Channel name, if any (e.g., for group chats)" },
        "type": { "type": "string", "enum": ["DIRECT", "GROUP", "SYSTEM"], "description": "System for Minion diaries maybe?" },
        "last_message_snippet": { "type": "string", "nullable": true },
        "last_message_timestamp": { "$ref": "#/components/schemas/Timestamp", "nullable": true },
        "unread_count": { "type": "integer", "default": 0 },
        "participants_summary": { // Brief summary, full list in Get Channel Details
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {"type": "string"},
              "name": {"type": "string"},
              "type": {"$ref": "#/components/schemas/ChatParticipantType"}
            }
          }
        }
      },
      "required": ["id", "type"]
    }
    ```
*   **Common Error Responses:** 400, 401, 500

### 6.4. Create New Chat Channel (REST)

*   **Method:** `POST`
*   **URL:** `/api/v1/chat/channels`
*   **Request Payload:**
    ```json
    {
      "type": "object",
      "properties": {
        "name": { "type": "string", "nullable": true, "description": "Optional name for group channels" },
        "participants": {
          "type": "array",
          "minItems": 2,
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string", "description": "User ID or Minion ID" },
              "type": { "$ref": "#/components/schemas/ChatParticipantType" }
            },
            "required": ["id", "type"]
          },
          "description": "List of participants. Must include the initiating user implicitly or explicitly."
        },
        "purpose": { "type": "string", "nullable": true, "description": "Optional purpose/description of the channel" }
      },
      "required": ["participants"]
    }
    ```
*   **Response Payload (201 Created):** Returns the full channel details (see 7.2 Get Channel Details).
    ```json
    // Same as 7.2 Get Channel Details response
    ```
*   **Common Error Responses:** 400 (e.g., invalid participant IDs), 401, 500

### 6.5. Get Message History for a Channel (REST)

*   **Method:** `GET`
*   **URL:** `/api/v1/chat/channels/{channel_id}/messages`
*   **Query Parameters:**
    *   `before_message_id` (string, format: uuid, optional): Fetch messages before this ID (for pagination backwards).
    *   `after_message_id` (string, format: uuid, optional): Fetch messages after this ID (for fetching newer messages).
    *   `limit` (integer, optional, default: 50, max: 100): Number of messages to fetch.
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "messages": {
          "type": "array",
          "items": {
            // Same as 'receive_message' payload in WebSocket (6.2)
            "$ref": "#/components/schemas/ChatMessage"
          }
        },
        "has_more_older": { "type": "boolean", "description": "True if older messages are available" },
        "has_more_newer": { "type": "boolean", "description": "True if newer messages are available (less common for typical history fetch)" }
      },
      "required": ["messages", "has_more_older", "has_more_newer"]
    }
    ```
    **`ChatMessage` Schema (for REST, matches WebSocket `receive_message` payload):**
    ```json
    {
      "type": "object",
      "properties": {
        "message_id": { "type": "string", "format": "uuid" },
        "channel_id": { "type": "string", "format": "uuid" },
        "sender": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "name": { "type": "string" },
            "type": { "$ref": "#/components/schemas/ChatParticipantType" },
            "avatar_url": { "type": "string", "format": "url", "nullable": true }
          },
          "required": ["id", "name", "type"]
        },
        "content": { "type": "string" },
        "timestamp": { "$ref": "#/components/schemas/Timestamp" },
        "mentions": { /* ... */ },
        "is_diary_entry_link": {"type": "boolean", "default": false},
        "diary_entry_details": { /* ... */ }
      },
      "required": ["message_id", "channel_id", "sender", "content", "timestamp"]
    }
    ```
*   **Common Error Responses:** 400, 401, 403 (Not a member of channel), 404, 500

### 6.6. Subscribe to Channel Events (Client -> Server via WebSocket)
*   **Message `type`:** `join_channel`
*   **Payload:**
    ```json
    {
      "channel_id": { "type": "string", "format": "uuid" }
    }
    ```
*   **Server Acknowledgement/Response:**
    *   `type`: `channel_joined`
    *   `payload`: `{ "channel_id": "uuid", "status": "subscribed", "current_participants": [/* participant objects */] }`
    *   `request_id`: (mirrors client's `request_id`)
    *   Server then starts sending `receive_message` for new messages, and other channel events like `participant_joined`, `participant_left`.

### 6.7. Unsubscribe from Channel Events (Client -> Server via WebSocket)
*   **Message `type`:** `leave_channel`
*   **Payload:**
    ```json
    {
      "channel_id": { "type": "string", "format": "uuid" }
    }
    ```
*   **Server Acknowledgement/Response:**
    *   `type`: `channel_left`
    *   `payload`: `{ "channel_id": "uuid", "status": "unsubscribed" }`
    *   `request_id`: (mirrors client's `request_id`)

## 7. Channel Management Endpoints (REST)

(List and Create are covered in 6.3 and 6.4 as they are tightly coupled with chat setup. This section details further management.)

### 7.1. List Channels (Duplicate of 6.3 for structural completeness)
*   **Method:** `GET`
*   **URL:** `/api/v1/chat/channels`
*   (See 6.3 for full details)

### 7.2. Create Channel (Duplicate of 6.4 for structural completeness)
*   **Method:** `POST`
*   **URL:** `/api/v1/chat/channels`
*   (See 6.4 for full details)

### 7.3. Get Channel Details

*   **Method:** `GET`
*   **URL:** `/api/v1/chat/channels/{channel_id}`
*   **Request Payload:** N/A
*   **Response Payload (200 OK):**
    ```json
    {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string", "nullable": true },
        "type": { "type": "string", "enum": ["DIRECT", "GROUP", "SYSTEM"] },
        "purpose": { "type": "string", "nullable": true },
        "participants": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string" }, // User ID or Minion ID
              "name": { "type": "string" },
              "type": { "$ref": "#/components/schemas/ChatParticipantType" },
              "avatar_url": { "type": "string", "format": "url", "nullable": true },
              "is_admin": { "type": "boolean", "default": false } // For group channels
            },
            "required": ["id", "name", "type"]
          }
        },
        "created_at": { "$ref": "#/components/schemas/Timestamp" },
        "updated_at": { "$ref": "#/components/schemas/Timestamp" },
        "creator_id": { "type": "string", "description": "ID of the user/minion who created the channel", "nullable": true}
      },
      "required": ["id", "type", "participants", "created_at", "updated_at"]
    }
    ```
*   **Common Error Responses:** 400, 401, 403 (Not a member), 404, 500

### 7.4. Edit Channel (Optional V1)

*   **Method:** `PUT`
*   **URL:** `/api/v1/chat/channels/{channel_id}`
*   **Request Payload:**
    ```json
    {
      "type": "object",
      "properties": {
        "name": { "type": "string", "nullable": true },
        "purpose": { "type": "string", "nullable": true },
        "participants_to_add": { // Only for group channels
          "type": "array",
          "items": { /* participant object as in create channel */ }
        },
        "participants_to_remove": { // Only for group channels
          "type": "array",
          "items": { "type": "string", "description": "ID of participant to remove" }
        }
      },
      "minProperties": 1
    }
    ```
*   **Response Payload (200 OK):** Returns updated Channel Details (see 7.3).
*   **Common Error Responses:** 400, 401, 403 (Not admin/permission denied), 404, 500
*   **WebSocket Event:** `channel_updated` sent to members with new channel details.

### 7.5. Delete Channel (Optional V1)

*   **Method:** `DELETE`
*   **URL:** `/api/v1/chat/channels/{channel_id}`
*   **Request Payload:** N/A
*   **Response Payload (204 No Content):**
*   **Common Error Responses:** 401, 403 (Not admin/permission denied), 404, 500
*   **WebSocket Event:** `channel_deleted` sent to members.

## 8. General Error Responses (REST)

These are common HTTP status codes and their general meaning in this API. The response body will typically use the `ErrorResponse` schema.

*   **400 Bad Request:** The request was malformed, contained invalid data, or violated schema constraints. The `ErrorResponse` should provide details.
    *   Example: `{ "error_code": "VALIDATION_ERROR", "message": "Invalid email format for participant.", "details": { "field": "participants[0].email" } }`
*   **401 Unauthorized:** Authentication failed or was not provided. The `X-API-Key` header is missing or invalid.
    *   Example: `{ "error_code": "AUTH_REQUIRED", "message": "Valid API key is required." }`
*   **403 Forbidden:** The authenticated client does not have permission to perform the requested action on the resource.
    *   Example: `{ "error_code": "PERMISSION_DENIED", "message": "You are not authorized to delete this Minion." }`
*   **404 Not Found:** The requested resource (e.g., Minion, Task, Channel) does not exist.
    *   Example: `{ "error_code": "RESOURCE_NOT_FOUND", "message": "Minion with ID 'xyz' not found." }`
*   **422 Unprocessable Entity:** The request was well-formed but semantically incorrect (e.g., trying to start an already completed task).
    *   Example: `{ "error_code": "INVALID_STATE_TRANSITION", "message": "Cannot cancel a task that is already completed." }`
*   **500 Internal Server Error:** An unexpected error occurred on the server. This indicates a bug or unhandled exception in the backend.
    *   Example: `{ "error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred. Please try again later." }`
*   **503 Service Unavailable:** The server is temporarily unable to handle the request (e.g., during maintenance or overload).
    *   Example: `{ "error_code": "SERVICE_UNAVAILABLE", "message": "The service is temporarily unavailable. Please try again in a few minutes." }`

## 9. Future Considerations (Post-V1)

*   **Advanced Authorization:** Role-based access control (RBAC).
*   **gRPC Exploration:** For performance-critical paths or more complex streaming scenarios.
*   **Event Sourcing:** For auditing and replaying Minion/Task state changes.
*   **API Versioning Strategy:** More robust URL or header-based versioning.
*   **Rate Limiting:** To prevent abuse.
*   **Internationalization (i18n)** for error messages.
*   **Webhooks:** For backend to notify external systems of events.