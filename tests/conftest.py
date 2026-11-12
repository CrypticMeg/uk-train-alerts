"""Shared pytest setup for every test suite.

Always use dummy values so tests can never hit a real ntfy topic or RTT
account. load_dotenv() does not override variables that are already set.
"""
import os

os.environ["RTT_API_TOKEN"] = "test-rtt-token"
os.environ["NTFY_TOPIC_URL"] = "https://ntfy.invalid/test-topic"
