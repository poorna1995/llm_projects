from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from .tools.push_notification import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from pydantic import BaseModel, Field
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


class TrendingCompany(BaseModel):
    """A company that is in the new and attracting attention"""
    name : str = Field(description = "Company Name")
    ticker : str = Field (description = "The ticker symbol of the Stock")
    reason : str = Field (description = " Reason why the company is trending the news")

class TrendingCompanyList(BaseModel):
    """ List of multiple trending companies that are in the news """
    companies: List[TrendingCompany] = Field(description="List of companies trending in the news")

class TrendingCompanyResearch(BaseModel):
    """ Detailed research on a company """
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")

class TrendingCompanyResearchList(BaseModel):
    """ A list of detailed research on all the companies """
    research_list: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def trending_company_finder(self) ->Agent:
        return Agent(
            config = self.agents_config['trending_company_finder'], verbose = True, tools = [SerperDevTool()], memory = True
        )


    @agent
    def financial_researcher(self)->Agent:
        return Agent(
            config = self.agents_config['financial_researcher'] , verbose = True, tools = [SerperDevTool()]
        )

    @agent
    def stock_picker(self)->Agent:
        return Agent(
            config = self.agents_config['stock_picker'] , verbose = True, tools = [PushNotificationTool],  memory = True
        )
    @agent
    def manager(self)->Agent:
        return Agent(
            config = self.agents_config['manager'] , verbose = True
        )
    
    @task
    def find_trending_companies(self)->Task:
        return Task(
            config = self.tasks_config['find_trending_companies'] , verbose = True,
            output_pydantic = TrendingCompanyList
        )
    @task
    def research_trending_companies(self)->Task:
        return Task(
            config = self.tasks_config['research_trending_companies'] , verbose = True,
            output_pydantic = TrendingCompanyResearchList
        )


    @task
    def pick_best_company(self)->Task:
        return Task(
            config = self.tasks_config['pick_best_company'] , verbose = True

        )

    @crew
    def crew(self) ->Crew:
        manager = Agent(
            config = self.agents_config ("manager"), allow_delegation = True

        )
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            # Long-term memory for persistent storage across sessions
            long_term_memory = LongTermMemory(
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            # Short-term memory for current context using RAG
            short_term_memory = ShortTermMemory(
                storage = RAGStorage(
                        embedder_config={
                            "provider": "openai",
                            "config": {
                                "model": 'text-embedding-3-small'
                            }
                        },
                        type="short_term",
                        path="./memory/"
                    )
                ),            # Entity memory for tracking key information about entities
            entity_memory = EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": 'text-embedding-3-small'
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
        )

