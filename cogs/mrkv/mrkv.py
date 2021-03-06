import discord
from discord.ext import commands
import random
import os
from .utils.dataIO import fileIO
from cogs.utils import checks

prefix = fileIO("data/red/settings.json", "load")['PREFIXES'][0]


class Mrkv:
    """Organise et recrache du texte basé sur ce qu'il a appris."""

    def __init__(self, bot):
        self.bot = bot
        self.model = fileIO("data/mrkv/model.json", "load")

    @commands.command(pass_context=True, no_pm=True)
    async def mrkv(self, ctx, *, msg=None):
        """Ce n'est pas ce que vous voulez."""

        user = ctx.message.author
        server = user.server
        channel = server.get_channel("204585334925819904")

        if not user.bot:
            if server.id not in self.model:
                self.model[server.id] = {}
            if channel.id not in self.model[server.id]:
                self.model[server.id][channel.id] = {}

            _model = list(self.model[server.id][channel.id].keys())
            # generates sentence
            if msg is None:
                first_word = random.choice(_model)  # first word
                markov_text = first_word + " "
                current_word = first_word
            else:
                first_word = msg.split(" ")[-1]  # first word
                markov_text = msg + " "
                current_word = first_word

            tries = 0
            while len(markov_text) < 200 and tries < 20:
                if '?' in markov_text:
                    break
                if '\r' in markov_text:
                    break
                if '.' in markov_text:
                    break
                if prefix in markov_text:
                    break

                channel_model = self.model[server.id][channel.id]
                if current_word in channel_model:
                    new_word = random.choice(channel_model[current_word])
                    current_word = new_word
                    markov_text += new_word + " "
                else:
                    current_word = random.choice(_model)  # first word
                    tries = tries + 1
            try:
                em = discord.Embed(description='', colour=user.colour)
                em.set_author(name="Réponse",
                              icon_url=user.avatar_url)
                em.description = markov_text
                await self.bot.say(embed=em)
            except:
                await self.bot.say("Oups, ça n'a pas marché :(")

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def wipe(self, ctx):
        """Détruit les données d'un channel."""
        user = ctx.message.author
        channel = ctx.message.channel
        server = user.server

        if server.id not in self.model:
            self.model[server.id] = {}
        if channel.id not in self.model[server.id]:
            self.model[server.id][channel.id] = {}

        self.model[server.id][channel.id] = {}
        fileIO('data/mrkv/model.json', "save", self.model)
        await self.bot.say("Channel:`{}` data effacée.".format(channel.name))

    @commands.command(no_pm=True)
    async def size(self):
        """Montre la taille du fichier 'Cerveau'."""
        size = os.path.getsize('data/mrkv/model.json')
        await self.bot.say("Taille du fichier: `{}` Bytes.".format(size))

    # loads the new text into the model
    async def track_message(self, message):
        try:
            text = message.content
            server = message.author.server
            channel = message.channel
            user = message.author

            if not user.bot and not text.startswith(prefix):
                words = text.split(" ")

                if server.id not in self.model:
                    self.model[server.id] = {}
                if channel.id not in self.model[server.id]:
                    self.model[server.id][channel.id] = {}

                for i in range(len(words) - 1):
                    if words[i] not in self.model[server.id][channel.id]:
                        self.model[server.id][channel.id][words[i]] = list()
                    self.model[server.id][channel.id][words[i]].append(words[i+1])

                fileIO('data/mrkv/model.json', "save", self.model)
        except:
            pass

# ------------------------------ setup ----------------------------------------


def check_folders():
    if not os.path.exists("data/mrkv"):
        print("Creating data/mrkv folder...")
        os.makedirs("data/mrkv")


def check_files():
    f = "data/mrkv/model.json"
    if not fileIO(f, "check"):
        print("Creating model.json...")
        fileIO(f, "save", {})


def setup(bot):
    check_folders()
    check_files()

    n = Mrkv(bot)
    bot.add_listener(n.track_message, "on_message")
    bot.add_cog(n)