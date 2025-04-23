import subprocess
from typing import List, Dict, Any
from webscout.Provider import *
from AGENTS.functioncall import FunctionCallingAgent, Fn
import inspect
from rich import print as rprint
from dataset import DatasetBuilder
from EXTRA.conversation import JARVISConversation
from TOOL.main import ask_website, check_internet_speed, get_news, process_pdf, websearch # Import the tools
from config.config import Config

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

functions: List[Fn] = []
local_vars: Dict[str, Any] = locals().copy() #Copy the local vars
for name, obj in local_vars.items():
    if callable(obj) and hasattr(obj, '_is_tool'):
        sig = inspect.signature(obj)
        parameters = {param.name: "string" if param.annotation is inspect._empty else str(param.annotation).replace("<class '","").replace("'>","") for param in sig.parameters.values()}
        
        docstring = obj.__doc__ if obj.__doc__ else " "
        
        functions.append(Fn(name=name, description=docstring, parameters=parameters))

class JARVIS:
    def __init__(self):
        self.dataset_builder = DatasetBuilder(filepath=Config.DATASET_FILE)  # Initialize DatasetBuilder
        self.conversation = JARVISConversation()  # Initialize JARVISConversation
        self.agent = FunctionCallingAgent(tools=functions) #pass the list of tools to the agent class
        self.ai = C4ai(
            is_conversation=False,
            system_prompt=self.conversation.intro
        )


    def execute_tool_and_respond(self, user_input: str) -> None:
        """
        Executes a tool based on user input using the FunctionCallingAgent and provides a response.
        """
        #add history to the chat
        try:
            # rprint(f"User Input: {user_input}")
            
            self.conversation._add_message("User", user_input) # Use conversation class to add message
            
            function_call_data = self.agent.function_call_handler(user_input)
            
            if "error" in function_call_data:
                error_message = f"I've encountered an error: {function_call_data['error']}"
                rprint(f"[bold red]JARVIS:[/] {error_message}")
                self.conversation._add_message("JARVIS", error_message) # Add error to conversation history
                return
            
            tool_calls = function_call_data.get("tool_calls", [])
            tool_outputs = []
            
            for tool_call in tool_calls:
                function_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})
                
                if not function_name:
                    rprint("[bold red]JARVIS: Tool name not found in the tool call data.[/]")
                    return
                
                if hasattr(self, function_name):
                    try:
                         function_to_call = getattr(self, function_name)
                         tool_output = function_to_call(**arguments) # Execute the function
                         tool_outputs.append({"name": function_name, "output": tool_output, "arguments": arguments})
                         rprint(f"[bold blue]Tool:[/] Executed tool '{function_name}'")
                         self.conversation._add_message("Tool" + function_name, f"Executed with output: {tool_output}") # Add tool output to conversation history
                         
                    except Exception as e:
                        rprint(f"[bold red]JARVIS:[/] Error executing tool '{function_name}': {e}")
                        tool_outputs.append({"name": function_name, "output": f"Error: {e}", "arguments": arguments})
                        self.conversation._add_message(function_name, f"Error: {e}") # Add error to conversation history
                else:
                    rprint(f"[bold red]JARVIS:[/] Tool '{function_name}' not found in JARVIS class.")
                    tool_outputs.append({"name": function_name, "output": f"Tool not found", "arguments": arguments})
                    self.conversation._add_message("JARVIS", f"Tool not found: {function_name}") # Add error to conversation history
                    
            # Generate a response using the LLM
            
            if tool_outputs:
                ai_prompt = f"""
                You are JARVIS, a helpful AI assistant. You have access to tools, and a user has just asked: '{user_input}'.

                Here are the results from using the specified tools:
                {tool_outputs}

                Your response: 
                """
                ai_prompt = self.conversation.gen_complete_prompt(ai_prompt) # Use conversation history for prompt
                llm_response = "".join(self.ai.chat(ai_prompt))
                rprint(f"[bold green]JARVIS:[/] {llm_response}")
                self.conversation._add_message("JARVIS", llm_response) # Add LLM response to conversation history

                # Add datapoint to the dataset
                self.dataset_builder.add_datapoint(
                    user_input=user_input,
                    tool_calls=tool_outputs,
                    response=llm_response
                )
            else:
               rprint("[bold red]JARVIS: No valid tool outputs to construct an AI response.[/]")
               self.conversation._add_message("JARVIS", "No valid tool outputs.") # Add to conversation history
        except Exception as e:
            rprint(f"[bold red]An unexpected error occurred: {e}[/]")
            self.conversation._add_message("JARVIS", f"An unexpected error occurred: {e}") # Add error to conversation history
########################################
# Tool Wrappers
########################################
    def ask_website(self, url: str, **kwargs) -> str:
        """Wrapper for ask_website tool with error handling."""
        try:
            # Pass the URL as positional argument and everything else as keyword arguments
            return ask_website(url, **kwargs)
        except Exception as e:
            rprint(f"[bold red]JARVIS:[/] Error using ask_website: {e}")
            return f"Error using ask_website: {e}"

    def check_internet_speed(self) -> str:
         """Wrapper for check_internet_speed tool with error handling."""
         try:
            return check_internet_speed()
         except Exception as e:
            rprint(f"[bold red]JARVIS:[/] Error using check_internet_speed: {e}")
            return f"Error using check_internet_speed: {e}"

    def get_news(self, topic: str, max_results: int = 3) -> str:
         """Wrapper for get_news tool with error handling."""
         try:
            return get_news(topic, max_results)
         except Exception as e:
            rprint(f"[bold red]JARVIS:[/] Error using get_news: {e}")
            return f"Error using get_news: {e}"
    
    def websearch(self, query: str, timeout: int = 30, stream: bool = False) -> str:
         """Wrapper for websearch tool with error handling."""
         try:
            return websearch(query, timeout, stream)
         except Exception as e:
            rprint(f"[bold red]JARVIS:[/] Error using websearch: {e}")
            return f"Error using websearch: {e}"
         
    def process_pdf(self, input_path: str, output_mode: str = 'both', output_path: str = None, show_page_breaks: bool = True) -> str:
          """Wrapper for the process_pdf tool with error handling."""
          try:
             return process_pdf(input_path, output_mode, output_path, show_page_breaks)
          except Exception as e:
              rprint(f"[bold red]JARVIS:[/] Error using process_pdf: {e}")
              return f"Error using process_pdf: {e}"
              
    def general_ai(self, question: str) -> str:
        return question
######################################################
# Main function to run the JARVIS assistant          #
######################################################
def main():
    jarvis = JARVIS()
    try:
        while True:
            user_input = input(">>> ").strip()
            if user_input.lower() in ["exit", "quit", "bye"]:
                rprint("[bold green]JARVIS:[/] Exiting...")
                break
            if user_input:
                jarvis.execute_tool_and_respond(user_input)
    except KeyboardInterrupt:
        rprint("\n[bold green]JARVIS:[/] Exiting due to keyboard interrupt...")
    except Exception as e:
        rprint(f"[bold red]JARVIS:[/] An unexpected error occurred in main(): {e}")
    finally:
        subprocess.run("clear")
        pass

if __name__ == "__main__":
    main()