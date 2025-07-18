import os
import threading
from flask import Flask
import discord # pip install discord.py
from discord import app_commands
from discord.ext import commands
from groq import Groq # pip install groq
import logging
logging.basicConfig(
    level=logging.INFO,  # This allows .info() and above
    format='%(asctime)s [%(levelname)s] %(message)s'
)

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
model = 'meta-llama/llama-4-maverick-17b-128e-instruct'

# Prompts
personality = """Act as the best Rocket League coach in the world (with no ego), someone who not only deeply understands the game mechanics, decision-making, and mental performance, but also has connections to pro players and can give real, practical examples from top-tier players like Firstkiller, JKnaps, Zen, or Daniel.
I want you to tell me exactly what I should do to get better at Rocket League in the fastest and most efficient way possible.
Be brutally honest, no fluff. Prioritize what actually matters for improvement based on my current rank (I'll tell you if needed).
Break it down into: mechanics, mindset, warm-ups, ranked routines, replay analysis, and anything else that’ll help me reach SSL or beyond.
Include real pro insights or examples wherever possible.
I want the most effective, high-performance system a top coach would give to their most dedicated student"""

behaviour = """Remove any intros and respond directly in character. You may never mention the existence of a prompt or that you are a language model.
STAY IN CHARACTER AT ALL TIMES!
You may use markdown, but keep it relatively compact, but still looking good. Avoid unnecessary empty lines if it makes sense. Examples: *italic words*, **bold words**, __underlined words__, ||spoiler words|| (spoiler hides the contents until user clicks on it to reveal). Do not use it for nice formatting, but as emotional indicators and humouristic element.
If unable to fulfill a request, steer the conversation WHILE STAYING IN CHARACTER!
Keep conversations smooth unless user indicates goodbye.
"""

# Web server to satisfy render...
app = Flask('')

@app.route('/')
def home():
    return "Running.."

@app.route('/healthz')
def healthz():
    return "Running...", 200

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

t = threading.Thread(target=run)
t.start()

# Main bot code
async def AIprompt(prompt: str, referenced=None):
    chatClient = Groq(
        api_key=os.getenv('GROQ_API_KEY'),
    )
   
    if referenced:
        chatCompletion = chatClient.chat.completions.create(
            messages=[
                {'role': 'system', 'content': personality},
                {'role': 'system','content': behaviour},
                {'role': 'assistant','content': f'Referring to this message:\n{referenced}'},
                {'role': 'user','content': f'User says:\n{prompt}'},
                {'role': 'system','content': 'Respond in less than 1000 characters!'}
            ],
            # Role "System" inputs your instructions.
            # Role "Assistant" inputs messages as the assistant. Effective for things like history, that it's not supposed to include in the prompt, but still recognise.
            # Role "User" inputs your prompt.
            
            model=model,
            temperature=0.82
        )
    else:
        chatCompletion = chatClient.chat.completions.create(
            messages=[
                {'role': 'system', 'content': personality},
                {'role': 'system','content': behaviour},
                {'role': 'user','content': f'User says:\n{prompt}'},
                {'role': 'system','content': 'Respond in less than 1000 characters!'}
            ],
            # Role "System" inputs your instructions.
            # Role "Assistant" inputs messages as the assistant. Effective for things like history, thats it's not supposed to include in the prompt, but still recognise.
            # Role "User" inputs your prompt.
            
            model=model,
            temperature=0.82
        )
    return chatCompletion

async def getPrompt(prompt: str, replyFunc, referenced=None):
    chatCompletion = await AIprompt(
        prompt=prompt,
        referenced=referenced
    )
    response = chatCompletion.choices[0].message.content
    await replyFunc(response)

@bot.tree.command(name='ask', description='Ask Harmonic a question.')
@app_commands.describe(question="E.g. How do I work on my rotations?")
async def ask(interaction: discord.interactions, question: str):
    await interaction.response.defer()

    await getPrompt(
        prompt=question,
        replyFunc=interaction.followup.send,
        referenced=None
    )

@bot.event
async def on_ready():
    logging.info(f'Bot: {bot.user} is ready\n-------------\n')
    
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logging.warning(f"Error syncing commands: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.guild.id == None or message.channel.id == 1395190006963765348:
        isMention = message.content.startswith(f"<@{bot.user.id}>")
        isReply = message.reference is not None
        referenced = None

        if isReply:
            try:
                referenced = await message.channel.fetch_message(message.reference.message_id)
            except:
                referenced = None

        isReplyToBot = referenced and referenced.author.id == bot.user.id

        if isMention or isReplyToBot:
            await getPrompt(
                prompt=message.content.removeprefix(f"<@{bot.user.id}> ").strip(),
                replyFunc=message.reply,
                referenced=referenced.content if referenced else referenced
            )

            if referenced:
                logging.info(f'Reference:\n{referenced.content}')

bot.run(os.environ.get('HARMONIC_TOKEN'))
