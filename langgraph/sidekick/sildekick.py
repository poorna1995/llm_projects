from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from config import pushover_token, pushover_user, pushover_url, serper

# 1. Playwright --> brower enginer( can navigate, click, ectract, ans so)
# 2. push tool s--> using the pushover api to push the notifcation for the tuser
# 3. get files tools --> acces the local gfiels
# 4. other wikipedia;
# 5. serpertool

#  5. python_repl = pythosRepl TOOls




async def playwright_tools():
    playwright = await async_playwright().start()                       # playwright → the main Playwright instance (so you can stop it when done)
    browser = await playwright.chromium.launch(headless=False)          # browser → the open browser object (so you can close it later)
    toolkit = PlayWrightBrowserToolkit(async_browser= async_browser)
    tools = toolkit.get_tools()                                         #tools → the agent’s ready-to-use Playwright tools
    return tools, browser, playwright


def push(text:str):
    """send notification to the user"""
    payload = {'token':pushover_token, 'user':pushover_user, 'message':text}
    requests.post(pushover_url, data=payload )
    return {'status':"success"}



def get_file_tools():
    toolkit = FileManagementToolkit(root_dir = 'sandbox')
    return toolkit.get(tools)

async def other tools():
    push_tools = Tools(name = 'send push notification', func = push, description= 'send the push notifiction to the user')
    
    file_tools = get_file_tools()

    search_tool = Tool(
        name = "search",
        func = serper.run,
        description = "use this tool to get the content/information and result of an online websseach goole"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    return file_tools + [push_tool, tool_search, python_repl,  wiki_tool]









