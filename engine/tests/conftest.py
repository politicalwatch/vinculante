import os

# The dev container enables LangSmith tracing; tests run fake LLM chains, so without
# this every run uploads traces to the real project. Set before any test imports
# langsmith, which reads (and caches) these on first use.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
