# Tool Integration Plan for ADK Minions (MCP & Native)  (1)

## 1. Introduction (3)

This document outlines the strategic approach for integrating essential operational tools into the Google Agent Development Kit (ADK) framework for "Operation Gemini Legion." It addresses the empowerment of Minion agents with capabilities for computer interaction, web automation, terminal command execution, and filesystem operations. This plan also details the strategy for GUI-configurable tool permissions, ensuring granular control over Minion abilities. The overarching goal is to provide Minions with robust, flexible, and secure access to the tools necessary to perform their diverse tasks. (9)

## 2. General ADK Tooling Approach & Philosophy (11)

The core philosophy for tool integration revolves around leveraging the ADK's native tool framework as the primary mechanism for exposing capabilities to Minions. This approach offers several advantages: (14)

*   **Standardization:** ADK provides a consistent way to define, register, and invoke tools, simplifying development and maintenance. (16)
*   **Flexibility:** The framework supports both Python-native tools and the integration of external MCP (Model Context Protocol) servers. (18)
*   **Security & Control:** ADK's structure is amenable to permission systems, allowing fine-grained control over which Minions can access specific tools. (20)

**Tool Definition and Registration:** (22)

New tools, whether Python-based or wrappers for MCP servers, will be defined as classes inheriting from ADK's base tool classes (e.g., `Tool` or more specialized variants). Key aspects of a tool definition include: (25)

*   **Name:** A unique identifier for the tool (this name will be used in the API for permissions). (27)
*   **Description:** A clear, LLM-understandable explanation of what the tool does, its inputs, and its outputs. This is crucial for the Minion to correctly decide when and how to use the tool. (29)
*   **Input Schema:** A structured definition (e.g., using Pydantic or JSON Schema) of the parameters the tool accepts. This enables validation and clear communication of requirements. (31)
*   **Execution Logic:** The actual Python code that performs the tool's action. For MCP wrappers, this logic would handle communication with the external MCP server. (33)

Tools will be registered with each Minion's `LlmAgent` instance, typically during initialization, making them available for the Minion to select and use based on its configured permissions. (36)

## 3. `ComputerUseMCP` Warnings and Legacy Context (38)

The `adk_minion_army/agents/minion_agent.py` script previously attempted to initialize a specific Node.js-based `ComputerUseMCP` found at `mcp_servers/computer_use_mcp/dist/index.js`. This MCP, while providing useful desktop automation capabilities (mouse, keyboard, screen analysis via `nut-js`), is now considered a legacy example rather than a core, default tool for all Minions. (43)

The warnings "ComputerUseMCP toolset not configured" arise if this specific script/directory is not found. (45)

**Resolution Plan:** (47)

To resolve these warnings and clarify the role of `ComputerUseMCP`: (49)

1.  **Modify `adk_minion_army/agents/minion_agent.py`:** (51)
    *   The default behavior should **not** be to automatically attempt to load this specific `ComputerUseMCP`. (53)
    *   Instead, Minions should be initialized with a core set of ADK-native or well-integrated Python-based tools (detailed in Section 4). (55)
    *   The logic for loading `ComputerUseMCP` can be retained but commented out or refactored into a conditional setup, perhaps triggered by a specific Minion configuration or role that explicitly requires its unique (Node.js/`nut-js`) capabilities. This makes it an optional, advanced tool rather than a default dependency. (58)
2.  **Documentation:** (60)
    *   Clearly document that the `mcp_servers/computer_use_mcp/` directory contains an *example* MCP server for advanced desktop automation. (62)
    *   Provide instructions on how to build (`npm run build` within its directory) and potentially run it if a developer or a specialized Minion profile needs its features. (64)
    *   Explain that for general Minion operations, the Python-based alternatives (see Section 4) are preferred for tighter integration and easier dependency management within the Python-centric ADK environment. (67)

This approach ensures that default Minion startup is not dependent on a Node.js environment or a specific pre-built script, while still acknowledging the `ComputerUseMCP` as a useful, albeit external, tool example. (70)

## 4. Tool Category Plans & Integration Methods (72)

This section details the strategy for providing Minions with key operational capabilities. The preference is for ADK-native features or Python libraries wrapped as ADK tools. (75)

### 4.1. Desktop GUI Interaction / Computer Use (77)

While the legacy `ComputerUseMCP` (using Node.js and `nut-js`) offers comprehensive capabilities, a Python-native approach is generally preferred for core Minion functionality. (80)

*   **Required Capabilities:** (82)
    *   Move mouse cursor to (x,y). (83)
    *   Perform mouse clicks (left, right, double). (84)
    *   Type text into fields. (85)
    *   Press keyboard keys and shortcuts. (86)
    *   Take screenshots (full screen, specific region). (87)
    *   (Advanced) Basic image recognition on screen (e.g., find template image). (88)
