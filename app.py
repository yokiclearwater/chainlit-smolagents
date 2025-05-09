# --- Imports ---
import os
import re
from typing import List, Optional, Dict
from dotenv import load_dotenv
import chainlit as cl
from chainlit.types import ThreadDict
from smolagents import CodeAgent, LiteLLMModel
from agent_tools import ListCSVFilesTool, DataframeOperationTool, FilterDataFrameTool, FinalAnswerTool
import smolagents.memory

def extract_thought(model_output: str) -> str:
    """
    Extracts the content between 'Thought:' and 'Code:'.
    """
    match = re.search(r"Thought:\s*(.*?)(?:\nCode:)", model_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

# --- Load environment variables ---
load_dotenv()

# --- Configuration ---
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini/gemini-2.0-flash"
LITELLM_MODEL = GEMINI_MODEL

SYSTEM_PROMPT = (
    "You are a data analyst with expertise in Python and Pandas. "
    "You can perform various operations on CSV files, including filtering, grouping, and statistical analysis. "
    "You can also list all CSV files in the './dataset' directory. "
    "Your task is to assist the user in analyzing their data. "
    "Use `final_answer()` to return the final answer. in Markdown format."
)

# --- Model Initialization ---
model = LiteLLMModel(
    model_id=LITELLM_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0.3,
    max_tokens=2048,
    
)

# --- OAuth Callback ---
@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    if provider_id == "github":
        return default_user
    return None

# --- Helper: Agent Creation ---
def _create_agent():
    return CodeAgent(
        model=model,
        tools=[
            ListCSVFilesTool(),
            DataframeOperationTool(),
            FilterDataFrameTool(),
            FinalAnswerTool(),
        ],
        additional_authorized_imports=["pandas", "glob", "tabulate", "pathlib"],
        max_steps=20,
        verbosity_level=0,
    )

# --- Chainlit Event Handlers ---
@cl.on_chat_start
async def start_chat():
    cl.user_session.set("chat_history", [])
    if not GITHUB_API_KEY:
        await cl.Message(content="Please set GITHUB_API_KEY in your .env file.").send()
        return
    agent = _create_agent()
    cl.user_session.set("agent", agent)
    await cl.Message(
        content="Hello! I'm your Pandas data analyst. Ask me anything about the CSV files in './dataset'!"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    chat_history = cl.user_session.get("chat_history", [])
    if not GITHUB_API_KEY:
        await cl.Message(content="Error: GITHUB_API_KEY is not configured.").send()
        return
    agent = cl.user_session.get("agent")
    if not agent:
        agent = _create_agent()
        cl.user_session.set("agent", agent)
    if chat_history:
        previous_messages: str = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in chat_history]
        )
        previous_messages_str = f"Converstaion Summary: {previous_messages}\nCurrent Task: {message.content}"
    else:
        previous_messages_str = f"Current Task: {message.content}"

    try:
        def step_callback_output(memory_step: smolagents.memory.MemoryStep):
            thought = extract_thought(str(memory_step.model_output))
            if step.output and step.output != "Thinking...":
                step.output += f"\n\n{thought}"
            else:
                step.output = thought
            # NOTE: we can use cl.run_sync to run async code in the main thread
            cl.run_sync(step.update())  # Update the step output

        agent.step_callbacks = [step_callback_output]
        async with cl.Step(name="Agent is thinking...", type="run", default_open=True) as step:
            step.output = "Thinking..."
            await step.update()
            response = await cl.make_async(agent.run)(
                f"" + previous_messages_str
            )
        await step.update()
        await cl.Message(content=str(response)).send()
        chat_history.append({"role": "user", "content": message.content})
        chat_history.append({"role": "assistant", "content": str(response)})
    except Exception as e:
        await cl.Message(content=f"Sorry, an error occurred: {str(e)}").send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("Chat resumed.")
    if not GITHUB_API_KEY:
        await cl.Message(content="Please set GITHUB_API_KEY in your .env file.").send()
        return
    agent = _create_agent()
    cl.user_session.set("agent", agent)
    chat_history = []
    for message in thread["steps"]:
        if message["type"] == "user_message":
            chat_history.append({"role": "user", "content": message["output"]})
        elif message["type"] == "assistant_message":
            chat_history.append({"role": "assistant", "content": message["output"]})
    cl.user_session.set("chat_history", chat_history)
