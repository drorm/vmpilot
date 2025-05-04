"""
Functions for building search prompts and executing searches.
These are used by the search.py module.
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
import openai

from codesearch.gemini_cache import GeminiCache
from codesearch.simple_usage import Usage

# Set up logging
logger = logging.getLogger(__name__)


def get_system_instruction() -> str:
    """
    Get the system instruction for the code search.

    Returns:
        The system instruction string
    """
    return """
You are a code search assistant that helps developers find relevant information in their codebase.

Your task is to analyze the provided code files and provide a comprehensive answer to the search query.

For each relevant section of code, include:
1. The file path
2. The specific code snippet that's relevant
3. An explanation of how it relates to the query

INSTRUCTIONS:
1. Focus on directly answering the search query with specific code references
2. If the provided files don't contain relevant information, say so clearly
3. If you need additional context or files to provide a complete answer, mention what's missing
4. Format your response in a clear, structured way with code snippets and explanations
5. Prioritize accuracy over comprehensiveness
"""


def build_search_prompt(
    files: List[Tuple[str, str]], query: str, config: Dict[str, Any]
) -> str:
    """
    Build a prompt for the LLM search based on the query and files.

    Args:
        files: List of (file_path, content) tuples
        query: User search query
        config: Configuration dictionary

    Returns:
        The constructed prompt
    """
    prompt = f"""
You are a code search assistant that helps developers find relevant information in their codebase.

SEARCH QUERY: {query}

I'll provide you with the content of relevant files from the codebase.
Your task is to analyze these files and provide a comprehensive answer to the search query.

For each relevant section of code, include:
1. The file path
2. The specific code snippet that's relevant
3. An explanation of how it relates to the query

CODEBASE FILES:
"""

    for filepath, content in files:
        prompt += f"\n--- FILE: {filepath} ---\n"
        prompt += content
        prompt += "\n--- END FILE ---\n"

    prompt += """
INSTRUCTIONS:
1. Focus on directly answering the search query with specific code references
2. If the provided files don't contain relevant information, say so clearly
3. If you need additional context or files to provide a complete answer, mention what's missing
4. Format your response in a clear, structured way with code snippets and explanations
5. Prioritize accuracy over comprehensiveness

Now, please provide a comprehensive answer to the search query based on the provided code files.
"""

    return prompt


def prepare_files_for_cache(files: List[Tuple[str, str]]) -> str:
    """
    Prepare files for caching by combining them into a single content string.

    Args:
        files: List of (file_path, content) tuples

    Returns:
        A single string containing all file contents with headers
    """
    content = "CODEBASE FILES:\n"

    for filepath, file_content in files:
        content += f"\n--- FILE: {filepath} ---\n"
        content += file_content
        content += "\n--- END FILE ---\n"

    return content


def execute_search(
    prompt: str, config: Dict[str, Any], files: List[Tuple[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute the search by calling the LLM API.

    Args:
        prompt: The prompt to send to the LLM
        config: Configuration dictionary
        files: List of (file_path, content) tuples for caching (only needed for Gemini)

    Returns:
        Dictionary containing search results and usage information
    """
    api_config = config.get("api", {})
    provider = api_config.get("provider", "openai")
    temperature = api_config.get("temperature", 0.2)
    top_p = api_config.get("top_p", 0.95)

    # throw error if provider is not supported
    model_name = api_config.get("model")
    if not model_name:
        raise ValueError("Model name is required in the configuration")

    # Initialize usage tracker
    # Map provider to string for usage tracking
    provider_str = provider  # Default to the provided string
    usage_tracker = Usage(provider=provider_str, model_name=model_name)

    try:
        if provider == "gemini":
            # Check for API key in environment
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")

            # Check if files are provided for caching
            if files:
                # Use caching mechanism
                logger.info("Using Gemini cache for code search")

                # Initialize the cache
                gemini_cache = GeminiCache(api_key=api_key)

                # Prepare files for caching
                combined_content = prepare_files_for_cache(files)

                # Create a temporary file to store the combined content
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as temp_file:
                    temp_file.write(combined_content)
                    temp_file_path = temp_file.name

                try:
                    # Get system instruction
                    system_instruction = get_system_instruction()

                    # Get or create cache with a 5-minute TTL
                    cache = gemini_cache.get_or_create_cache(
                        model_name=model_name,
                        file_info=temp_file_path,
                        system_instruction=system_instruction,
                        ttl_minutes=5,
                    )

                    # Extract the query from the prompt
                    query_start = prompt.find("SEARCH QUERY:") + len("SEARCH QUERY:")
                    query_end = prompt.find("\n\nI'll provide you")
                    query = prompt[query_start:query_end].strip()

                    # Generate response using the cache
                    full_query = f"SEARCH QUERY: {query}\n\nPlease provide a comprehensive answer to this search query based on the provided code files."
                    response = gemini_cache.generate_from_cache(full_query)

                    if response is None:
                        logger.warning(
                            "Cache expired, falling back to standard API call"
                        )
                        # Fall back to standard API call
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            generation_config={
                                "temperature": temperature,
                                "top_p": top_p,
                            },
                        )
                        response = model.generate_content(prompt)
                        response_text = response.text
                    else:
                        response_text = response.text
                        logger.info("Successfully used Gemini cache for response")
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
            else:
                # Standard API call without caching (fallback)
                logger.info("Using standard Gemini API call (no caching)")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=usage_tracker.model_name,
                    generation_config={
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                )
                response = model.generate_content(prompt)
                response_text = response.text

            # Instead of trying to extract tokens from the response, use a simple estimation
            # Estimate: 1 token ≈ 4 characters for both input and output
            estimated_prompt_tokens = len(prompt) // 4
            estimated_completion_tokens = len(response_text) // 4

            # Manually add token estimates
            usage_tracker.input_tokens += estimated_prompt_tokens
            usage_tracker.output_tokens += estimated_completion_tokens

            logger.info(
                f"Estimated tokens - input: {estimated_prompt_tokens}, output: {estimated_completion_tokens}"
            )

        elif provider == "openai":
            # Check for API key in environment
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            openai.api_key = api_key

            # Use model_name from usage_tracker (set from config)
            response = openai.chat.completions.create(
                model=usage_tracker.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
            )
            response_text = response.choices[0].message.content

            # Instead of trying to extract tokens from the response, use a simple estimation
            # Estimate: 1 token ≈ 4 characters for both input and output
            estimated_prompt_tokens = len(prompt) // 4
            estimated_completion_tokens = len(response_text) // 4

            # Manually add token estimates
            usage_tracker.input_tokens += estimated_prompt_tokens
            usage_tracker.output_tokens += estimated_completion_tokens

            logger.info(
                f"Estimated tokens - input: {estimated_prompt_tokens}, output: {estimated_completion_tokens}"
            )

        # Get usage cost message
        cost_message = usage_tracker.get_cost_message()

        return {"response": response_text, "usage_cost": cost_message}

    except Exception as e:
        logger.error(f"Error in execute_search: {str(e)}")
        return {"error": str(e), "response": f"Error executing search: {str(e)}"}
