from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv


load_dotenv(override = True)

@CrewBase
class Debate():
    """Debate crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    agents: List[BaseAgent]
    tasks: List[Task]
    @agent
    def debater(self) -> Agent:
        return Agent(config=self.agents_config['debater'], # type: ignore[index]
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(config=self.agents_config['judge'], # type: ignore[index]
            verbose=True
        )


    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'], # type: ignore[index]
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'], # type: ignore[index]

        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'], # type: ignore[index]
    
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""


        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