*   **Proposed Integration (Python-based ADK Tools):** (90)
    *   **`pyautogui`:** This library provides excellent cross-platform GUI automation capabilities (mouse, keyboard, screenshots). It can be wrapped into a set of ADK tools. (92)
        *   `desktop_move_mouse(x: int, y: int)` (93)
        *   `desktop_click(button: str = 'left', clicks: int = 1, x: int | None = None, y: int | None = None)` (94)
        *   `desktop_type_text(text: str, interval: float = 0.01)` (95)
        *   `desktop_press_key(keys: list[str] | str)` (96)
        *   `desktop_take_screenshot(filename: str | None = None, region: tuple[int,int,int,int] | None = None) -> str (path or base64)` (97)
    *   **`opencv-python` (for image recognition):** For more advanced screen analysis, `opencv` can be used in conjunction with screenshots taken by `pyautogui`. (99)
        *   `desktop_find_image_on_screen(template_image_path: str, confidence: float = 0.8) -> tuple[int,int,int,int] | None` (100)
    *   **ADK Native Tools (if/when available):** If future ADK versions provide direct, robust desktop interaction tools, those should be prioritized. (102)

### 4.2. Web Browser Automation (104)

Minions will often need to interact with web pages. (106)

*   **Required Capabilities:** (108)
    *   Navigate to a URL. (109)
    *   Click links and buttons. (110)
    *   Fill out forms. (111)
    *   Extract text or data from pages. (112)
    *   Take screenshots of web pages. (113)
    *   Execute JavaScript. (114)
*   **Proposed Integration (Python-based ADK Tools):** (116)
    *   **`selenium` or `playwright-python`:** Both are powerful browser automation libraries. `playwright-python` is more modern and often preferred for its robustness and API. These would be wrapped as ADK tools. (119)
        *   `browser_navigate(url: str)` (120)
        *   `browser_click(selector: str)` (121)
        *   `browser_fill_form(selector: str, text: str)` (122)
        *   `browser_get_text(selector: str) -> str` (123)
        *   `browser_get_html(selector: str | None = None) -> str` (124)
        *   `browser_take_screenshot(filename: str | None = None) -> str (path or base64)` (125)
        *   `browser_execute_script(script: str) -> Any` (126)
    *   **Playwright MCP Server:** The existing `playwright-mcp-server` (referenced in the initial environment context) is a viable option if direct Python wrapping is complex or if its pre-built MCP interface offers advantages. This can be integrated using ADK's `MCPToolset`. (130)

### 4.3. Terminal Command Execution (132)

Executing shell commands is a fundamental requirement. (134)

*   **Required Capabilities:** (136)
    *   Run arbitrary shell commands. (137)
    *   Capture stdout, stderr, and return codes. (138)
    *   Execute commands in a specified working directory. (139)
    *   Handle long-running commands (potentially). (140)
*   **Proposed Integration (Python-based ADK Tools):** (142)
    *   **`subprocess` module:** Python's built-in `subprocess` module is the standard way to run shell commands. (144)
        *   `terminal_run_command(command: str, cwd: str | None = None, timeout: int | None = None) -> dict[str, str | int]` (returning stdout, stderr, return_code) (145)
    *   **ADK Native `execute_command` (if aligned):** The `execute_command` tool available in some ADK environments (like the one Roo, the architect, uses) should be investigated for its suitability and potentially adopted or adapted for Minions if it meets security and functionality requirements. (148)

### 4.4. Filesystem Operations (150)

Minions will need to read, write, and manage files and directories. (152)

*   **Required Capabilities:** (154)
    *   Read file contents. (155)
    *   Write content to a file (create or overwrite). (156)
    *   Append content to a file. (157)
    *   List directory contents. (158)
    *   Check if a file or directory exists. (159)
    *   Create directories. (160)
    *   Delete files and directories (with safeguards). (161)
