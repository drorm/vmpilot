"""
Functions for building search prompts and executing searches.
These are used by the search.py module.
"""

import logging
import os
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
import openai

# Set up logging
logger = logging.getLogger(__name__)


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


def execute_search(prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the search by calling the LLM API.

    Args:
        prompt: The prompt to send to the LLM
        config: Configuration dictionary

    Returns:
        Dictionary containing search results
    """
    api_config = config.get("api", {})
    provider = api_config.get("provider", "openai")
    temperature = api_config.get("temperature", 0.2)
    top_p = api_config.get("top_p", 0.95)

    try:
        if provider == "gemini":
            # Check for API key in environment
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-8b",
                generation_config={
                    "temperature": temperature,
                    "top_p": top_p,
                },
            )

            response = model.generate_content(prompt)
            response_text = response.text

        elif provider == "openai":
            # Check for API key in environment
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            openai.api_key = api_key
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
            )
            response_text = response.choices[0].message.content

        return {
            "response": response_text,
        }

    except Exception as e:
        logger.error(f"Error in execute_search: {str(e)}")
        return {"error": str(e), "response": f"Error executing search: {str(e)}"}
