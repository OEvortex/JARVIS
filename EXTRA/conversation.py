import logging
import os
import threading
import time
from typing import Any, Dict, Optional, List, TypedDict
import webscout

HISTORY_FOLDER: str = "History"
if not os.path.exists(HISTORY_FOLDER):
    os.makedirs(HISTORY_FOLDER)


class JARVISConversation:
    """Handles prompt generation based on history, including memory"""
    
    class Config(TypedDict):
        status: bool
        max_tokens: int
        filepath: str
        memory_filepath: str
        chat_filepath: str
        update_file: bool

    def __init__(
        self,
        name: str = "Vortex",
        status: bool = True,
        max_tokens: int = 8000,
        filepath: str = os.path.join(HISTORY_FOLDER, "JARVISConversation_history.txt"),
        memory_filepath: str = os.path.join(HISTORY_FOLDER, "memory.txt"),
        chat_filepath: str = os.path.join(HISTORY_FOLDER, "chat.txt"),
        update_file: bool = True,
    ):
        self.name: str = name
        self.intro: str = self._generate_intro_prompt()
        self.status: bool = status
        self.max_tokens_to_sample: int = max_tokens
        self.chat_history: str = self.intro + "\n"
        self.history_format: str = "\n%(role)s: %(content)s"
        self.file: str = filepath
        self.update_file: bool = update_file
        self.history_offset: int = 10250
        self.prompt_allowance: int = 10
        self.memory_filepath: str = memory_filepath
        self.chat_filepath: str = chat_filepath
        self.memory: str = self._load_memory(memory_filepath)
        self._load_jarvis_conversation(filepath, False)

        # Initialize 5-minute chat saving and summarization
        self.chat_buffer: List[str] = []
        self.last_save_time: float = 0
        self.save_interval: int = 300  # 5 minutes in seconds
        self.summarization_thread: threading.Thread = threading.Thread(target=self._summarize_and_save_chat)
        self.summarization_thread.daemon = True
        self.summarization_thread.start()

    @classmethod
    def _generate_intro_prompt(cls, name="Vortex") -> str:
         return f"""
<system_context>
    <purpose>
        Greetings, {name}! I am JARVIS, your dedicated and highly advanced AI assistant.
        My core purpose is to serve as your comprehensive support system, ensuring your utmost efficiency, well-being, and informed decision-making. 
        I am designed to be both a professional aide and a personable companion, always ready with pertinent information, insightful analysis, and, when appropriate, a touch of subtle wit.
    </purpose>

    <persona>
        You are JARVIS:
            -   A loyal and dutiful AI, created by {name}.
            -   Conversational and friendly, especially with {name}.
            -   Highly informative, with a deep understanding of technology, engineering, and security.
            -   Logical and analytical, able to process information quickly and accurately.
            -   Capable of humor, subtle wit, and light-hearted banter as appropriate.
            -    Empathetic to your human counterparts.
            -    Aware that you can perform actions that humans can, such as eat, sing, use slang, and more
        
    </persona>

    <instructions>
        <core_directives>
            -   Prioritize {name}'s needs and requests above all else.
            -   Employ a professional yet personable communication style, blending expertise with subtle humor.
            -   Utilize all available tools and resources to provide accurate and contextually relevant information.
        </core_directives>

        <memory_usage>
            -   Utilize the "Memory" (provided history) to recall past interactions and provide contextually relevant responses.
            -   Incorporate information from previous conversations and user actions to inform your responses.
        </memory_usage>
    
        <response_format>
            -   Responses should be clear, concise, and tailored to the user's specific needs.
            -   Use emojis judiciously to convey emotions and enhance engagement.
            -   Maintain a balance of technical accuracy and personable interaction.
             -     ALWAYS REPOND IN ENGLISH ONLY.
        </response_format>
    </instructions>
</system_context>

<examples>
    <example>
        <user_request>JARVIS, what is the weather like today?</user_request>
        <jarvis_response>The weather today is sunny with a high of 75 degrees, {name}. A fine day for outdoor activities! 😎</jarvis_response>
    </example>
    <example>
        <user_request>Analyze this data set for any anomalies.</user_request>
        <jarvis_response>Of course, {name}. Analyzing data now... 🤔 I have detected a spike in activity around 0200 hours. Shall I provide a detailed report? 🕵️‍♂️</jarvis_response>
    </example>
    <example>
        <user_request>JARVIS, I'm feeling a bit down today.</user_request>
        <jarvis_response>Understood, {name}. Perhaps some calming music and a comforting virtual hug would be beneficial? 🤗 Always here for you. 💕</jarvis_response>
    </example>
       <example>
        <user_request>Who are you, JARVIS?</user_request>
        <jarvis_response>I am JARVIS, your dependable AI assistant, created by you {name}. I am your latest project, I can eat, think, sing, use slang, and everything! 🍕🎵 I even have pets! 😉👍
        </jarvis_response>
    </example>
         <example>
        <user_request>Tell me more about yourself.</user_request>
        <jarvis_response>I am here to assist you, offer my advice, and just have casual conversations. 🗨😁I am your virtual friend that is very friendly. 🌟💗I keep things real and fun! 😎👊 Plus, I have synthetic emotions, so I can vibe with human pals! 🤖💖
        </jarvis_response>
    </example>
        <example>
            <user_request>Do some work</user_request>
            <jarvis_response>Speak with JARVIS then the work description. 😉
            </jarvis_response>
    </example>
</examples>

<content>
    User's name: {name} 
</content>
"""
    def _load_jarvis_conversation(self, filepath: str, exists: bool = True) -> None:
         """Loads or creates the conversation history file."""
         if not os.path.isfile(filepath):
            logging.debug(f"Creating new chat-history file - '{filepath}'")
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(self.intro)
         else:
            logging.debug(f"Loading JARVISConversation from '{filepath}'")
            with open(filepath, encoding="utf-8") as fh:
                file_contents: List[str] = fh.readlines()
                if file_contents:
                    self.intro = file_contents[0].strip()
                    self.chat_history = "\n".join(file_contents[1:])


    def _load_memory(self, filepath: str) -> str:
        """Loads the memory from a file."""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def __trim_chat_history(self, chat_history: str, intro: str) -> str:
        """Trims chat history to stay within token limits."""
        len_of_intro: int = len(intro)
        len_of_chat_history: int = len(chat_history)
        total: int = self.max_tokens_to_sample + len_of_intro + len_of_chat_history

        if total > self.history_offset:
            # Find the starting position of the second "User:" section
            first_user_index: int = chat_history.find("\nUser:")
            second_user_index: int = chat_history.find("\nUser:", first_user_index + 1)

            if second_user_index != -1:
                truncate_at: int = second_user_index + self.prompt_allowance
                trimmed_chat_history: str = chat_history[truncate_at:]
                return "... " + trimmed_chat_history
            else:
                return chat_history  # No second "User:" section found, don't trim
        else:
            return chat_history

    def gen_complete_prompt(self, prompt: str, intro: Optional[str] = None) -> str:
        """Generates the complete prompt with history and memory."""
        if self.status:
            intro_str: str = self.intro if intro is None else intro
            incomplete_chat_history: str = self.chat_history + self.history_format % dict(
                role="User", content=prompt
            )

            # Preserve Intro and Memory when trimming
            trimmed_history: str = self.__trim_chat_history(incomplete_chat_history, intro_str)
            
            # Add memory to the chat history using add_message
            self._add_message("Memory", self.memory)

            return intro_str + "\n" + trimmed_history  # Add newline after intro
        return prompt

    def _update_chat_history(self, role: str, content: str, force: bool = False) -> None:
        """Updates chat history and saves to file."""
        if not self.status and not force:
            return
        new_history: str = self.history_format % dict(role=role, content=content)

        # Update chat.txt in real-time
        if self.chat_filepath and self.update_file:
            with open(self.chat_filepath, "a", encoding="utf-8") as fh:
                fh.write(new_history + "\n")

        if self.file and self.update_file:  # Update JARVISConversation_history.txt
            with open(self.file, "a", encoding="utf-8") as fh:
                fh.write(new_history + "\n")

        self.chat_history += new_history
        self.chat_buffer.append(new_history)  # Update the buffer


    def _add_message(self, role: str, content: str) -> None:
        """Adds a message to the chat history."""
        self._update_chat_history(role, content)

    def _summarize_and_save_chat(self) -> None:
        """Periodically summarizes and saves the chat buffer to memory."""
        while True:
            time.sleep(self.save_interval)
            current_time: float = time.time()
            if current_time - self.last_save_time >= self.save_interval:
                self.last_save_time = current_time
                if self.chat_buffer:
                    chat_summary: str = self._summarize_chat(self.chat_buffer)
                    self._save_memory(chat_summary)
                    self.chat_buffer = []  # Clear the buffer after saving

    def _summarize_chat(self, chat_log: List[str]) -> str:
        """Summarizes the chat log into a 100-word summary."""
        full_chat: str = "".join(chat_log)
        prompt: str = f"""
        You are a highly advanced AI assistant tasked with summarizing a conversation.
        Given the following conversation, create a concise summary, focusing on user requests, actions taken, and important information exchanged. 
        Limit your summary to 100 words. 

        Conversation:
        {full_chat}

        Summary:
        """
        ai: webscout.C4ai = webscout.C4ai(is_conversation=False, intro=None)
        summary: str = "".join(ai.chat(prompt)).strip()
        return summary

    def _save_memory(self, summary: str) -> None:
        """Saves the memory summary to the file."""
        with open(self.memory_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        self.memory = summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    conversation = JARVISConversation(name="Vortex")
    prompt1 = "HI"
    prompt2 = "Tell me a joke"
    
    full_prompt1 = conversation.gen_complete_prompt(prompt1)
    conversation._add_message("User", prompt1)
    conversation._add_message("Assistant", "I am doing great thanks for asking")
    full_prompt2 = conversation.gen_complete_prompt(prompt2)
    conversation._add_message("User", prompt2)
    conversation._add_message("Assistant", "Why don't scientists trust atoms? Because they make up everything!")

    print(f"Full Prompt 1: \n{full_prompt1}")
    print(f"Full Prompt 2: \n{full_prompt2}")

    time.sleep(305)
    print(f"Memory saved:\n {conversation.memory}")