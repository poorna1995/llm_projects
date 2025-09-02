
from duckduckgo_search import DDGS
from pydantic import BaseModel, Field


HOW_MANY_SEARCHES = 3
MODEL_NAME = "gpt-4o-mini"
MESSAGE = "Latest AI Agent frameworks in 2025"


PLANNER = {
    "INSTRUCTIONS_PLANNER": (
        f"You are a helpful research assistant. Given a query, "
        f"come up with a set of web searches to perform to best answer the query. "
        f"Output {HOW_MANY_SEARCHES} terms to query for."
    )
}

SEARCH = {
    "INSTRUCTIONS_SEARCH": (
        "You are a research assistant. Given a search term, you search the web for that term and "
        "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than "
        "300 words. Capture the main points. Write succinctly; no need for complete sentences or "
        "perfect grammar. This will be consumed by someone synthesizing a report, so it is vital "
        "you capture the essence and ignore fluff. Do not include any additional commentary other "
        "than the summary itself."
    )
}


WRITER = {
    "INSTRUCTIONS_WRITER" :(
            "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."

    )

}



class ReportData(BaseModel):
    short_summary:str = Field(description = " A short 2-3 summary of the findings")

    markdown)report :str = Field(description = " The final report")
    follow_uo_quesitons : list[str] = Field(description="Suggested topics to research further")

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    

@function_tool
def duckduckgo_search(query:str) ->str:
    print(f"Running DuckDuckGo news search for {query}...")
    
    # DuckDuckGo search
    ddg_api = DDGS()
    results = ddg_api.text(f"{query} ", max_results=2)
    if results:
        news_results = "\n\n".join([f"Title: {result['title']}\nURL: {result['href']}\nDescription: {result['body']}" for result in results])
        print(news_results)
        return news_results
    else:
        return f"Could not find news results for {query}."
    



