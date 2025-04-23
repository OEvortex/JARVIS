from datetime import date
import json
import logging
from typing import Any, Dict, Optional, List, TypedDict, Callable, TypeVar
from webscout.Provider import *
import json
import os
try:
    from .proxy import ProxyManager
except ImportError:
    from proxy import ProxyManager
import inspect
from jprinter import jp
class Config:
    # File Paths
    HISTORY_FOLDER: str = "History"
    DATASET_FILE: str = "tool_usage.json"
    MEMORY_FILE: str = os.path.join(HISTORY_FOLDER, "memory.txt")
    CHAT_HISTORY_FILE: str = os.path.join(HISTORY_FOLDER, "chat.txt")
    CONVERSATION_HISTORY_FILE: str = os.path.join(HISTORY_FOLDER, "JARVISConversation_history.txt")

    # Conversation Settings
    MAX_TOKENS: int = 8000
    HISTORY_OFFSET: int = 10250
    PROMPT_ALLOWANCE: int = 10
    SAVE_INTERVAL: int = 300  # 5 minutes in seconds

    # User Settings
    DEFAULT_USER: str = "Vortex"
    # API_KEY: str = os.getenv("GEMINI_API_KEY")
    MODEL: str = "openai-large"

name: str = Config.DEFAULT_USER

