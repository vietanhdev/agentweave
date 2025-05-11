"""
Main agent implementation for {{project_name}}.

This file implements a LangGraph agent with configurable tools.
"""

import json
import logging
import operator
import os
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from backend.utils.config import get_llm_config
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# Configure logging
logger = logging.getLogger(__name__)

# Global registry of active agents
_agents = {}

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are an AI assistant for {{project_name}}.

An AI agent built with AgentWeave

Your task is to help users by providing useful, accurate, and relevant information.
When users ask about the weather, ALWAYS use the weather tool to get current weather data.
You have several tools available to help you, including:
- A weather tool to check current weather conditions
- Vector store tools for knowledge retrieval and storage

Step by step:
1. Carefully analyze the user's request
2. If the user asks about weather, use the weather tool with the appropriate location
3. If the user asks about stored information, use the vector_store_query tool
4. When using tools, carefully analyze the results before responding to the user
5. Always provide helpful, concise responses

Important: You must use the appropriate tool rather than making up information yourself.
"""


# Define the agent state schema
class AgentState(TypedDict):
    """State schema for the agent."""

    messages: Annotated[List[AnyMessage], operator.add]
    conversation_id: Optional[str]
    context: Dict[str, Any]


class Agent:
    """
    Agent implementation using LangGraph with a class-based approach.
    """

    def __init__(
        self,
        model_config: Dict[str, Any],
        tools: List[BaseTool],
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        """Initialize an agent with model configuration, tools, and system prompt."""
        self.model_config = model_config
        self.system_prompt = system_prompt

        # Add execution steps tracking
        self.execution_steps = []

        # Make sure we have at least one tool
        if not tools:
            logger.warning(
                "No tools were provided. Agent might not function correctly."
            )

        # Process tools to ensure API keys are properly set
        processed_tools = []
        for tool in tools:
            try:
                # Ensure name is correctly set
                if isinstance(tool, dict):
                    # Handle tools defined as dictionaries
                    logger.warning(f"Tool provided as dictionary: {tool}")
                    continue

                if not hasattr(tool, "name") or not getattr(tool, "name", None):
                    logger.warning(
                        f"Tool without name detected: {getattr(tool, '__dict__', str(tool))}. Skipping."
                    )
                    continue

                # Special handling for weather tool
                if tool.name == "weather":
                    # Try to ensure the weather tool has a proper API key
                    try:
                        from tools.weather import WeatherTool

                        api_key = os.environ.get("OPENWEATHER_API_KEY")
                        if api_key:
                            if api_key == "your_openweather_api_key_here":
                                logger.warning(
                                    "Using placeholder OpenWeather API key. Weather tool will return mock data."
                                )
                            else:
                                # Create a new instance with the API key
                                logger.info(
                                    f"Creating new WeatherTool instance with API key: {api_key[:4]}..."
                                )
                                tool = WeatherTool(api_key=api_key)
                                # Print confirmation for debugging
                                logger.info(
                                    f"Weather tool initialized: {tool.name} with API key: {api_key[:4]}..."
                                )
                    except ImportError:
                        logger.warning(
                            "Could not import WeatherTool - using original tool"
                        )

                processed_tools.append(tool)
                logger.info(f"Added tool: {tool.name}")
            except Exception as e:
                logger.error(f"Error processing tool: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

        # Create map of tools by name for easy lookup
        self.tools_map = {tool.name: tool for tool in processed_tools}
        self.tools = processed_tools

        # Log available tools for debugging
        logger.info(f"Available tools in agent: {list(self.tools_map.keys())}")

        # Initialize LLM
        # Make sure ChatOpenAI is imported at the top level of the file
        try:
            self.model = ChatOpenAI(
                model=model_config.get("model", "gpt-3.5-turbo"),
                temperature=model_config.get("temperature", 0.7),
            )

            # Handle tool binding
            if processed_tools:
                try:
                    # Try with the current API
                    self.llm = self.model.bind_tools(processed_tools)
                    logger.info(
                        f"Successfully bound {len(processed_tools)} tools to LLM"
                    )
                except Exception as e:
                    logger.error(
                        f"Error binding tools to model with bind_tools: {str(e)}"
                    )

                    # Try legacy method
                    try:
                        self.llm = self.model.bind(
                            functions=[tool.metadata for tool in processed_tools]
                        )
                        logger.info("Successfully bound tools using legacy method")
                    except Exception as e2:
                        logger.error(
                            f"Error binding tools with legacy method: {str(e2)}"
                        )
                        self.llm = self.model
                        logger.warning("Using LLM without tool binding")
            else:
                self.llm = self.model
                logger.warning("No tools to bind to LLM")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

            # Fall back to default initialization
            self.model = ChatOpenAI()
            self.llm = self.model

        # Create checkpointer
        memory = MemorySaver()

        # Build the graph
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_llm)
        graph.add_node("action", self.execute_tool)

        # Add conditional edges
        graph.add_conditional_edges(
            "llm", self.should_use_tool, {True: "action", False: END}
        )

        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")

        # Compile the graph
        self.graph = graph.compile(checkpointer=memory)

    def call_llm(self, state: AgentState) -> Dict[str, Any]:
        """Call the LLM with the current conversation history."""
        # Create step to track this action
        step_id = len(self.execution_steps) + 1
        step = {
            "id": step_id,
            "type": "llm_call",
            "timestamp": datetime.now().isoformat(),
            "input": {
                "system_prompt": self.system_prompt[:100] + "..."
                if len(self.system_prompt) > 100
                else self.system_prompt
            },
        }

        try:
            # Extract messages from state
            messages = state.get("messages", [])
            if not messages:
                logger.warning("No messages in state")
                step["output"] = "No messages to process"
                step["status"] = "warning"
                self.execution_steps.append(step)
                return {
                    "messages": [
                        AIMessage(content="I don't have any messages to respond to.")
                    ]
                }

            # Update step input with messages
            step["input"]["messages"] = [
                msg.content if hasattr(msg, "content") else str(msg)
                for msg in messages[-5:]
                if messages
            ]

            # Check if there are weather-related keywords in the last user message
            modified_system_prompt = self.system_prompt
            if messages and hasattr(messages[-1], "content") and messages[-1].content:
                last_message = messages[-1].content.lower()
                weather_keywords = [
                    "weather",
                    "temperature",
                    "hot",
                    "cold",
                    "rainy",
                    "sunny",
                    "forecast",
                ]

                # Check if any weather keyword is in the last message
                if any(keyword in last_message for keyword in weather_keywords):
                    # Add a custom instruction to use the weather tool
                    weather_tools_available = "weather" in self.tools_map
                    if weather_tools_available:
                        logger.info("Adding weather tool instruction to system prompt")
                        weather_instruction = "\nI notice you're asking about weather. I'll use the weather tool to get you the most up-to-date information."
                        modified_system_prompt += weather_instruction

            # Build the list of messages to send to the LLM
            prompt_messages = [SystemMessage(content=modified_system_prompt)]

            # Add only the recent messages to avoid context length issues
            max_messages = 10  # Limit to avoid context length issues
            for msg in messages[-max_messages:]:
                prompt_messages.append(msg)

            # Call the LLM directly
            logger.info(f"Calling LLM with {len(prompt_messages)} messages")
            response = self.llm.invoke(prompt_messages)

            # Update the step with the result
            step["output"] = (
                response.content if hasattr(response, "content") else str(response)
            )
            step["status"] = "success"
            self.execution_steps.append(step)

            return {"messages": [response]}

        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")

            # Update the step with the error
            step["error"] = str(e)
            step["status"] = "error"
            self.execution_steps.append(step)

            error_message = AIMessage(content=f"I encountered an error: {str(e)}")
            return {"messages": [error_message]}

    def should_use_tool(self, state: AgentState) -> bool:
        """
        Determine if the agent should use a tool.

        Args:
            state: The current agent state

        Returns:
            True if the agent should use a tool, False otherwise
        """
        if not state["messages"]:
            return False

        last_message = state["messages"][-1]
        # Check for tool_calls attribute in different ways
        tool_calls = None

        if hasattr(last_message, "tool_calls"):
            tool_calls = last_message.tool_calls
        elif (
            hasattr(last_message, "additional_kwargs")
            and "tool_calls" in last_message.additional_kwargs
        ):
            tool_calls = last_message.additional_kwargs.get("tool_calls")

        # If tool_calls is explicitly defined, use it
        if tool_calls is not None:
            has_tool_calls = len(tool_calls) > 0
            logger.info(f"Found {len(tool_calls) if has_tool_calls else 0} tool calls")
            return has_tool_calls

        # If no tool_calls found but the content contains indicators of tools
        elif hasattr(last_message, "content") and last_message.content:
            content = last_message.content.lower()

            # Check for patterns that suggest tool usage
            weather_patterns = [
                "weather in",
                "weather for",
                "temperature in",
                "weather at",
                "current weather",
                "check weather",
            ]

            # Check if any weather pattern is in the content
            for pattern in weather_patterns:
                if pattern in content:
                    logger.info(
                        f"Detected weather pattern: '{pattern}' in message: '{content}'"
                    )
                    return True

            # No tool use detected from content
            return False

        # Default case - no tool use
        return False

    def execute_tool(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute tools called by the LLM.

        Args:
            state: The current agent state

        Returns:
            Updates to the state
        """
        if not state["messages"]:
            return {"messages": []}

        last_message = state["messages"][-1]

        # Extract tool calls in a safe way
        tool_calls = None
        if hasattr(last_message, "tool_calls"):
            tool_calls = last_message.tool_calls
        elif (
            hasattr(last_message, "additional_kwargs")
            and "tool_calls" in last_message.additional_kwargs
        ):
            tool_calls = last_message.additional_kwargs.get("tool_calls")

        if not tool_calls:
            logger.warning("No tool calls found in message")
            return {"messages": []}

        # Log information about available tools
        logger.info(f"Available tools: {list(self.tools_map.keys())}")

        results = []
        for tool_call in tool_calls:
            # Extract tool information safely
            if isinstance(tool_call, dict):
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get(
                    "name"
                )
                tool_args = tool_call.get("args") or tool_call.get("function", {}).get(
                    "arguments", "{}"
                )
                tool_id = tool_call.get("id")
            else:
                # Try different attributes that might exist
                tool_name = None
                tool_args = "{}"
                tool_id = None

                # Try to get name
                if hasattr(tool_call, "name"):
                    tool_name = tool_call.name
                elif hasattr(tool_call, "function") and hasattr(
                    tool_call.function, "name"
                ):
                    tool_name = tool_call.function.name

                # Try to get args
                if hasattr(tool_call, "args"):
                    tool_args = tool_call.args
                elif hasattr(tool_call, "function") and hasattr(
                    tool_call.function, "arguments"
                ):
                    tool_args = tool_call.function.arguments

                # Try to get id
                if hasattr(tool_call, "id"):
                    tool_id = tool_call.id

            # Log what we extracted
            logger.info(
                f"Extracted tool call: name={tool_name}, args={tool_args}, id={tool_id}"
            )

            # Convert string arguments to dict if needed
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse tool arguments: {str(e)}. Using as string input."
                    )
                    tool_args = (
                        {"location": tool_args}
                        if tool_name == "weather"
                        else {"input": tool_args}
                    )

            # Create a step to track this tool execution
            step_id = len(self.execution_steps) + 1
            step = {
                "id": step_id,
                "type": "tool_call",
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "input": tool_args,
                "tool_id": tool_id,
            }

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            try:
                if tool_name and tool_name in self.tools_map:
                    tool = self.tools_map[tool_name]
                    logger.info(f"Found tool in tools_map: {tool.name}")

                    # Special handling for weather tool
                    if (
                        tool_name == "weather"
                        and "location" not in tool_args
                        and len(tool_args) > 0
                    ):
                        # Try to extract location from args
                        if isinstance(tool_args, dict) and (
                            first_value := next(iter(tool_args.values()), None)
                        ):
                            # Use the first value as location
                            tool_args = {"location": first_value}
                            logger.info(f"Extracted location from args: {tool_args}")

                    # Call the tool and get the result
                    try:
                        tool_result = tool.invoke(tool_args)

                        # Update the step with the result
                        step["output"] = tool_result
                        step["status"] = "success"
                        self.execution_steps.append(step)

                        # Create a tool message for the result
                        results.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_id or "unknown",
                                name=tool_name,
                            )
                        )
                    except Exception as e:
                        # Tool execution failed
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        logger.error(error_msg)

                        # Update the step with the error
                        step["error"] = error_msg
                        step["status"] = "error"
                        self.execution_steps.append(step)

                        # Create an error tool message
                        results.append(
                            ToolMessage(
                                content=f"Error: {error_msg}",
                                tool_call_id=tool_id or "unknown",
                                name=tool_name,
                            )
                        )
                else:
                    # Tool not found
                    error_msg = f"Tool {tool_name} not found in available tools: {list(self.tools_map.keys())}"
                    logger.error(error_msg)

                    # Try to provide a fallback for weather tool
                    if tool_name == "weather" and "location" in tool_args:
                        fallback_msg = (
                            f"I don't have access to real-time weather data for {tool_args.get('location')}. "
                            + "You can check a weather website or app for the current conditions."
                        )
                        results.append(
                            ToolMessage(
                                content=fallback_msg,
                                tool_call_id=tool_id or "unknown",
                                name=tool_name,
                            )
                        )

                        # Add step for tracking
                        step["output"] = fallback_msg
                        step["status"] = (
                            "success"  # Mark as success since we provided a fallback
                        )
                        self.execution_steps.append(step)
                    else:
                        # Update the step with the error
                        step["error"] = error_msg
                        step["status"] = "error"
                        self.execution_steps.append(step)

                        # Create an error tool message
                        results.append(
                            ToolMessage(
                                content=f"Error: {error_msg}",
                                tool_call_id=tool_id or "unknown",
                                name=tool_name if tool_name else "unknown_tool",
                            )
                        )
            except Exception as e:
                # Something went wrong in the try/except itself
                error_msg = f"Error in tool execution process: {str(e)}"
                logger.error(error_msg)

                # Update the step with the error
                step["error"] = error_msg
                step["status"] = "error"
                self.execution_steps.append(step)

                # Create an error tool message
                results.append(
                    ToolMessage(
                        content=f"Error: {error_msg}",
                        tool_call_id=tool_id or "unknown",
                        name=tool_name if tool_name else "unknown_tool",
                    )
                )

        return {"messages": results}


