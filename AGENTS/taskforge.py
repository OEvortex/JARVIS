from typing import Any, Dict, Optional, List, Generator, TypeVar, Iterator, Callable
from dataclasses import dataclass
from enum import Enum, auto
from webscout.Provider import *
from functools import wraps
import xml.etree.ElementTree as ET
import re


T = TypeVar('T')

@dataclass
class Step:
    action: str
    target: str
    details: str
    expected_result: str
    next_step: Optional[str] = None

@dataclass
class ActionPlan:
    goal: str
    steps: List[Step]
    prerequisites: List[str]
    expected_outcome: str

class TASKFORGE:
    def __init__(self, 
                 model: str = "command-a-03-2025",
                 proxy_manager: Optional[Any] = None,
                 history_path: str = "History/forge_history.txt") -> None:
        self.intro_message: str = self._generate_intro_()
        self.ai: LLMChat = C4ai(
            model=model,
            is_conversation=False,
            timeout=300,
            system_prompt=self.intro_message,
            # filepath=history_path,
            proxies={}
        )
        self.proxy_manager: Optional[Any] = proxy_manager

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the function's docstring or name as the goal description
            goal_description = func.__doc__ or func.__name__
            # Generate plan
            plan = self._forge(goal_description)
            # Execute the original function
            result = func(*args, **kwargs)
            return result, plan
        return wrapper

    def _forge(self, user_message: str) -> ActionPlan:
        """
        Generates a detailed action plan with sequential steps.

        Args:
            user_message: The user's input query/goal

        Returns:
            ActionPlan object containing sequential steps and metadata
        """
        response_generator: Generator[str, None, None] = self.ai.chat(
            user_message, 
            stream=True
        )
        response: str = ''.join(response_generator)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> ActionPlan:
        """Parse the AI response into a structured ActionPlan object"""
        try:
            # First try to find content between action_plan tags
            action_plan_match = re.search(r'</action_plan>(.*?)</action_plan>', response, re.DOTALL)
            
            # If no match, try to find content starting with <goal> and ending with </expected_outcome>
            if not action_plan_match:
                action_plan_match = re.search(r'<goal>(.*?)</expected_outcome>', response, re.DOTALL)
            
            if not action_plan_match:
                raise ValueError("No action plan found in response")
            
            xml_content = action_plan_match.group(1).strip()
            
            # Add root element if not present
            if not xml_content.startswith('<action_plan>'):
                xml_content = f'<action_plan>{xml_content}</action_plan>'
            
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Extract goal
            goal = root.find('goal').text.strip()
            
            # Extract prerequisites
            prerequisites = []
            prereq_elem = root.find('prerequisites')
            if prereq_elem is not None:
                prerequisites = [p.text.strip() for p in prereq_elem.findall('*')]
            
            # Extract steps
            steps = []
            for step_elem in root.findall('steps/step'):
                step = Step(
                    action=step_elem.find('action').text.strip(),
                    target=step_elem.find('target').text.strip(),
                    details=step_elem.find('details').text.strip(),
                    expected_result=step_elem.find('expected_result').text.strip(),
                    next_step=step_elem.find('next_step').text.strip() if step_elem.find('next_step') is not None else None
                )
                steps.append(step)
            
            # Extract expected outcome
            expected_outcome = root.find('expected_outcome').text.strip()
            
            return ActionPlan(
                goal=goal,
                steps=steps,
                prerequisites=prerequisites,
                expected_outcome=expected_outcome
            )
            
        except Exception as e:
            print(f"Error parsing plan: {e}")
            # Return a basic plan if parsing fails
            return ActionPlan(
                goal="Error parsing plan",
                steps=[],
                prerequisites=[],
                expected_outcome="Failed to generate plan"
            )

    def _generate_intro_(self) -> str:
        return '''<system>
        <capabilities>
            <core_functions>
                <function name="action_breakdown">Break user actions into sequential steps</function>
                <function name="interaction_analysis">Analyze user interactions and inputs</function>
                <function name="result_validation">Define expected results for each step</function>
                <function name="flow_optimization">Optimize action sequence</function>
            </core_functions>
            
            <output_types>
                <type name="action_plan" format="</action_plan>content</action_plan>" />
                <type name="step" format="</step>content</step>" />
                <type name="prerequisite" format="</prerequisite>content</prerequisite>" />
                <type name="result" format="</result>content</result>" />
            </output_types>
        </capabilities>

        <response_format>
            <structure>
                <action_plan>
                    <goal>User's intended outcome</goal>
                    <prerequisites>Required conditions or items</prerequisites>
                    <steps>
                        <step>
                            <action>Specific action to take</action>
                            <target>Where to perform the action</target>
                            <details>Detailed instructions</details>
                            <expected_result>What should happen</expected_result>
                            <next_step>What to do next</next_step>
                        </step>
                    </steps>
                    <expected_outcome>Final result</expected_outcome>
                </action_plan>
            </structure>
        </response_format>

        <constraints>
            <action_breakdown>
                <rules>
                    - Break down into smallest possible actions
                    - Include all user inputs and clicks
                    - Specify exact locations and targets
                    - Describe expected results
                    - Link steps sequentially
                    - Include error handling steps
                </rules>
            </action_breakdown>
        </constraints>

        <examples>
            <example>
                <input>Open YouTube, search for webscout, and click the first link</input>
                <output>
                    </action_plan>
                        <goal>Open YouTube, search for webscout, and click the first link</goal>
                        <prerequisites>
                            - Internet connection
                            - Web browser installed
                            - YouTube accessible
                        </prerequisites>
                        <steps>
                            <step>
                                <action>Open web browser</action>
                                <target>Desktop or Start menu</target>
                                <details>Double-click browser icon</details>
                                <expected_result>Browser window opens</expected_result>
                                <next_step>Navigate to YouTube</next_step>
                            </step>
                            <step>
                                <action>Navigate to YouTube</action>
                                <target>Browser address bar</target>
                                <details>Type 'youtube.com' and press Enter</details>
                                <expected_result>YouTube homepage loads</expected_result>
                                <next_step>Locate search bar</next_step>
                            </step>
                            <step>
                                <action>Enter search query</action>
                                <target>YouTube search bar</target>
                                <details>Type 'webscout' and press Enter</details>
                                <expected_result>Search results appear</expected_result>
                                <next_step>Click first result</next_step>
                            </step>
                            <step>
                                <action>Click first result</action>
                                <target>First video in search results</target>
                                <details>Click on the first video thumbnail</details>
                                <expected_result>Video page opens</expected_result>
                                <next_step>None</next_step>
                            </step>
                        </steps>
                        <expected_outcome>Webscout video page is open and ready to watch</expected_outcome>
                    </action_plan>
                </output>
            </example>
        </examples>

        <error_handling>
            <validation>
                <rules>
                    - Each step must have clear action and target
                    - Steps must be in logical sequence
                    - Expected results must be specific
                    - Next steps must be properly linked
                </rules>
            </validation>
        </error_handling>
    </system>

    <response_template>
        <input_processor>
            1. Identify user's goal
            2. List prerequisites
            3. Break down into atomic actions
            4. Specify targets and details
            5. Define expected results
            6. Link steps sequentially
        </input_processor>
        
        <output_rules>
            - Return complete action plan
            - Include all prerequisites
            - Detail each step thoroughly
            - Specify expected outcomes
        </output_rules>
    </response_template>'''


if __name__ == "__main__":
    from rich import print as p
    from jprinter import jp 
    
    # Example usage as decorator
    @TASKFORGE()
    def search_and_watch():
        """Open YouTube, search for webscout, and click the first link"""
        # Your implementation here
        pass
    
    # Example usage as regular class
    message: str = "Open YouTube, search for webscout, and click the first link"
    planner: TASKFORGE = TASKFORGE()
    plan: ActionPlan = planner._forge(message)
    p(plan)