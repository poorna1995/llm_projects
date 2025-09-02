# plan the query 
# template of the agent ( agent (name, instruction ( system prompt), model, tools))
# run (agent, ,messge ( query))


import os
from dotenv import load_dotenv
from agents import Agent
from config import PLANNER, HOW_MANY_SEARCHES, MODEL_NAME, MESSAGE, WebSearchItem, WebSearchPlan
from pydantic import BaseModel, Field



load_dotenv(override=True)

def planner_agent():
    return Agent(
        model=MODEL_NAME,
        instructions=PLANNER["INSTRUCTIONS_PLANNER"],
        output_type = WebSearchPlan,
        name = "Planner Agent"
    )





# instructions