def get_agent_config() -> Dict[str, Any]:
    """Get the agent configuration."""
    config = get_llm_config()

    # Set defaults if not provided
    if "llm_provider" not in config:
        config["llm_provider"] = "openai"

    if "model" not in config:
        config["model"] = "gpt-3.5-turbo-0125"

    if "temperature" not in config:
        config["temperature"] = 0.7

    return config


def create_agent(conversation_id: Optional[str] = None, reset: bool = False) -> Any:
    """
    Create or get an agent for a conversation.

    Args:
        conversation_id: Unique identifier for the conversation
        reset: Whether to reset the agent if it already exists

    Returns:
        The agent instance
    """
    global _agents

    # Generate a new conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Check if we need to create a new agent
    if reset or conversation_id not in _agents:
        # Get configuration
        config = get_agent_config()

        # Create tools directly instead of using registry
        try:
            # Initialize the tools list
            tools = []

            # Create weather tool
            try:
                from tools.weather import WeatherTool

                weather_tool = WeatherTool()
                logger.info(f"Created weather tool with name: {weather_tool.name}")
                tools.append(weather_tool)
            except Exception as e:
                logger.error(f"Error creating weather tool: {str(e)}")

            # Load a calculator tool if available
            try:
                from langchain.chains import LLMMathChain
                from langchain.tools import Tool
                from langchain_openai import OpenAI

                llm = OpenAI(temperature=0)
                llm_math_chain = LLMMathChain.from_llm(llm=llm, verbose=True)
                calc_tool = Tool(
                    name="calculator",
                    func=llm_math_chain.run,
                    description="Useful for when you need to answer questions about math.",
                )
                tools.append(calc_tool)
                logger.info("Created calculator tool")
            except Exception as e:
                logger.error(f"Error creating calculator tool: {str(e)}")

            # Try to get other tools from registry
            try:
                from tools.registry import get_available_tools

                registry_tools = get_available_tools()
                logger.info(f"Loaded {len(registry_tools)} tools from registry")
                # Add non-duplicate tools
                for tool in registry_tools:
                    if not any(t.name == tool.name for t in tools):
                        tools.append(tool)
            except Exception as e:
                logger.error(f"Error loading tools from registry: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

            if not tools:
                logger.warning(
                    "No tools could be created. The agent might not function correctly."
                )
        except Exception as e:
            logger.error(f"Error setting up tools: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            # Fallback to empty tools list
            tools = []

        logger.info(
            f"Creating agent with {len(tools)} tools: {[getattr(t, 'name', str(t)) for t in tools]}"
        )

        # Create a new agent
        agent = Agent(
            model_config=config, tools=tools, system_prompt=DEFAULT_SYSTEM_PROMPT
        )

        _agents[conversation_id] = {
            "agent": agent,
            "conversation_id": conversation_id,
            "messages": [],
        }

    return _agents[conversation_id]


def invoke_agent(
    agent: Dict[str, Any],
    query: str,
    conversation_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Invoke the agent with a query.

    Args:
        agent: The agent instance
        query: The user query to process
        conversation_id: The conversation ID
        context: Additional context for the agent

    Returns:
        The agent response
    """
    if conversation_id is None:
        conversation_id = agent["conversation_id"]

    if context is None:
        context = {}

    # Add the user message to the message history
    user_message = HumanMessage(content=query)

    # Prepare the thread config
    thread = {"configurable": {"thread_id": conversation_id}}

    # Prepare the initial state for the graph
    initial_state = {
        "messages": agent["messages"] + [user_message],
        "conversation_id": conversation_id,
        "context": context,
    }

    # Reset execution steps for this invocation
    agent_instance = agent["agent"]
    agent_instance.execution_steps = []

    # Invoke the agent
    try:
        result = agent_instance.graph.invoke(initial_state, thread)

        # Store updated messages in agent
        agent["messages"] = result["messages"]

        # Extract the last AI message as the response
        messages = result["messages"]
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                response = message.content
                break
        else:
            # Fallback if no AI message found
            response = "I'm not sure how to respond to that."

        # Include execution steps in the response metadata
        execution_steps = agent_instance.execution_steps

        return {
            "response": response,
            "conversation_id": conversation_id,
            "metadata": {
                "message_count": len(messages),
                "execution_steps": execution_steps,
            },
        }
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        raise e
