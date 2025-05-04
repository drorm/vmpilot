"""
Google Gemini cache module for code search functionality.
Provides a class to handle Google Gemini API caching operations.
"""

import datetime
import os
import pathlib
import time
from typing import Any, Optional, Union

import google.api_core.exceptions
import google.generativeai as genai


class GeminiCache:
    """
    A class to handle Google Gemini caching operations.
    This class provides methods for creating caches and using cached models.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GeminiCache with API key configuration.

        Args:
            api_key: Google API key (optional, will use environment variable if not provided)
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Please provide a Google API key or set the GOOGLE_API_KEY environment variable"
            )

        # Configure the Gemini API client
        genai.configure(api_key=self.api_key)

        # Store the current model and cache for reuse
        self._current_model = None
        self._current_cache = None

    def upload_code_file(self, file_path: Union[str, pathlib.Path]) -> Any:
        """
        Upload a code file to Gemini API and wait for processing to complete.

        Args:
            file_path: Path to the code file to upload

        Returns:
            The processed code file object
        """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"The file {path} does not exist.")

        print(f"Uploading code file: {path}")
        code_file = genai.upload_file(path=path)

        # Wait for the file to finish processing
        while code_file.state.name == "PROCESSING":
            print("Waiting for code file to be processed...")
            time.sleep(2)
            code_file = genai.get(name=code_file.name)

        print(f"Code file processing complete: {code_file.uri}")
        return code_file

    def create_cache(
        self,
        model_name: str,
        display_name: str,
        system_instruction: str,
        contents: list,
        ttl_minutes: int = 5,
    ) -> Any:
        """
        Create a cache for the specified model and content.

        Args:
            model_name: Name of the Gemini model to use
            display_name: Display name for the cache
            system_instruction: System instruction for the model
            contents: List of content files to include in the cache
            ttl_minutes: Time-to-live in minutes (default: 5)

        Returns:
            The created cache object
        """
        print(f"Creating cache with {ttl_minutes}-minute TTL...")

        # Convert minutes to timedelta
        ttl = datetime.timedelta(minutes=ttl_minutes)

        # Create the cache
        cache = genai.caching.CachedContent.create(
            model=model_name,
            display_name=display_name,
            system_instruction=system_instruction,
            contents=contents,
            ttl=ttl,
        )

        print(f"Cache created: {cache.name}")
        self._current_cache = cache
        self._current_model = self.get_model_from_cache(cache)
        return cache

    def get_model_from_cache(self, cache: Any) -> Any:
        """
        Create a model instance from the specified cache.

        Args:
            cache: The cache object to use

        Returns:
            A model instance that uses the cache
        """
        return genai.GenerativeModel.from_cached_content(cached_content=cache)

    def generate_from_cache(self, prompt: str, model: Any = None) -> Any:
        """
        Generate content using a cached model with error handling.
        If no model is provided, uses the current model from the last created cache.

        Args:
            prompt: The prompt to send to the model
            model: The model instance from cache (optional)

        Returns:
            The generated response or None if cache expired
        """
        # Use provided model or fall back to current model
        model_to_use = model or self._current_model

        if model_to_use is None:
            raise ValueError(
                "No model available. Create a cache first or provide a model."
            )

        try:
            return model_to_use.generate_content(prompt)
        except google.api_core.exceptions.PermissionDenied as e:
            if "CachedContent not found" in str(e):
                print("Cache expired")
            else:
                print(f"Permission denied: {e}")
            return None
