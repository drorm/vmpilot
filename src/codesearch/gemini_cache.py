"""
Google Gemini cache module for code search functionality.
Provides a class to handle Google Gemini API caching operations.
"""

import datetime
import hashlib
import logging
import os
import pathlib
import time
from typing import Any, Dict, Optional, Union

import google.api_core.exceptions
import google.generativeai as genai

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        self.checksum = None  # Store the current checksum for reuse

        # Show existing caches
        # self._show_existing_caches()

    def _show_existing_caches(self):
        """
        List existing caches in the Gemini API.
        """
        logger.info("Existing caches:")
        for cache in genai.caching.CachedContent.list():
            logger.info(cache)

    def generate_checksum(self, file_path: Union[str, pathlib.Path]) -> None:
        """
        Generate an MD5 checksum for a file's content.

        Args:
            file_path: Path to the file to generate checksum for

        Returns:
            MD5 checksum of the file content as a hex string
        """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"The file {path} does not exist.")

        logger.debug(f"Generating MD5 checksum for {path}")
        md5_hash = hashlib.md5()
        with open(path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)

        self.checksum = md5_hash.hexdigest()
        logger.debug(f"Generated checksum: {self.checksum}")

    def upload_code_file(self, file_path: Union[str, pathlib.Path]) -> Dict[str, Any]:
        """
        Upload a code file to Gemini API and wait for processing to complete.

        Args:
            file_path: Path to the code file to upload

        Returns:
            Dictionary containing the processed code file object
        """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"The file {path} does not exist.")

        logger.debug(f"Uploading code file: {path}")
        code_file = genai.upload_file(path=path)

        # Wait for the file to finish processing
        while code_file.state.name == "PROCESSING":
            logger.debug("Waiting for code file to be processed...")
            time.sleep(1)
            code_file = genai.get(name=code_file.name)

        logger.debug(f"Code file processing complete: {code_file.uri}")

        # Return the code file
        return {"file": code_file}

    def find_existing_cache(self) -> Optional[Any]:
        """
        Find an existing cache with the given checksum in the display_name.


        Returns:
            The cache object if found, None otherwise
        """
        cache_name = f"code_search_cache_{self.checksum}"

        logger.debug(f"Looking for existing cache with display_name: {cache_name}")

        try:
            # List all available caches
            found_caches = []
            for cache in genai.caching.CachedContent.list():
                logger.debug(
                    f"Found cache: {cache.name} with display_name: {cache.display_name}"
                )
                found_caches.append(cache.display_name)

                if cache.display_name == cache_name:
                    # Check if the cache is still valid (not expired)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    time_left = cache.expire_time - now
                    time_left_seconds = time_left.total_seconds()

                    if time_left_seconds > 0:
                        logger.debug(
                            f"Found valid existing cache: {cache.name} expires in {time_left_seconds:.1f} seconds"
                        )
                        return cache
                    else:
                        logger.debug(
                            f"Found expired cache: {cache.name} (expired {-time_left_seconds:.1f} seconds ago)"
                        )

            if cache_name not in found_caches:
                logger.info(f"No cache found with display_name: {cache_name}")
                if found_caches:
                    logger.debug(f"Available caches: {', '.join(found_caches)}")
                else:
                    logger.debug("No caches available")

        except Exception as e:
            logger.error(f"Error while looking for existing cache: {e}")

        return None

    def create_cache(
        self,
        model_name: str,
        system_instruction: str,
        contents: list,
        ttl_minutes: int = 5,
    ) -> Any:
        """
        Create a cache for the specified model and content using the checksum
        as part of the display_name.

        Args:
            model_name: Name of the Gemini model to use
            system_instruction: System instruction for the model
            contents: List of content files to include in the cache
            ttl_minutes: Time-to-live in minutes (default: 5)

        Returns:
            The created cache object
        """
        # Create a display name using the checksum
        display_name = f"code_search_cache_{self.checksum}"

        logger.debug(
            f"Creating cache with display_name: {display_name} and {ttl_minutes}-minute TTL..."
        )

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

        logger.info(f"Cache created: {cache.name} with ttl {ttl_minutes} minutes")
        self._current_cache = cache
        self._current_model = self.get_model_from_cache(cache)
        return cache

    def get_or_create_cache(
        self,
        model_name: str,
        file_info: Union[Dict[str, Any], str, pathlib.Path],
        system_instruction: str,
        ttl_minutes: int = 5,
    ) -> Any:
        """
        Get an existing cache or create a new one if none exists.

        Args:
            model_name: Name of the Gemini model to use
            file_info: Either a dictionary with file information, or a file path
            system_instruction: System instruction for the model
            ttl_minutes: Time-to-live in minutes (default: 5)

        Returns:
            The cache object (either existing or newly created)
        """
        # Handle the case where file_info is a file path
        file_path = None
        code_file = None

        if isinstance(file_info, (str, pathlib.Path)):
            file_path = pathlib.Path(file_info)
            # Calculate the checksum first, don't upload yet
            # This will update self.checksum
            self.generate_checksum(file_path)
        else:
            code_file = file_info.get("file")

        # Try to find an existing cache using self.checksum
        existing_cache = self.find_existing_cache()

        if existing_cache:
            logger.info(f"Using existing cache: {existing_cache.name}")
            self._current_cache = existing_cache
            self._current_model = self.get_model_from_cache(existing_cache)
            return existing_cache

        # If no existing cache, we need to upload the file (if not already done)
        if code_file is None and file_path is not None:
            logger.debug(
                f"No existing cache found. Uploading file for new cache creation."
            )
            # Now we upload the file since we need to create a new cache
            logger.debug(f"Uploading code file: {file_path}")
            code_file = genai.upload_file(path=file_path)

            # Wait for the file to finish processing
            while code_file.state.name == "PROCESSING":
                logger.debug("Waiting for code file to be processed...")
                time.sleep(1)
                code_file = genai.get(name=code_file.name)

            logger.debug(f"Code file processing complete: {code_file.uri}")

        # Create a new cache
        return self.create_cache(
            model_name=model_name,
            system_instruction=system_instruction,
            contents=[code_file],
            ttl_minutes=ttl_minutes,
        )

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
                logger.error("Cache expired")
            else:
                logger.error(f"Permission denied: {e}")
            return None
