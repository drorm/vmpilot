"""
Test script for the GeminiCache class.
Demonstrates cache creation and usage for code search.
"""

import pathlib
import time

from gemini_cache import GeminiCache

# Initialize the GeminiCache
gemini_cache = GeminiCache()

# Path to the all.py file that contains the concatenated Python code
path_to_code_file = pathlib.Path(__file__).parent / "all.py"

# Specify the model to use
model_name = "gemini-1.5-flash-8b"

# System instruction for the code analysis
system_instruction = (
    "You are an expert code analyzer. Your job is to answer "
    "questions about the provided Python code. Analyze the code structure, "
    "functionality, and provide clear explanations when asked."
)

# Get or create a cache with a 1-minute TTL using the file's checksum as part of the display name
cache = gemini_cache.get_or_create_cache(
    model_name=model_name,
    file_info=path_to_code_file,
    system_instruction=system_instruction,
    ttl_minutes=2,
)

# First request using the cache
print("\n--- First Request ---")
response = gemini_cache.generate_from_cache("Give a brief summary of this code")

# If cache expired, exit gracefully
if response is None:
    print("Exiting due to expired cache")
    exit(1)

# Print usage metadata to verify cache usage
print("\nUsage Metadata:")
print(response.usage_metadata)

# Print the first 80 characters of the response
print("\nResponse:")
print(response.text[:80])

# Wait a bit and make another request to demonstrate cache reuse
print("\n--- Sleeping for 5 seconds ---")
time.sleep(5)

# Second request using the same cache
print("\n--- Second Request (should use cache) ---")
response = gemini_cache.generate_from_cache("What are the main functions in this code?")

# If cache expired, exit gracefully
if response is None:
    print("Exiting due to expired cache")
    exit(1)

# Print usage metadata to verify cache usage
print("\nUsage Metadata:")
print(response.usage_metadata)

# Print the response
print("\nResponse:")
print(response.text[:80])

"""
# Wait until close to cache expiration
print("\n--- Waiting for cache to approach expiration ---")
time.sleep(60)

# Third request when cache is about to expire
print("\n--- Third Request (cache nearing expiration) ---")
response = gemini_cache.generate_from_cache(
    "Explain the purpose of the usage tracking in this code"
)

# If cache expired, exit gracefully
if response is None:
    print("Exiting due to expired cache")
    exit(1)

# Print usage metadata
print("\nUsage Metadata:")
print(response.usage_metadata)

# Print the response
print("\nResponse:")
print(response.text)

print("\nCache test completed!")
"""