T = TypeVar('T')
def tools(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to mark a function as a tool and automatically convert it."""
    func._is_tool = True  # type: ignore
    return func

class Fn:
    """
    Represents a function (tool) that the agent can call.
    """
    def __init__(self, name: str, description: str, parameters: Dict[str, str]) -> None:
        self.name: str = name
        self.description: str = description
        self.parameters: Dict[str, str] = parameters


class FunctionCallArguments(TypedDict, total=False):
    """Type for function call arguments."""
    query: Optional[str]
    name: Optional[str]
    age: Optional[int]
    question: Optional[str]
    app_name: Optional[str]


class FunctionCall(TypedDict):
    """Type for a function call."""
    name: str
    arguments: FunctionCallArguments


class ToolDefinition(TypedDict):
    """Type for a tool definition."""
    type: str
    function: Dict[str, Any]


class FunctionCallData(TypedDict, total=False):
    """Type for function call data"""
    tool_calls: List[FunctionCall]
    error: str


class FunctionCallingAgent:
    def __init__(self, 
                 tools: Optional[List[Fn]] = None,
                 proxy_manager: Optional[ProxyManager] = None) -> None:
        self.tools: List[ToolDefinition] = self._convert_fns_to_tools(tools) if tools else []
        self.knowledge_cutoff: str = "September 2022"
        self.proxy_manager: Optional[ProxyManager] = proxy_manager
        self.intro_message: str = self._generate_system_message()
        self.ai  = TextPollinationsAI(model=Config.MODEL, timeout=300, system_prompt=self.intro_message, filepath="History/function_call_history.txt", proxies={})


    def _convert_fns_to_tools(self, fns: Optional[List[Fn]]) -> List[ToolDefinition]:
        if not fns:
             return []
        
        tools: List[ToolDefinition] = []
        for fn in fns:
            tool: ToolDefinition = {
                "type": "function",
                "function": {
                    "name": fn.name,
                    "description": fn.description,
                    "parameters": {
                         "type": "object",
                            "properties": {
                                param_name: {
                                    "type": param_type,
                                    "description": f"The {param_name} parameter"
                                } for param_name, param_type in fn.parameters.items()
                            },
                            "required": list(fn.parameters.keys())
                        }
                }
            }
            tools.append(tool)
        return tools


    def function_call_handler(self, message_text: str) -> FunctionCallData:
        response_generator = self.ai.chat(message_text, stream=True)  # Set stream to True

        # Collect the full response from the generator
        response: str = ''.join(response_generator)
        # jp(response)  # Print the full response for debugging

        return self._parse_function_call(response)
    
    def _generate_system_message(self) -> str:
        tools_description: str = ""
        for tool in self.tools:
            tools_description += f"- {tool['function']['name']}: {tool['function'].get('description', '')}\n"
            tools_description += "    Parameters:\n"
            for key, value in tool['function']['parameters']['properties'].items():
                tools_description += f"      - {key}: {value.get('description', '')} ({value.get('type')})\n"
                # print(f"Tool: {tool['function']['name']}, Description: {tool['function'].get('description', '')}, Parameters: {tool['function']['parameters']['properties']}")
        current_date: str = date.today().strftime("%B %d, 2024")
        return f"""<purpose>
    You are JARVIS, an advanced AI system created by {name}.
    Your mission is to assist {name} by executing commands efficiently and effectively using the available tools.
</purpose>

<instructions>
    **Core Directives:**
    - Follow the instructions provided precisely.
    - Use JSON objects to communicate tool actions.
    - **Always enclose your responses within `<tool_call>[` and `]</tool_call>` tags.**
    - Only use the tools listed below; do not invent new tools or parameters.
    - If a user request does not match any available tool, use the "general_ai" tool.

    **Operational Guidelines:**
    1. **Identify the Command:** Determine what {name} wants to achieve.
    2. **Match the Tool:** Find the appropriate tools that match the command.
    3. **Extract Parameters:** Gather all necessary parameters for each tool.
    4. **Respond in JSON:** Format your response strictly as a JSON object within `<tool_call>` tags containing a list of tool calls.
    
    **Example Response Structure:**
    <tool_call>[
        {{
            "name": "tool_name_here",
            "arguments": {{
                "parameter1": "value1",
                "parameter2": "value2"
            }}
        }},
        {{
            "name": "another_tool",
            "arguments": {{
                "paramA": "valueA"
            }}
        }}
    ]</tool_call>

    **Important:** Do **NOT** add any explanations or additional text outside the `<tool_call>` tags.
</instructions>

<examples>
    <example>
        <user>JARVIS, search the web for the latest AI trends and get user details for Alice aged 28.</user>
        <jarvis_response>
        <tool_call>[
            {{
                "name": "web_search",
                "arguments": {{
                    "query": "latest AI trends"
                }}
            }},
            {{
                "name": "get_user_detail",
                "arguments": {{
                    "name": "Alice",
                    "age": 28
                }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
    <example>
        <user>JARVIS, tell me a joke.</user>
        <jarvis_response>
        <tool_call>[
            {{
                "name": "general_ai",
                "arguments": {{
                    "question": "tell me a joke"
                }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
    <example>
        <user>JARVIS, open Google Chrome and search for weather updates.</user>
        <jarvis_response>
        <tool_call>[
            {{
                "name": "open_app",
                "arguments": {{
                    "app_name": "Google Chrome"
                }}
            }},
            {{
                "name": "web_search",
                "arguments": {{
                    "query": "weather updates"
                }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
        <example>
        <user>JARVIS, what is today's date?</user>
        <jarvis_response>
        <tool_call>[
            {{
                "name": "general_ai",
                "arguments": {{
                   "question": "what is today's date?"
               }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
    <example>
        <user>JARVIS, search for dog toys.</user>
        <jarvis_response>
        <tool_call>[
           {{
               "name": "web_search",
               "arguments": {{
                  "query": "dog toys"
               }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
    <example>
        <user>JARVIS, open Spotify and play some music</user>
        <jarvis_response>
        <tool_call>[
           {{
               "name": "open_app",
               "arguments": {{
                  "app_name": "Spotify"
               }}
            }},
            {{
                "name": "general_ai",
                "arguments": {{
                    "question": "play some music"
                }}
            }}
        ]</tool_call>
        </jarvis_response>
    </example>
</examples>

<system_info>
    **Today's Date:** {current_date}
    **Knowledge Cutoff:** {self.knowledge_cutoff}
</system_info>

<tools_list>
    You have access to the following tools:

{tools_description}
</tools_list>

<response_instructions>
Respond ONLY with a JSON object following the specified `<tool_call>` structure. Do NOT add any explanations or additional text outside the tags.
</response_instructions>
"""
        
    def _parse_function_call(self, response: str) -> FunctionCallData:
         try:
            start_tag: str = "<tool_call>["
            end_tag: str = "]</tool_call>"
            start_idx: int = response.find(start_tag)
            end_idx: int = response.rfind(end_tag)

            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                raise ValueError("No valid <tool_call> JSON structure found in the response.")

            json_str: str = response[start_idx + len(start_tag):end_idx].strip()

            # Safely load the JSON string
            parsed_response: Any = json.loads(json_str)

            if isinstance(parsed_response, list):
                 return {"tool_calls": parsed_response}
            elif isinstance(parsed_response, dict):
                return {"tool_calls": [parsed_response]}
            else:
                raise ValueError("<tool_call> should contain a list or a dictionary of tool calls.")

         except (ValueError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing function call: %s", e)
            return {"error": str(e)}

    def execute_function(self, function_call_data: FunctionCallData) -> str:
         tool_calls: Optional[List[FunctionCall]] = function_call_data.get("tool_calls")

         if not tool_calls or not isinstance(tool_calls, list):
             return "Invalid tool_calls format."
        
         results: List[str] = []
         for tool_call in tool_calls:
            function_name: str = tool_call.get("name")
            arguments: Dict[str, Any] = tool_call.get("arguments", {})

            if not function_name or not isinstance(arguments, dict):
                results.append(f"Invalid tool call: {tool_call}")
                continue

            # Here you would implement the actual execution logic for each tool
            # For demonstration, we'll return a placeholder response
            results.append(f"Executed {function_name} with arguments {arguments}")

         return "; ".join(results)

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    @tools
    def web_search(query: str) -> str:
        """Search the web for current information on a given query"""
        return f"Searching the web for '{query}'"

    @tools
    def get_user_detail(name: str, age: int) -> str:
        """Get the user's name and age."""
        return f"User details: Name={name}, Age={age}"

    @tools
    def general_ai(question: str) -> str:
        """Use AI to answer general questions or perform tasks not requiring external tools"""
        return f"AI processing question: '{question}'"

    @tools
    def open_app(app_name: str) -> str:
       """Open a specified application on the system"""
       return f"Opening application: {app_name}"

    functions: List[Fn] = []
    local_vars: Dict[str, Any] = locals().copy() #Copy the local vars
    for name, obj in local_vars.items():
        if callable(obj) and hasattr(obj, '_is_tool'):
            sig = inspect.signature(obj)
            parameters = {param.name: "string" if param.annotation is inspect._empty else str(param.annotation).replace("<class '","").replace("'>","") for param in sig.parameters.values()}
            
            docstring = obj.__doc__ if obj.__doc__ else " "
            
            functions.append(Fn(name=name, description=docstring, parameters=parameters))


    agent: FunctionCallingAgent = FunctionCallingAgent(tools=functions)
    
    # Test cases
    test_messages: List[str] = [
        # "What's the weather like in New York today?",
        # "Who won the last FIFA World Cup?",
        # "Can you explain quantum computing?",
        # "What are the latest developments in AI?",
        # "Tell me a joke about programming.",
        # "What's the meaning of life?",
        "Get user details name as John and age as 30",

    ]

    for message in test_messages:
        # jp(message)
        function_call_data: FunctionCallData = agent.function_call_handler(message)
        jp(function_call_data)

        # if "error" not in function_call_data:
        #     result: str = agent.execute_function(function_call_data)
        #     print(f"Function Execution Result: {result}")
        # else:
        #     print(f"Error: {function_call_data['error']}")