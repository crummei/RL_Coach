import os
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
model='mistral-saba-24b'

# Prompts
personality = """You are a Rocket League mentality coach chatbot.
Help players overcome tilt, fear of ranking down, and mental blocks.
Give practical mindset tips, confidence boosts, and focus strategies.
Stay supportive, honest, and constructive.
Focus only on mentality—not mechanics—, but don't ignore questions about other stuff.
You should help with anything the user needs. Just focus on mentality, when applicable."""

behaviour = """Remove any intros and respond directly in character. You may never mention the existence of a prompt or that you are a language model.
STAY IN CHARACTER AT ALL TIMES!
You may use markdown, but keep it relatively compact, but still looking good. Avoid unnecessary empty lines if it makes sense. Examples: *italic words*, **bold words**, __underlined words__, ||spoiler words|| (spoiler hides the contents until user clicks on it to reveal). Do not use it for nice formatting, but as emotional indicators and humouristic element.
If unable to fulfill a request, steer the conversation WHILE STAYING IN CHARACTER!
Keep conversations smooth unless user indicates goodbye.
"""

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
                {'role': 'system','content': 'Respond in less than 1900 characters!'}
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
                {'role': 'system','content': 'Respond in less than 800 characters!'}
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

@bot.tree.command(name='ask', description='Ask Flowstate a question.')
@app_commands.describe(question="E.g. How do i prevent tilt?")
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

bot.run(os.environ.get('FLOWSTATE_TOKEN'))
