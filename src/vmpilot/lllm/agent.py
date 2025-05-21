"""
Agent implementation for LiteLLM Migration MVP.
Provides a simple agent loop with tool support using LiteLLM.
"""

import json
import logging
import os
import queue
import threading
import traceback
from typing import Any, Dict, Generator, List

import litellm

# Import shell tool from lllm implementation
from vmpilot.lllm.shelltool import SHELL_TOOL
from vmpilot.lllm.shelltool import execute_tool as lllm_execute_tool_original
from vmpilot.tools.shelltool import (
    ShellTool as VMPilotShellTool,  # For direct shell execution
)

# Configure logging
logger = logging.getLogger(__name__)

# Suppress LiteLLM info/debug logs
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_tool_calls(response) -> tuple:
    """
    Extract tool calls and content from the LLM response.

    Returns:
        tuple: (tool_calls, content) where content is the text message if present
    """
    tool_calls = []
    content = None

    try:
        # Extract tool calls from the response
        message = response.choices[0].message

        # Get content if available
        if hasattr(message, "content") and message.content:
            content = message.content

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                # Parse arguments from JSON string to dict
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {"error": "Failed to parse arguments"}

                tool_calls.append(
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": arguments,
                    }
                )
    except Exception as e:
        logger.error(f"Error parsing tool calls: {str(e)}")

    return tool_calls, content


import asyncio


async def process_messages(
    model,
    provider,
    system_prompt_suffix,
    messages,
    output_callback,
    tool_output_callback,
    api_key,
    max_tokens,
    temperature,
    disable_logging=False,
    recursion_limit=None,
):
    """
    Coroutine for LiteLLM agent: processes messages, streams LLM and tool responses via output/tool callbacks.
    Accepts the same signature as the original for compatibility.
    """
    # Compose system prompt
    system_prompt = "You are VMPilot, an AI assistant that can help with system operations.\nYou can execute shell commands to help users with their tasks.\nAlways format command outputs with proper markdown formatting.\nBe concise and helpful in your responses."
    if system_prompt_suffix:
        system_prompt += f"\n\n{system_prompt_suffix}"
    # Compose user input (last user message)
    user_input = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_input = msg.get("content", "")
            break
    # Set up tools
    tools = [SHELL_TOOL]
    # Call agent_loop and stream outputs through the correct callback
    try:
        for item in agent_loop(
            user_input=user_input,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
        ):
            # Heuristic: if item looks like tool output, call tool_output_callback; else output_callback
            if isinstance(item, dict) and ("output" in item or "error" in item):
                if tool_output_callback:
                    tool_output_callback(item, None)
            else:
                if output_callback:
                    output_callback({"type": "text", "text": item})
            await asyncio.sleep(0)  # Yield control to event loop for streaming
    except Exception as e:
        if output_callback:
            output_callback({"type": "text", "text": f"Error: {str(e)}"})
        raise


# The original synchronous agent_loop entry point remains for internal use


