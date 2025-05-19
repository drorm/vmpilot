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

# ShellToolResult will be used for history formatting, execute_tool for non-shell or as fallback
# Import shell tool from lllm implementation
from vmpilot.lllm.shelltool import SHELL_TOOL, ShellToolResult
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


def generate_responses(
    body, pipeline_self, messages, system_prompt_suffix, formatted_messages
) -> Generator[str, None, None]:
    """
    LiteLLM version of generate_responses that uses agent_loop instead of process_messages.
    This function is intended to be called from within the pipeline logic.

    Args:
        body: Request body
        pipeline_self: Reference to the pipeline object
        messages: List of messages
        system_prompt_suffix: Additional text to append to the system prompt
        formatted_messages: Formatted messages for the LLM

    Yields:
        Response chunks as they become available
    """
    output_queue = queue.Queue()
    loop_done = threading.Event()

    # Extract the user input from formatted_messages
    user_input = ""
    for msg in formatted_messages:
        if msg.get("role") == "user":
            user_input = msg.get("content", "")
            break

    if not user_input:
        logger.error("No user input found in formatted_messages")
        yield "Error: No user input found"
        return

    # Set up tools - initially just the shell tool
    tools = [SHELL_TOOL]

    # Prepare system prompt with more context from VMPilot
    system_prompt = """You are VMPilot, an AI assistant that can help with system operations.
You can execute shell commands to help users with their tasks.
Always format command outputs with proper markdown formatting.
Be concise and helpful in your responses."""

    # Add system prompt suffix if provided
    if system_prompt_suffix:
        system_prompt += "\n\n" + system_prompt_suffix

    # Log system prompt at debug level
    logger.debug(f"System prompt: {system_prompt}")

    # Run agent_loop in a separate thread
    def run_loop():
        try:
            # Get model from pipeline
            model = pipeline_self.valves.model
            logger.info(f"Using model: {model}")

            # Run the agent loop and stream results to the queue
            for item in agent_loop(
                user_input=user_input,
                system_prompt=system_prompt,
                tools=tools,  # tools are passed to litellm.completion inside agent_loop
                model=model,
            ):
                output_queue.put(item)
        except Exception as e:
            # This top-level exception catch in run_loop might be redundant if agent_loop handles its errors by yielding them
            # However, it can catch errors from agent_loop's setup or if agent_loop itself fails to instantiate/run
            error_msg = f"Error in agent_loop dispatcher: {str(e)}"
            logger.error(error_msg)
            import traceback

            logger.error("".join(traceback.format_tb(e.__traceback__)))
            output_queue.put(f"Error: {str(e)}")
        finally:
            loop_done.set()

    # Start the thread
    thread = threading.Thread(target=run_loop)
    thread.daemon = True
    thread.start()

    # Yield responses from the queue
    response_received = False
    while not loop_done.is_set() or not output_queue.empty():
        try:
            response = output_queue.get(timeout=0.1)
            response_received = True
            yield response
        except queue.Empty:
            pass

    # If no response was received and the loop is done, yield a default message
    if not response_received and loop_done.is_set():
        yield "Command executed but no response was generated."


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
                            # The ShellTool class from shelltool.py is a LangChain BaseTool.
                            # Its execution method is _run, not execute.
                            # It also doesn't return a dict like default_api.shell, but the formatted string directly.
                            shell_tool_instance = VMPilotShellTool()
                            # Call the LangChain tool's execution method _run
                            # It returns the fully formatted string including the command, stdout, and stderr.
                            # We need to parse this or, better, call execute_shell_command directly for more control.

                            # Let's call execute_shell_command directly to get components separately if needed for streaming.
                            # However, the current streaming logic yields command, then output separately.
                            # execute_shell_command itself formats the entire block (command + output).

                            # Option 1: Use execute_shell_command and parse (complex)
                            # Option 2: Modify execute_shell_command to return parts (invasive)
                            # Option 3: Construct output parts here, similar to how execute_shell_command does.

                            # Going with a simplified version of Option 3 for now, using subprocess like execute_shell_command
                            # to get raw output first, then format and yield.

                            import subprocess

                            process_output = subprocess.run(
                                command_to_run,
                                shell=True,
                                capture_output=True,
                                text=True,
                                executable="/bin/bash",
                                timeout=60,
                            )
                            stdout = process_output.stdout.strip()
                            stderr = process_output.stderr.strip()
                            return_code = process_output.returncode

                            if stdout:
                                yield f"```{language}\n{stdout}\n```\n"
                            if stderr and return_code != 0:
                                yield f"**Error (code {return_code}):**\n```text\n{stderr}\n```\n"
                            if not stdout and not stderr:
                                yield "*Command executed with no output*\n"

                            # For history, format it as ShellToolResult expects (command + its full output)
                            # We can call execute_shell_command to get this full formatted block for history
                            # This avoids duplicating formatting logic here and keeps history consistent.
                            from vmpilot.tools.shelltool import (
                                execute_shell_command as format_shell_for_history,
                            )

                            tool_result_for_history = format_shell_for_history(
                                {"command": command_to_run, "language": language}
                            )

                        except subprocess.TimeoutExpired:
                            error_msg = f"Error: Command timed out after 60 seconds: {command_to_run}"
                            yield error_msg + "\n"
                            tool_result_for_history = error_msg
                        except Exception as e:
                            error_msg = f"Error executing shell command: {str(e)}"
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

    # The following commented out code appears to be the source of the problem
    # and should be removed.

    # Remove this append as messages are added for tool results above
    #                messages.append(
    #                    {
    #                        "role": "assistant",
    #                        "content": None, # Or the actual assistant message if it had text + tool_calls
    #                        "tool_calls": [
    #                            {
    #                                "id": tool_call["id"],
    #                                "type": "function",
    #                                "function": {
    #                                    "name": tool_name,
    #                                    "arguments": json.dumps(tool_args), # LiteLLM expects string here
    #                                },
    #                            }
    #                        ],
    #                    }
    #                )
    #                messages.append(
    #                    {
    #                        "role": "tool",
    #                        "content": tool_result,
    #                        "tool_call_id": tool_call["id"],
    #                    }
    #                )
    #
    #        except Exception as e:
    #            logger.error(f"Error in agent loop: {str(e)}")
    #            return f"Error: {str(e)}"
    #
    #    # If we've reached max iterations but have tool results, return those with an error message
    #    if all_tool_results:
    #        return (
    #            "\n".join(all_tool_results)
    #            + "\n\nError: Maximum iterations reached without a final response"
    #        )
    #
    #    return "Error: Maximum iterations reached without a final response"
    #                )
    #                messages.append(
    #                    {
    #                        "role": "tool",
    #                        "content": tool_result,
    #                        "tool_call_id": tool_call["id"],
    #                    }
    #                )
    #
    #        except Exception as e:
    #            logger.error(f"Error in agent loop: {str(e)}")
    #            return f"Error: {str(e)}"
    #
    #    # If we've reached max iterations but have tool results, return those with an error message
    if all_tool_results:
        return (
            "\n".join(all_tool_results)
            + "\n\nError: Maximum iterations reached without a final response"
        )

    return "Error: Maximum iterations reached without a final response"
