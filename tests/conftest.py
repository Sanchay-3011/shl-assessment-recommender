import os
import pytest

# Configure environment variables for test execution
os.environ["GROQ_MODEL"] = "llama-3.1-70b-versatile"
os.environ["GROQ_API_KEY"] = "gsk_dummy_test_key_for_routing"
