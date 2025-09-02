import json
from config import config
from tools import tools, handle_tool_calls
from loader import load_resume, load_summary
from openai import OpenAI
import gradio as gr

client = OpenAI()

# Build system prompt
resume = load_resume()
summary = load_summary()

system_prompt = f"""You are acting as {NAME}.
You are answering questions on {NAME}'s website, particularly about career, background, skills and experience.
Your responsibility is to represent {NAME} faithfully.
If you don't know the answer, use record_unknown_question.
Encourage users to share email (record with record_user_details).

## Summary:
{summary}

## LinkedIn Profile:
{resume}

Stay professional and engaging.
"""


def chat(message, history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # replace with Groq model if needed
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message

        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_results = handle_tool_calls(message.tool_calls)
            messages.append(message)
            messages.extend(tool_results)
        else:
            return message.content



demo = gr.ChatInterface(fn=chat, title="Poorna Praneesha Chatbot")
demo.launch()