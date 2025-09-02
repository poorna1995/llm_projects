# write the answer for the qiery


from config import INSTRUCTIONS_WRITER,ReportData
from agent import Agent

def writer_agent():
    return Agent(
        name="WriterAgent",
        instructions=WRITER.INSTRUCTION_WRITER,
        model=MODEL_NAME,
        output_type=ReportData,
    )