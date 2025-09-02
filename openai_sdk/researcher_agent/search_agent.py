# search the query
from config import MODEL_NAME, SEARCH, duckduckgo_search
from agents import Agent, ModelSettings


def search_agent = Agent(
    model_name = MODEL_NAME,
    instructions = SEARCH.INSTRUCTIONS_SEARCH,
    tools = [duckduckgo_search],
    name = "search agent",
    model_settings = ModelSettings(tool_choice = "required")
)