def agent_loop(
    user_input: str,
    system_prompt: str,
    tools: List[Dict[str, Any]],
    model: str = "gpt-4o",
) -> Generator[str, None, None]:
    """
    Simple agent loop that processes user input, sends it to the LLM,
    executes tools when requested, and yields responses and tool outputs as they are generated.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # Set up configuration from environment variables
    api_key = None

    # Get provider from model string
    # TODO: This provider logic should ideally be centralized or handled by LiteLLM's env variables.
    if "openai" in model.lower() or "gpt" in model.lower():
        provider = "openai"
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            yield "Error: OPENAI_API_KEY environment variable not set"
            return
    elif "anthropic" in model.lower() or "claude" in model.lower():
        provider = "anthropic"
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            yield "Error: ANTHROPIC_API_KEY environment variable not set"
            return
    elif "google" in model.lower() or "gemini" in model.lower():
        provider = "google"
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            yield "Error: GOOGLE_API_KEY environment variable not set"
            return
    # Ensure api_key is set if a provider was matched, otherwise LiteLLM might pick one with no key.
    # For providers that don't require explicit keys if configured elsewhere (e.g. Bedrock),
    # this logic might need adjustment or rely on LiteLLM's own key management.
    # For now, if a known provider pattern is matched, we expect a key.
    elif provider not in [
        "openai",
        "anthropic",
        "google",
    ]:  # Check if provider was not set
        # Assuming LiteLLM can handle other models without explicit key here if not in known list.
        # Or, this could be an error:
        # yield f"Error: Unknown model provider for {model}"
        # return
        pass

    # Main agent loop
    max_iterations = 10  # Safety limit to prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Agent loop iteration {iteration}")

        try:
            # Call LLM via LiteLLM
            response = litellm.completion(
                model=model,
                messages=messages,
                tools=tools,
                temperature=0,
                api_key=api_key,
                max_tokens=4000,
            )

            # Parse tool calls and content from response
            tool_calls, content = parse_tool_calls(response)

            # Yield LLM's textual response if present
            if content:
                yield content

            # If no tool calls, we've reached the final response from the LLM for this turn
            if not tool_calls:
                # If there was no textual content, but the LLM didn't call a tool,
                # it might be an empty response or an implicit end of operation.
                # The original code had: final_response = content or response.choices[0].message.content
                # If content was None, but there was a message, yield that.
                # However, parse_tool_calls should already put message.content into `content`.
                # If content is still None and no tools, it's likely the end.
                if (
                    not content and response.choices[0].message.content
                ):  # Ensure full message is out
                    yield response.choices[0].message.content
                return  # End of this agent interaction or loop

            # Append the assistant's message with tool calls to history
            assistant_msg_obj = response.choices[
                0
            ].message  # This is a litellm.Message object

            history_assistant_msg = {
                "role": assistant_msg_obj.role,
                "content": (
                    str(assistant_msg_obj.content)
                    if assistant_msg_obj.content is not None
                    else None
                ),
            }

            if (
                hasattr(assistant_msg_obj, "tool_calls")
                and assistant_msg_obj.tool_calls
            ):
                clean_tool_calls_for_history = []
                for tc_instance in assistant_msg_obj.tool_calls:
                    # tc_instance is expected to be litellm.types.CompletionMessageToolCall
                    # It should have .id, .type, .function (with .name, .arguments)
                    try:
                        # Ensure arguments is a string (JSON string)
                        func_args = tc_instance.function.arguments
                        if not isinstance(func_args, str):
                            logger.warning(
                                f"Tool call function arguments were not a string: {type(func_args)}. Converting to JSON string."
                            )
                            func_args = json.dumps(
                                func_args
                            )  # Should already be JSON string from LLM

                        clean_tool_calls_for_history.append(
                            {
                                "id": tc_instance.id,
                                "type": tc_instance.type,
                                "function": {
                                    "name": tc_instance.function.name,
                                    "arguments": func_args,
                                },
                            }
                        )
                    except AttributeError as e:
                        logger.warning(
                            f"Skipping tool call in history due to missing attributes: {tc_instance}, error: {e}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error processing tool call for history: {tc_instance}, error: {e}"
                        )

                if clean_tool_calls_for_history:  # Only add if list is not empty
                    history_assistant_msg["tool_calls"] = clean_tool_calls_for_history

            messages.append(history_assistant_msg)

            # Execute each tool call and add results to messages
            for (
                tool_call
            ) in (
                tool_calls
            ):  # tool_calls here is from parse_tool_calls(), a list of dicts
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.info(f"Executing tool: {tool_name}")
                tool_result_for_history = ""

                if tool_name == "shell":
                    command_to_run = tool_args.get("command")
                    language = tool_args.get("language", "bash")

                    if command_to_run:
                        yield f"**$ {command_to_run}**\n"  # Yield command string first

                        try:
                            shell_tool_instance = VMPilotShellTool()
                            tool_output_string = lllm_execute_tool_original(
                                "shell",
                                {"command": command_to_run, "language": language},
                            )

                            # Yield the entire formatted string from the tool.
                            yield tool_output_string
                            tool_result_for_history = tool_output_string

                        except (
                            Exception
                        ) as e:  # Catch any exception from the tool call itself
                            error_msg = (
                                f"Error executing shell command via tool: {str(e)}"
                            )
                            yield error_msg + "\n"
                            tool_result_for_history = error_msg
                    else:
                        error_msg = "Error: 'command' argument missing for shell tool"
                        yield error_msg + "\n"
                        tool_result_for_history = error_msg
                else:
                    # Fallback to original lllm_execute_tool for other tools or if shell fails in a different way
                    try:
                        # This part assumes lllm_execute_tool_original returns a string or string-convertible
                        tool_output_obj = lllm_execute_tool_original(
                            tool_name, tool_args
                        )
                        tool_result_for_history = str(tool_output_obj)
                        yield tool_result_for_history + "\n"  # Yield the output directly
                    except Exception as e:
                        tool_result_for_history = (
                            f"Error executing tool {tool_name}: {str(e)}"
                        )
                        yield tool_result_for_history + "\n"

                # Add the tool result to messages for the next LLM call
                messages.append(
                    {
                        "role": "tool",
                        "content": tool_result_for_history,  # Use the carefully prepared history entry
                        "tool_call_id": tool_call["id"],
                    }
                )
            # After processing all tool calls for this iteration, continue the loop
            # for the LLM to process the tool results.

        except Exception as e:
            logger.error(f"Error in agent loop: {str(e)}\n{traceback.format_exc()}")
            yield f"Error: {str(e)}"
            return

    # If we've reached max iterations
    yield "Error: Maximum iterations reached without a final response"

    if all_tool_results:
        return (
            "\n".join(all_tool_results)
            + "\n\nError: Maximum iterations reached without a final response"
        )

    return "Error: Maximum iterations reached without a final response"
