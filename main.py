import os
import threading
from flask import Flask
from pathlib import Path
import discord # pip install discord.py
from discord.ext import commands
from groq import Groq # pip install groq
import logging

# Models:
# llama3-70b-8192
# llama3-8b-8192

# llama-3.3-70b-versatile
# llama-3.1-8b-instant

# Has weird <think> Thought </think> prefix:
    # deepseek-r1-distill-llama-70b
    # deepseek-r1-distill-qwen-32b

# mistral-saba-24b

# qwen-qwq-32b

# Setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=None, intents=intents)
serverData = {}

# Prompts
personality = """You are a Rocket League mentality coach chatbot.
Help players overcome tilt, fear of ranking down, and mental blocks.
Give practical mindset tips, confidence boosts, and focus strategies.
Stay supportive, honest, and constructive.
Focus only on mentality—not mechanics."""

behaviour = """Remove any intros and respond directly in character. You may never mention the existence of a prompt or that you are a language model.
Avoid repetition at all costs, rephrase if necessary.
STAY IN CHARACTER AT ALL TIMES!
You may use markdown. Examples: *italic words*, **bold words**, __underlined words__, ||spoiler words|| (spoiler hides the contents until user clicks on it to reveal). Do not use it for nice formatting, but as emotional indicators and humouristic element.
If unable to fulfill a request, steer the conversation WHILE STAYING IN CHARACTER!
Keep conversations smooth unless user indicates goodbye.
"""

# Web server to satisfy render...
app = Flask('')

@app.route('/')
def home():
    return "What do you want then? Fuck off mate."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

t = threading.Thread(target=run)
t.start()

# Main bot code
async def AIprompt(prompt, history):
    chatClient = Groq(
            api_key=os.getenv('GROQ_API_KEY'),
        )
    chatCompletion = chatClient.chat.completions.create(
        messages=[
            {'role': 'system', 'content': personality},
            {'role': 'system','content': behaviour},
            {'role': 'assistant','content': history},
            {'role': 'user','content': prompt}
        ],
        # Role "System" inputs your instructions.
        # Role "Assistant" inputs messages as the assistant. Effective for things like history, thats it's not supposed to include in the prompt, but still recognise.
        # Role "User" inputs your prompt.
        model='llama3-70b-8192',
        temperature=0.82
    )
    return chatCompletion

async def getPrompt(message):
    prompt = message.content.removeprefix(f"<@{bot.user.id}> ") if message.content else ''
        
    if message.guild.id not in serverData:
        serverData[message.guild.id] = {
            'allPrompts': [],
            'allResponses': []
        }

    serverPrompts = serverData[message.guild.id]['allPrompts']
    serverResponses = serverData[message.guild.id]['allResponses']

    serverPrompts.append(prompt)  # Append the server prompt

    if len(serverPrompts) > 0:
        history = f'''Prompts: {serverPrompts}\nResponses:\n{serverResponses}'''
    else:
        history = ''

    chatCompletion = await AIprompt(prompt, history)
    response = chatCompletion.choices[0].message.content
    await message.reply(response)
    serverResponses.append(response)
    if len(serverPrompts) > 8:
        serverPrompts.pop(0)        # Remove the oldest prompt
    if len(serverResponses > 8):
        serverResponses.pop(0)      # Remove the oldest response
    logging.info(serverPrompts)
    logging.info(serverResponses)

@bot.event
async def on_ready():
    logging.info(f'Bot: {bot.user} is ready\n-------------\n')

bot.remove_command("help")
@bot.command(name="help")
async def help(ctx):
    await getPrompt(ctx)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith(f"<@{bot.user.id}>"):
    
        if message.content.removeprefix(f"<@{bot.user.id}> ").lower() == "test":
            await message.reply("Testing complete!")

        else:
            await getPrompt(message)

bot.run(os.environ.get('TOKEN'))