*   **Proposed Integration (Python-based ADK Tools):** (163)
    *   **`os` and `shutil` modules:** Python's standard libraries offer comprehensive filesystem operations. These would be wrapped into specific ADK tools like: (165)
        *   `fs_read_file(path: str) -> str` (166)
        *   `fs_write_file(path: str, content: str)` (167)
        *   `fs_append_file(path: str, content: str)` (168)
        *   `fs_list_directory(path: str, recursive: bool = False) -> list[str]` (169)
        *   `fs_path_exists(path: str) -> bool` (170)
        *   `fs_create_directory(path: str, exist_ok: bool = True)` (171)
        *   `fs_delete_path(path: str)` (This tool would require careful permissioning and confirmation mechanisms). (172)
    *   **ADK Native File Tools:** Many ADK environments (like Roo's current one) come with pre-defined tools such as `read_file`, `write_to_file`, `list_files`, `apply_diff`, `insert_content`. These should be the **primary choice** for Minions due to their tight integration and existing testing within the ADK ecosystem, assuming they are available and provide the necessary granularity. The Python wrappers above would be considered if these native tools are insufficient or not available in a specific Minion's ADK context. (178)

## 5. GUI-Configurable Tool Permissions Management (180)

Effective operation of a Minion army requires granular control over the tools each Minion can access. This will be managed via the Legion Commander GUI, interacting with backend APIs as defined in [`docs/master_plan/01_API_CONTRACT_V1.md`](docs/master_plan/01_API_CONTRACT_V1.md:0). (183)

**Strategy:** (185)

1.  **Storage and Structure (as per API Contract V1):** (187)
    *   Tool permissions for each Minion are stored as part of its configuration. (189)
    *   The Minion's configuration, retrievable via `GET /api/v1/minions/{minion_id}` (API Contract Section 4.2), includes a `tools` array. (191)
    *   Each element in this array is an object specifying the tool's `name` (string) and its `enabled` status (boolean). (193)
        ```json
        // Example from API Contract (Section 4.2 Get Minion Details -> tools property)
        "tools": [
          { "name": "fs_read_file", "description": "Reads file contents", "enabled": true },
          { "name": "terminal_run_command", "description": "Runs shell commands", "enabled": false }
          // ... other tools
        ]
        ``` (201)
    *   When updating, the `PUT /api/v1/minions/{minion_id}/config` endpoint (API Contract Section 4.5) accepts a similar `tools` array in its request payload to set the desired state for each tool. The contract notes: "Only tools present in this list will be considered; tools not listed might be disabled or retain their current state based on backend logic (clarify)." This backend logic for unlisted tools needs to be clearly defined (e.g., are unlisted tools implicitly disabled, or does the PUT require a complete list of all known tools and their states?). For simplicity and explicitness, providing a complete list of known tools and their intended `enabled` state is recommended for `PUT` operations. (207)

2.  **API Endpoints (from API Contract V1):** (209)
    *   **Retrieve Current Permissions:** The Legion Commander GUI will use `GET /api/v1/minions/{minion_id}` to fetch a specific Minion's details, which includes the `tools` array detailing each tool's name, description (if provided by backend), and current `enabled` status. (212)
    *   **Update Permissions:** The GUI will use `PUT /api/v1/minions/{minion_id}/config` to update a Minion's configuration. The payload will include the `tools` array, where each entry specifies a tool `name` and its new `enabled` (true/false) state. (215)

3.  **Legion Commander GUI Interaction:** (217)
    *   **Displaying Tools:** (219)
        *   The API contract (`01_API_CONTRACT_V1.md`) does not explicitly define an endpoint like `GET /api/v1/tools/available` to list all possible tools in the system. (221)
        *   **Recommendation:** The backend should provide a mechanism for the GUI to discover all valid tool names and their descriptions. This could be a new endpoint (e.g., `GET /api/v1/system/tool_definitions`) or the GUI might infer the set of all possible tools by aggregating the `tools` arrays from all Minions and/or having a pre-defined list. A dedicated endpoint is preferable for clarity and dynamic updates if new tools are added to the system globally. (225)
        *   Assuming such a list is available, the GUI will display all known tools. (226)
    *   **Managing Permissions for a Minion:** (228)
        *   When an administrator selects a Minion, the GUI fetches its current tool configuration via `GET /api/v1/minions/{minion_id}`. (230)
        *   The GUI will then display each tool (from the global list) and indicate whether it's currently `enabled` or `disabled` for that specific Minion, likely using checkboxes or toggles. (232)
        *   The administrator can modify these `enabled` states. (233)
        *   Upon saving, the GUI constructs the `tools` array (containing all known tools and their desired `enabled` states for that Minion) and sends it via `PUT /api/v1/minions/{minion_id}/config`. (235)

4.  **Minion Enforcement:** (237)
    *   When a Minion agent initializes or its configuration is updated, it will receive/load its list of enabled tools as per the `tools` array in its configuration. (239)
    *   The Minion's `LlmAgent` (or a dedicated internal tool/permission manager) will only register and make available the tools explicitly marked as `enabled: true`. (241)
    *   If the Minion's LLM attempts to generate a call for a tool that is not in its list of enabled tools, the agent's internal logic should prevent the tool call from being dispatched, effectively enforcing the configured permissions. (244)

This strategy, leveraging the defined API endpoints, allows for clear and manageable tool permissions configurable via the Legion Commander GUI. The point regarding the discovery of all available tools by the GUI should be clarified or addressed with a dedicated API endpoint. (248)

## 6. Conclusion (250)

This plan provides a roadmap for empowering ADK Minions with a comprehensive and controllable set of operational tools. By prioritizing ADK-native integration and Python-based solutions, while retaining the flexibility to incorporate external MCPs where beneficial, "Operation Gemini Legion" can ensure its Minions are well-equipped for their diverse and critical tasks. The successful implementation of GUI-configurable permissions, guided by the `01_API_CONTRACT_V1.md`, will be key to maintaining security and operational control. (256)