import asyncio
import os
from .utils import checks
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
from .utils.dataIO import fileIO, dataIO


class EgoAPI:
    """EgoAPI V3 | Fournisseur de statistiques et de services personnalisés"""
    def __init__(self, bot, path):
        self.bot = bot
        self.data = dataIO.load_json(path)
        self.old = dataIO.load_json("data/ego/profil.json")

    def save(self, backup=False):
        if backup:
            if "data.json" in os.listdir("data/ego/backup/"):
                if os.path.getsize("data/ego/backup/data.json") < os.path.getsize("data/ego/data.json"):
                    fileIO("data/ego/backup/data.json", "save", self.data)
                else:
                    print("ATTENTION: EGO n'a pas réalisé de backup car le fichier source est moins "
                          "volumineux que le dernier fichier backup. Un problème à pu se produire dans les données...")
            else:
                fileIO("data/ego/backup/data.json", "save", self.data)
        fileIO("data/ego/data.json", "save", self.data)
        return True

    def open(self, user):
        if user.id not in self.data:
            if user.id in self.old:
                self.data[user.id] = {"STATS": {},
                                      "SERVICES": {},
                                      "HISTORY": self.old[user.id]["HISTO"],
                                      "JEUX": self.old[user.id]["STATS"]["JEUX"] if "JEUX" in
                                                                                    self.old[user.id]["STATS"] else [],
                                      "CREATION": self.old[user.id]["BORN"]}
                if "SITE" in self.old[user.id]["PERSO"]:
                    self.data[user.id]["SERVICES"]["SITE"] = self.old[user.id]["PERSO"]["SITE"]
                if "PSEUDOS" in self.old[user.id]["STATS"]:
                    self.data[user.id]["STATS"]["PSEUDOS"] = self.old[user.id]["STATS"]["PSEUDOS"]
                if "D_PSEUDOS" in self.old[user.id]["STATS"]:
                    self.data[user.id]["STATS"]["D_PSEUDOS"] = self.old[user.id]["STATS"]["D_PSEUDOS"]
            else:
                self.data[user.id] = {"STATS": {},
                                      "SERVICES": {},
                                      "HISTORY": [],
                                      "JEUX": [],
                                      "CREATION": time.time()}
            self.save()
            self.new_event(user, "autre", "Inscrit sur EGO V3")
        Profil = namedtuple('Profil', ["stats", "services", "history", "jeux", "creation"])
        a = self.data[user.id]["STATS"]
        b = self.data[user.id]["SERVICES"]
        c = self.data[user.id]["HISTORY"]
        d = self.data[user.id]["JEUX"]
        e = self.data[user.id]["CREATION"]
        return Profil(a, b, c, d, e)

    def new_event(self, user, type_event: str, descr: str):
        types = ["punition", "nom", "role", "autre", "immigration"]
        if type_event in types:
            if len(descr) > 30:
                descr = descr[:30] + "..."
            ego = self.open(user)
            jour = time.strftime("%d/%m/%Y", time.localtime())
            heure = time.strftime("%H:%M", time.localtime())
            ego.history.append([heure, jour, type_event, descr])
            return True
        else:
            print("Impossible de créer un nouvel évenement pour {} (EventNotInList)".format(str(user)))
            return False

    def since(self, user, format=None):
        ego = self.open(user)
        s = time.time() - ego.creation
        sm = s / 60  # en minutes
        sh = sm / 60  # en heures
        sj = sh / 24  # en jours
        sa = sj / 364.25  # en années
        if format == "année":
            return int(sa) if sa > 0 else 0.1
        elif format == "jour":
            return int(sj) if sj > 0 else 1
        elif format == "heure":
            return int(sh) if sh > 0 else 1
        elif format == "minute":
            return int(sm) if sm > 0 else 1
        else:
            return int(s) if s > 0 else 1

    def stat_color(self, user):
        s = user.status
        if not user.bot:
            if s == discord.Status.online:
                return 0x43B581 #Vert
            elif s == discord.Status.idle:
                return 0xFAA61A #Jaune
            elif s == discord.Status.dnd:
                return 0xF04747 #Rouge
            else:
                return 0x9ea0a3 #Gris
        else:
            return 0x2e6cc9 #Bleu

    def jeux_verif(self):
        verif = []
        dispo = []
        for p in self.data:  # On sort une liste des jeux vérifiés
            if self.data[p]["JEUX"]:
                for g in self.data[p]["JEUX"]:
                    if g not in verif:
                        verif.append(g)
                    else:
                        if g not in dispo:
                            dispo.append(g)
        return dispo

    def biblio(self, user):
        pot = self.open(user).jeux
        liste = self.jeux_verif()
        if pot.jeux:
            poss = []
            for g in pot.jeux:
                if g.lower() in liste:
                    poss.append(g)
            return poss if poss else False
        return False

    def affinite(self, auteur, user):
        liste = [[self.data[user.id]["MENTIONS"][r], r] for r in self.data[user.id]["MENTIONS"]]
        liste = sorted(liste, key=operator.itemgetter(0), reverse=True)
        if auteur.id == liste[0][1]:
            return "Meilleur ami(e)"
        elif auteur.id in [i[1] for i in liste[:3]]:
            return "Très forte"
        elif auteur.id in [i[1] for i in liste[:5]]:
            return "Forte"
        elif auteur.id in [i[1] for i in liste[:20]]:
            return "Moyenne"
        else:
            return "Faible"

    def leven(self, s1, s2):
        if len(s1) < len(s2):
            m = s1
            s1 = s2
            s2 = m
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[
                                 j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def find_m(self, content): # Retrouve les mentions indirectes
        listm = []
        for e in content:
            for p in self.bot.get_all_members():
                ego = self.open(p)
                if self.leven(p.name.lower(), e.lower()) <= 1:
                    if p.id not in listm:
                        listm.append(p.id)
                elif self.leven(p.display_name.lower(), e.lower()) <= 1:
                    if p.id not in listm:
                        listm.append(p.id)
                elif "SURNOM" in ego.services:
                    if e.lower() == ego.services["SURNOM"].lower():
                        if p.id not in listm:
                            listm.append(p.id)
                else:
                    pass
        return listm

    def find_pseudo(self, term: str):
        possible = []
        for p in self.data:
            if "PSEUDOS" in self.data[p]["STATS"]:
                for i in self.data[p]["STATS"]["PSEUDOS"]:
                    if term.lower() in i.lower():
                        possible.append([p, i])
            if "D_PSEUDOS" in self.data[p]["STATS"]:
                for i in self.data[p]["STATS"]["D_PSEUDOS"]:
                    if term.lower() in i.lower():
                        if p not in possible:
                            possible.append([p, i])
        return possible if possible else False


class Ego:
    """Ego V3 | Fournisseur de statistiques et de services personnalisés"""
    def __init__(self, bot):
        self.bot = bot
        self.ego = EgoAPI(bot, "data/ego/data.json")
        self.glb = dataIO.load_json("data/ego/glb.json")
        self.version = "EGO V3 (&majs)"
        self.logo_url = "http://i.imgur.com/nmJH3Zf.png"
        self.cycle_task = bot.loop.create_task(self.ego_loop())

    @commands.command(name="majs", pass_context=True)
    async def changelog(self):
        """Informations sur les MAJ de Ego et des modules auxilliaires."""
        em = discord.Embed(title="EGO V3.0 | Voir Github",color=0x5184a5, url="https://github.com/GitAcrown/Addon/issues/3")
        em.add_field(name="&card",
                     value="+ Activité écrite et vocale par membre\n"
                           "+ Affinité avec le membre\n"
                           "+ L'historique est désormais journalier et horodaté\n"
                           "+ Possibilité de refresh les informations\n"
                           "+ Le code de l'invitation s'affiche dans l'historique\n"
                           "+ Nouvel affichage en menu"
                           "+ Anciens pseudos et surnoms")
        em.add_field(name="&global",
                     value="*(Fusion de stats et scard)*\n"
                           "+ Temps de vocal et parole total (TTV & TTP)\n"
                           "+ Possibilité de refresh les informations\n"
                           "+ Nouvel affichage en menu")
        em.add_field(name="Système",
                     value="+ Meilleure détection des pseudos non-mentionnés\n"
                           "+ Capacité à surveiller les invitations\n"
                           "+ Plus grande précision dans le comptage de personnes en vocal\n"
                           "+ Comptage du temps de parole/vocal à la seconde près pour chaque membre\n"
                           "+ Classement des messages par channel\n"
                           "+ Détection connexion/déconnexion\n"
                           "+ Système de Rollback en cas de données corrompues\n"
                           "- Les commandes ne sont plus considérées comme des messages\n"
                           "- Le rôle prison n'est plus considéré comme un rôle supérieur aux rôles honorifiques")
        em.add_field(name="Bientôt",
                     value="+ Recherche de jeux\n"
                           "+ Compilation de 'Tops' (Top actifs, e-pop, temps de parole...)\n"
                           "+ Créer et gérer des groupes de jeu\n"
                           "+ Créer et gérer des évenements\n"
                           "+ Rappels personnalisés\n"
                           "+ Personnalisation (Bio, Anniversaire, Surnom)\n"
                           "+ Projet Oracle (Voir Github en cliquant plus haut)")
        em.set_footer(text="MAJ publiée le 22/08 | Début de la récolte de stats V3: 22/08/2017", icon_url=self.logo_url)
        await self.bot.say(embed=em)

    @commands.command(name="global", pass_context=True, no_pm=True)
    async def _global(self, ctx):
        """Affiche des informations et des statistiques sur le serveur."""
        server = ctx.message.server
        today = time.strftime("%d/%m/%Y", time.localtime())
        rewind = 0
        menu = None
        futur = False
        while True:
            if rewind == 0:
                date = today
            elif rewind > 0:
                date = time.strftime("%d/%m/%Y",
                                    time.localtime(time.mktime(time.strptime(today, "%d/%m/%Y")) - (86400 * rewind)))
            else:
                rewind += 1
                date = time.strftime("%d/%m/%Y",
                                     time.localtime(time.mktime(time.strptime(today, "%d/%m/%Y")) - (86400 * rewind)))
                futur = True
            if date in self.glb["DATES"]:
                em = discord.Embed(title="EGO Data | **{}**".format(date if date != today else "Aujourd'hui"))
                em.set_thumbnail(url=server.icon_url)
                if futur:
                    em.set_footer(text="Impossible d'aller dans le futur pour le moment ¯\_(ツ)_/¯",
                                  icon_url=self.logo_url)
                    await self.bot.edit_message(menu, embed=em)
                    await asyncio.sleep(1)
                    futur = False
                salons = ""
                if "CHANNEL_MSG" in self.glb["DATES"][date]:
                    for e in self.glb["DATES"][date]["CHANNEL_MSG"]:
                        channel = self.bot.get_channel(e)
                        salons += "**{}:** {}\n".format(channel.name, self.glb["DATES"][date]["CHANNEL_MSG"][e])
                    msgs = "{}\n" \
                          "**Total:** {}\n" \
                          "**Sans bot:** {}".format(salons, self.glb["DATES"][date]["TOTAL_MSG"],
                                                     self.glb["DATES"][date]["TOTAL_MSG"] -
                                                     self.glb["DATES"][date]["BOT_TOTAL_MSG"])
                    em.add_field(name="Messages", value=msgs)
                if "HORO_ECRIT" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["HORO_ECRIT"] = {}
                if "HORO_VOCAL_ACTIF" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["HORO_VOCAL_ACTIF"] = {}
                if "TOTAL_VOCAL" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["TOTAL_VOCAL"] = 0
                if "TOTAL_PAROLE" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["TOTAL_PAROLE"] = 0
                #TODO Enlever cette (^) sécurité après quelques jours...
                elb = []  # Ecrit ---
                totalelb = 0
                act_ecr = act_voc = ""
                for heure in self.glb["DATES"][date]["HORO_ECRIT"]:
                    elb.append([int(heure), (int(heure) + 1), self.glb["DATES"][date]["HORO_ECRIT"][heure]])
                    totalelb += self.glb["DATES"][date]["HORO_ECRIT"][heure]
                top = sorted(elb, key=operator.itemgetter(2), reverse=True)
                top = top[:5]
                for c in top:
                    pourc = (c[2] / totalelb) * 100
                    act_ecr += "**[{};{}[:** {}%\n".format(c[0], c[1], round(pourc, 2))
                elb = []  # Vocal ---
                totalelb = 0
                for heure in self.glb["DATES"][date]["HORO_VOCAL_ACTIF"]:
                    elb.append([int(heure), (int(heure) + 1), self.glb["DATES"][date]["HORO_VOCAL_ACTIF"][heure] / 2])
                    totalelb += self.glb["DATES"][date]["HORO_ECRIT"][heure] / 2
                top = sorted(elb, key=operator.itemgetter(2), reverse=True)
                top = top[:5]
                for c in top:
                    pourc = (c[2] / totalelb) * 100
                    act_voc += "**[{};{}[:** {}%\n".format(c[0], c[1], round(pourc, 2))
                ttv = self.glb["DATES"][date]["TOTAL_VOCAL"]  # secondes
                ttp = self.glb["DATES"][date]["TOTAL_PAROLE"]  # secondes
                for p in server.members:
                    ego = self.ego.open(p)
                    if "CAR_VOCAL" in ego.stats:
                        if ego.stats["CAR_VOCAL"] > 0:
                            ttv += ego.stats["CAR_VOCAL"]
                    if "CAR_PAROLE" in ego.stats:
                        if ego.stats["CAR_PAROLE"] > 0:
                            ttp += ego.stats["CAR_PAROLE"]
                ttv /= 1440  # heures
                ttp /= 1440  # heures
                acts = "**__Écrit__**\n" \
                      "{}\n" \
                      "**__Vocal__**\n" \
                      "{}\n" \
                      "**TTV:** {}\n" \
                      "**TTP:** {}\n".format(act_ecr, act_voc, round(ttv, 2), round(ttp, 2))
                em.add_field(name="Activité", value=acts)
                min_ = self.glb["DATES"][date]["TOTAL_JOIN"] if "TOTAL_JOIN" in self.glb["DATES"][date] else 0
                mre_ = self.glb["DATES"][date]["TOTAL_RETOUR"] if "TOTAL_RETOUR" in self.glb["DATES"][date] else 0
                mem_ = self.glb["DATES"][date]["TOTAL_QUIT"] if "TOTAL_QUIT" in self.glb["DATES"][date] else 0
                migra = "**Immigrants:** {}\n" \
                        "**Dont revenants:** {}\n" \
                        "**Émigrants:** {}\n" \
                        "**Solde:** {}".format(min_, mre_, mem_, (min_ - mem_))
                em.add_field(name="Flux migratoire", value=migra)
                em.set_footer(text="Utilisez les réactions ci-dessous pour naviguer | {}".format(self.version),
                              icon_url=self.logo_url)
            else:
                em = discord.Embed(title="EGO Data | **{}**".format(date if date != today else "Aujourd'hui"),
                                   description= "Aucune donnée pour ce jour.")
                em.set_thumbnail(url=server.icon_url)

            if menu is None:
                menu = await self.bot.say(embed=em)
            else:
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                menu = await self.bot.edit_message(menu, embed=em)
            await self.bot.add_reaction(menu, "⬅")
            await self.bot.add_reaction(menu, "⏬")
            if rewind > 0:
                await self.bot.add_reaction(menu, "➡")
            if rewind == 0:
                await self.bot.add_reaction(menu, "🔄")
                await self.bot.add_reaction(menu, "ℹ")
            act = await self.bot.wait_for_reaction(["⬅", "⏬", "➡", "🔄", "ℹ"], message=menu, timeout=60,
                                                   check=self.check)
            if act is None:
                em.set_footer(text="Session expirée | {}".format(self.version), icon_url=self.logo_url)
                await self.bot.edit_message(menu, embed=em)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                return
            elif act.reaction.emoji == "⬅":
                rewind += 1
            elif act.reaction.emoji == "⏬":
                em.set_footer(text="Entrez la date désirée ci-dessous (dd/mm/aaaa) | {}".format(self.version),
                              icon_url=self.logo_url)
                await self.bot.edit_message(menu, embed=em)
                rep = await self.bot.wait_for_message(author=act.user, channel=menu.channel, timeout=30)
                if rep is None:
                    em.set_footer(text="Timeout | Retour",
                                  icon_url=self.logo_url)
                    await self.bot.edit_message(menu, embed=em)
                    await asyncio.sleep(0.5)
                elif len(rep.content) == 10:
                    rewind += int((time.mktime(time.strptime(date, "%d/%m/%Y")) - time.mktime(
                        time.strptime(rep.content, "%d/%m/%Y"))) / 86400)
                    try:
                        await self.bot.delete_message(rep)
                    except:
                        pass
                else:
                    em.set_footer(text="Invalide | Retour".format(self.version),
                                  icon_url=self.logo_url)
                    await self.bot.edit_message(menu, embed=em)
                    await asyncio.sleep(0.5)
            elif act.reaction.emoji == "➡" and rewind > 0:
                rewind -= 1
            elif act.reaction.emoji == "🔄" and rewind == 0:
                continue
            elif act.reaction.emoji == "ℹ" and rewind == 0:
                online = str(len([m.status for m in server.members if
                                  str(m.status) == "online" or str(m.status) == "idle" or str(m.status) == "dnd"]))
                total_users = str(len(server.members))
                em = discord.Embed(title="EGO Data | {}".format(server.name), color=ctx.message.author.color)
                em.add_field(name="ID", value="{}".format(server.id))
                em.add_field(name="Région", value="{}".format(server.region))
                em.add_field(name="Propriétaire", value="{}".format(server.owner))
                em.add_field(name="Nb membres", value="**{}**/{}".format(online, total_users))
                passed = (ctx.message.timestamp - server.created_at).days
                em.add_field(name="Age", value="{} jours".format(passed))
                em.set_thumbnail(url=server.icon_url)
                em.set_footer(text="Utilisez la réaction ci-dessous pour retourner au menu | {}".format(
                    self.version), icon_url=self.logo_url)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                await self.bot.edit_message(menu, embed=em)
                retour = await self.bot.wait_for_reaction(["⏹"], message=menu, timeout=60, check=self.check)
                if retour is None:
                    em.set_footer(text="Session expirée | {}".format(self.version), icon_url=self.logo_url)
                    await self.bot.edit_message(menu, embed=em)
                    return
                elif retour.reaction.emoji == "⏹":
                    continue
                else:
                    pass
            else:
                em.set_footer(text="Réaction invalide | {}".format(self.version), icon_url=self.logo_url)
                await self.bot.edit_message(menu, embed=em)
                return

    @commands.command(aliases=["carte", "c"], pass_context=True)
    async def card(self, ctx, user: discord.Member = None):
        """Affiche les informations détaillées d'un membre."""
        if user is None: user = ctx.message.author
        menu = None
        while True:
            ego = self.ego.open(user)
            color = self.ego.stat_color(user)
            date = time.strftime("%d/%m/%Y", time.localtime())
            em = discord.Embed(title="{}".format(str(user) if user != ctx.message.author else "Votre profil"),
                               color=color)
            em.set_thumbnail(url=user.avatar_url)
            if user.display_name.lower() != user.name.lower():
                em.add_field(name="Pseudo", value=user.display_name)
            em.add_field(name="ID", value=user.id)
            passed = (ctx.message.timestamp - user.created_at).days
            em.add_field(name="Création", value=str(passed) + " jours")
            passed = (ctx.message.timestamp - user.joined_at).days
            rpas = passed if passed >= self.ego.since(user, "jour") else "+" + passed
            em.add_field(name="Ancienneté", value=rpas + " jours")
            ecr = round(ego.stats["NB_MSG"] / self.ego.since(user, "jour")) if "NB_MSG" in ego.stats else 0
            if "TOTAL_PAROLE" in ego.stats:
                if "TOTAL_VOCAL" in ego.stats:
                    hvoc = round(ego.stats["TOTAL_PAROLE"] + ego.stats["TOTAL_VOCAL"] + ego.stats["CAR_PAROLE"]
                                 + ego.stats["CAR_VOCAL"]) * 3600
                    voc = hvoc / self.ego.since(user, "jour")
                else:
                    voc = 0
            else:
                voc = 0
            act = "**Écrit:** {}msg/j\n" \
                  "**Vocal:** {}h/j".format(ecr, voc)
            em.add_field(name="Activité", value=act)
            rolelist = " ,".join([r.name for r in user.roles if r.name != "@everyone"])
            em.add_field(name="Rôles", value=rolelist)
            em.add_field(name="Auparavant", value="**Pseudos:** {}\n**Surnoms:** {}".format(" ,".join(
                ego.stats["PSEUDOS"][:3]), " ,".join(ego.stats["D_PSEUDOS"][:3])))
            liste = []
            for e in ego.history:
                if e[1] == date:
                    mel = "{} {}".format(e[0], e[1])
                    sec = time.mktime(time.strptime(mel, "%H:%M %d/%m/%Y"))
                    liste.append([sec, e[0], e[1], e[2], e[3]])
            if liste:
                msg = ""
                order = sorted(liste, key=operator.itemgetter(0), reverse=True)
                top = order[:3]
                for t in top:
                    msg += "**{}** *{}*\n".format(t[1], t[4])
            else:
                msg = "*Aucune action*"
            em.add_field(name="Aujourd'hui", value=msg)
            if ctx.message.author != user:
                em.add_field(name="Affinité", value=self.ego.affinite(ctx.message.author, user))
            em.set_footer(text="Utilisez les réactions ci-dessous pour naviguer | {}".format(self.version),
                          icon_url=self.logo_url)
            if menu is None:
                menu = await self.bot.say(embed=em)
            else:
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                menu = await self.bot.edit_message(menu, embed=em)
            await self.bot.add_reaction(menu, "🕹")  # Jeux
            if user == ctx.message.author:
                await self.bot.add_reaction(menu, "⚙")
            await self.bot.add_reaction(menu, "🔄")  # Refresh
            rap = await self.bot.wait_for_reaction(["🕹", "🔄", "⚙"], message=menu, timeout=60, check=self.check)
            if rap is None:
                em.set_footer(text="Session expirée | {}".format(self.version), icon_url=self.logo_url)
                await self.bot.edit_message(menu, embed=em)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                return
            elif rap.reaction.emoji == "⚙" and user == ctx.message.author:
                await self.bot.whisper("**Fonctionnalité en cours de développement !**\n"
                                       "Bientôt: \n"
                                       "+ Ajout d'une petite bio à votre carte\n"
                                       "+ Ajout de la date de votre anniversaire\n"
                                       "+ Ajout d'un surnom\n"
                                       "+ Ajout d'un site web personnel")
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                return
            elif rap.reaction.emoji == "🕹":
                aff = ""
                if ctx.message.author != user:
                    selfbib = self.ego.biblio(ctx.message.author)
                    userbib = self.ego.biblio(user)
                    if userbib:
                        for g in userbib:
                            if g.lower() in selfbib:
                                aff += "__*{}*__\n".format(g.title())
                            else:
                                aff += "*{}*\n".format(g.title())
                    else:
                        aff = "???"
                    em = discord.Embed(
                        title="Jeux de {}".format(user.name) if user != ctx.message.author else "Vos jeux",
                        color=color, description=aff)
                    resul = "Les jeux en commun sont soulignés" if userbib else "Bibliothèque vide " \
                                                                                       "ou non detectée"
                    em.set_footer(text="{} | {}".format(resul, self.version), icon_url=self.logo_url)
                else:
                    selfbib = self.ego.biblio(ctx.message.author)
                    if selfbib:
                        for g in selfbib:
                            aff += "*{}*\n".format(g.title())
                    else:
                        aff = "???"
                    em = discord.Embed(
                        title="Jeux de {}".format(user.name) if user != ctx.message.author else "Vos jeux",
                        color=color, description=aff)
                    resul = "Utilisez la réaction ci-dessous pour revenir à votre profil" if \
                        selfbib else "Bibliothèque vide ou non detectée"
                    em.set_footer(text="{} | {}".format(resul, self.version), icon_url=self.logo_url)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                await self.bot.edit_message(menu, embed=em)
                retour = await self.bot.wait_for_reaction(["⏹"], message=menu, timeout=60, check=self.check)
                if retour is None:
                    em.set_footer(text="Session expirée | {}".format(self.version), icon_url=self.logo_url)
                    await self.bot.edit_message(menu, embed=em)
                    return
                elif retour.reaction.emoji == "⏹":
                    continue
                else:
                    pass
                # TODO Pouvoir constituer un groupe de jeu
            elif rap.reaction.emoji == "🔄":
                continue
            else:
                em.set_footer(text="Réaction invalide | {}".format(self.version), icon_url=self.logo_url)
                await self.bot.edit_message(menu, embed=em)
                return

    @commands.command(pass_context=True, no_pm=True)
    async def find(self, ctx, *recherche):
        """Permet de retrouver à qui appartient un pseudo ou un surnom."""
        recherche = " ".join(recherche)
        liste = self.ego.find_pseudo(recherche)
        if not liste:
            await self.bot.say("Aucun résultat trouvé. Essayez d'être moins précis et/ou vérifiez l'orthographe.")
            return
        server = ctx.message.server
        msg = ""
        for p in liste:
            try:
                mp = server.get_member(p[0])
                msg += "**{}** ({})\n".format(str(mp), p[1])
            except:
                msg += "*{}* ({})\n".format(p[0], p[1])
        em = discord.Embed(color=ctx.message.author.color, title="Résultats pour {}".format(recherche), description=msg)
        em.set_footer(text="Anciens pseudos pris en compte | {}".format(self.version),
                      icon_url=self.logo_url)
        await self.bot.say(embed=em)

    def check(self, reaction, user):
        return not user.bot

    async def ego_loop(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(15)  # Temps de mise en route
            server = self.bot.get_server("328632789836496897")
            while True:
                if "INVITS" not in self.glb["SYS"]: #MAJ des Invitations actives
                    self.glb["SYS"]["INVITS"] = {}
                invits = self.bot.invites_from(server)
                for i in invits:
                    if i.code not in self.glb["SYS"]["INVITS"]:
                        self.glb["SYS"]["INVITS"][i.code] = {"CREATED": i.created_at,
                                                      "MAX_USES": i.max_uses,
                                                      "USES": i.uses,
                                                      "CHANNEL": i.channel,
                                                      "URL": str(i)}
                for e in self.glb["SYS"]["INVITS"]:
                    if e.code not in [i.code for i in invits]:
                        del self.glb["SYS"]["INVITS"][e.code]

                date = time.strftime("%d/%m/%Y", time.localtime())
                heure = time.strftime("%H", time.localtime())
                totalactif = totalinactif = 0
                if date not in self.glb["DATES"]:
                    self.glb["DATES"][date] = {}
                if "HORO_VOCAL_ACTIF" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["HORO_VOCAL_ACTIF"] = {}
                if "HORO_VOCAL_INACTIF" not in self.glb["DATES"][date]:
                    self.glb["DATES"][date]["HORO_VOCAL_INACTIF"] = {}
                for user in server.members:
                    if user.voice:
                        if not user.voice.is_afk:
                            if not user.voice.self_deaf or not user.voice.deaf:
                                if not user.voice.self_mute or not user.voice.mute:
                                    totalactif += 1
                                else:
                                    totalinactif += 1
                self.glb["DATES"][date]["HORO_VOCAL_ACTIF"][heure] = \
                    self.glb["DATES"][date]["HORO_VOCAL_ACTIF"][heure] \
                    + totalactif if heure in self.glb["DATES"][date]["HORO_VOCAL_ACTIF"] else totalactif
                self.glb["DATES"][date]["HORO_VOCAL_INACTIF"][heure] = \
                    self.glb["DATES"][date]["HORO_VOCAL_INACTIF"][heure] \
                    + totalinactif if heure in self.glb["DATES"][date]["HORO_VOCAL_INACTIF"] else totalinactif
                fileIO("data/ego/glb.json", "save", self.glb)
                await asyncio.sleep(1800)  # ! Changer aussi le calcul de l'activité vocale si cette valeur change !
        except asyncio.CancelledError:
            pass

    async def l_msg(self, message):
        if not message.server.id == "328632789836496897":
            return
        mentions = message.mentions
        author = message.author
        channel = message.channel
        ego = self.ego.open(author)
        date = time.strftime("%d/%m/%Y", time.localtime())
        if date not in self.glb["DATES"]:
            self.glb["DATES"][date] = {}
        if not author.bot:
            self.glb["DATES"][date]["TOTAL_MSG"] = self.glb["DATES"][date]["TOTAL_MSG"] + 1 if \
                "TOTAL_MSG" in self.glb["DATES"][date] else 1
            if "CHANNEL_MSG" in self.glb["DATES"][date]:
                self.glb["DATES"][date]["CHANNEL_MSG"][channel.id] = \
                    self.glb["DATES"][date]["CHANNEL_MSG"][channel.id] \
                    + 1 if channel.id in self.glb["DATES"][date]["CHANNEL_MSG"] else 1
            else:
                self.glb["DATES"][date]["CHANNEL_MSG"] = {channel.id: 1}
        else:
            self.glb["DATES"][date]["BOT_TOTAL_MSG"] = \
                self.glb["DATES"][date]["BOT_TOTAL_MSG"] + 1 if "BOT_TOTAL_MSG" in self.glb["DATES"][date] else 1
        heure = time.strftime("%H", time.localtime())
        if "HORO_ECRIT" in self.glb["DATES"][date]:
            self.glb["DATES"][date]["HORO_ECRIT"][heure] = \
                self.glb["DATES"][date]["HORO_ECRIT"][heure] + 1 if \
                heure in self.glb["DATES"][date]["HORO_ECRIT"] else 1
        else:
            self.glb["DATES"][date]["HORO_ECRIT"] = {heure: 1}
        ego.stats["NB_MSG"] = ego.stats["NB_MSG"] + 1 if "NB_MSG" in ego.stats else 1
        if "NB_MSG_CHANNEL" in ego.stats:
            ego.stats["NB_MSG_CHANNEL"][channel.id] = ego.stats["NB_MSG_CHANNEL"][channel.id] + 1 if \
                channel.id in ego.stats["NB_MSG_CHANNEL"] else 1
        else:
            ego.stats["NB_MSG_CHANNEL"] = {channel.id: 1}
        if mentions:
            if "MENTIONS" in ego.stats:
                for u in mentions:
                    ego.stats["MENTIONS"][u.id] = \
                        ego.stats["MENTIONS"][u.id] + 1 if u.id in ego.stats["MENTIONS"] else 1
            else:
                ego.stats["MENTIONS"] = {}
        lmi = self.ego.find_m(message.content)
        if lmi:
            if "MENTIONS" in ego.stats:
                for u in mentions:
                    ego.stats["MENTIONS"][u] = \
                        ego.stats["MENTIONS"][u] + 1 if u in ego.stats["MENTIONS"] else 1
            else:
                ego.stats["MENTIONS"] = {}
        self.ego.save()
        fileIO("data/ego/glb.json", "save", self.glb)
        # TODO Avec Charm (en lié) > Stats des Emojis & Stickers

    async def l_join(self, user):
        server = user.server
        ego = self.ego.open(user)
        descr = "Est arrivé [{}]"
        if server.id != "328632789836496897" or user.bot:
            return
        date = time.strftime("%d/%m/%Y", time.localtime())
        if date not in self.glb["DATES"]:
            self.glb["DATES"][date] = {}
        self.glb["DATES"][date]["TOTAL_JOIN"] = self.glb["DATES"][date]["TOTAL_JOIN"] + 1 if \
            "TOTAL_JOIN" in self.glb["DATES"][date] else 1
        if ego.creation <= (time.time() - 500):
            descr = "Est revenu [{}]"
            self.glb["DATES"][date]["TOTAL_RETOUR"] = self.glb["DATES"][date]["TOTAL_RETOUR"] + 1 if \
                "TOTAL_RETOUR" in self.glb["DATES"][date] else 1
        ego.stats["JOINS"] = ego.stats["JOINS"] + 1 if "JOINS" in ego.stats else 1
        code = "???"
        for i in self.bot.invites_from(server):
            for e in self.glb["SYS"]["INVITS"]:
                if i.code == e:
                    if self.glb["SYS"]["INVITS"][e]["USES"] < i.uses:
                        code = i.code
                        if "JOIN_FROM" not in ego.stats:
                            ego.stats["JOIN_FROM"] = []
                        else:
                            ego.stats["JOIN_FROM"].append([date, i.code])
                        self.glb["SYS"]["INVITS"][e]["USES"] = i.uses
        self.ego.new_event(user, "immigration", descr.format(code))
        fileIO("data/ego/glb.json", "save", self.glb)
        self.ego.save()

    async def l_quit(self, user):
        server = user.server
        ego = self.ego.open(user)
        if server.id != "328632789836496897" or user.bot:
            return
        date = time.strftime("%d/%m/%Y", time.localtime())
        if date not in self.glb["DATES"]:
            self.glb["DATES"][date] = {}
        self.glb["DATES"][date]["TOTAL_QUIT"] = self.glb["DATES"][date]["TOTAL_QUIT"] + 1 if \
            "TOTAL_QUIT" in self.glb["DATES"][date] else 1
        ego.stats["QUITS"] = ego.stats["QUITS"] + 1 if "QUITS" in ego.stats else 1
        ego.stats["ROLLBACK_ROLES"] = [r.name for r in user.roles]
        self.ego.new_event(user, "immigration", "A quitté le serveur")
        fileIO("data/ego/glb.json", "save", self.glb)
        self.ego.save()

    async def l_react(self, reaction, user):
        server = user.server
        ego = self.ego.open(user)
        if server.id != "328632789836496897" or user.bot:
            return
        date = time.strftime("%d/%m/%Y", time.localtime())
        if date not in self.glb["DATES"]:
            self.glb["DATES"][date] = {}
        if "REACTIONS" not in self.glb["DATES"][date]:
            self.glb["DATES"][date]["REACTIONS"] = {}
        self.glb["DATES"][date]["REACTIONS"][reaction.emoji.name] = \
            self.glb["DATES"][date]["REACTIONS"][reaction.emoji.name] + 1 if \
            reaction.emoji.name in self.glb["DATES"][date]["REACTIONS"] else 1
        if "REACTIONS" not in ego.stats:
            ego.stats["REACTIONS"] = {}
        ego.stats["REACTIONS"][reaction.emoji.name] = \
            ego.stats["REACTIONS"][reaction.emoji.name] + 1 if reaction.emoji.name in ego.stats["REACTIONS"] else 1
        fileIO("data/ego/glb.json", "save", self.glb)
        self.ego.save()

    async def l_profil(self, avant, apres):  # Non-optimisable :(
        ego = self.ego.open(apres)
        heure = time.strftime("%H", time.localtime())
        if avant.name != apres.name:
            if "PSEUDOS" in ego.stats:
                ego.stats["PSEUDOS"].append(apres.name)
            else:
                ego.stats["PSEUDOS"] = [avant.name, apres.name]
            self.ego.new_event(apres, "nom", "Pseudo changé pour {}".format(apres.name))
        if avant.display_name != apres.display_name:
            if "D_PSEUDOS" in ego.stats:
                ego.stats["D_PSEUDOS"].append(apres.name)
            else:
                ego.stats["D_PSEUDOS"] = [avant.display_name, apres.display_name]
            self.ego.new_event(apres, "nom", "Surnom changé pour {}".format(apres.display_name))
        if avant.avatar_url != apres.avatar_url:
            self.ego.new_event(apres, "autre", "Changement d'avatar")
        if avant.top_role != apres.top_role:
            if avant.top_role.name != "Prison" and apres.top_role.name != "Prison":
                if apres.top_role > avant.top_role:
                    self.ego.new_event(apres, "role", "A été promu {}".format(apres.top_role.name))
                else:
                    self.ego.new_event(apres, "role", "A été rétrogradé {}".format(avant.top_role.name))
            else:
                if apres.top_role.name == "Prison":
                    self.ego.new_event(apres, "punition", "Est entré en prison")
                else:
                    self.ego.new_event(apres, "punition", "Est sorti de prison")
        if apres.game:
            if apres.game.name:
                if apres.game.name.lower() not in ego.jeux:
                    ego.jeux.append(apres.game.name.lower())
        if avant.status.offline:
            if apres.status.online or apres.status.dnd or apres.status.idle:
                if "CONNECT" in ego.stats:
                    ego.stats["CONNECT"][heure] = ego.stats["CONNECT"][heure] + 1 if \
                        heure in ego.stats["CONNECT"] else 1
                else:
                    ego.stats["CONNECT"] = {heure : 1}
        elif avant.status.online:
            if apres.status.offline or apres.status.invisible:
                if "DECONNECT" in ego.stats:
                    ego.stats["DECONNECT"][heure] = ego.stats["DECONNECT"][heure] + 1 if \
                        heure in ego.stats["DECONNECT"] else 1
                else:
                    ego.stats["DECONNECT"][heure] = 1
        else:
            pass
        self.ego.save()

    async def l_ban(self, user):
        ego = self.ego.open(user)
        ego.stats["BANS"] = ego.stats["BANS"] + 1 if "BANS" in ego.stats else 1
        self.ego.new_event(user, "punition", "A été banni")
        self.ego.save()

    async def l_voice(self, avant, apres):
        ego = self.ego.open(apres)
        server = apres.server
        if server.id != "328632789836496897" or apres.bot:
            return
        date = time.strftime("%d/%m/%Y", time.localtime())
        if date not in self.glb["DATES"]:
            self.glb["DATES"][date] = {}
        if apres.voice:
            if apres.voice.is_afk:
                if avant.voice.mute or avant.voice.self_mute:
                    diff = time.time() - ego.stats["CAR_VOCAL"] if ego.stats["CAR_VOCAL"] > 0 else 0
                    now = time.strftime("%d/%m/%Y", time.localtime())
                    debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_VOCAL"]))
                    if now != debut:
                        zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                        tempsnow = time.time() - zero
                        tempsdebut = zero - ego.stats["CAR_VOCAL"]
                        self.glb["DATES"][now]["TOTAL_VOCAL"] = \
                            self.glb["DATES"][now]["TOTAL_VOCAL"] + tempsnow if "TOTAL_VOCAL" \
                                                                                 in self.glb["DATES"][
                                                                                     now] else tempsnow
                        self.glb["DATES"][debut]["TOTAL_VOCAL"] = \
                            self.glb["DATES"][debut]["TOTAL_VOCAL"] + tempsdebut if "TOTAL_VOCAL" \
                                                                                     in self.glb["DATES"][
                                                                                         debut] else tempsdebut
                    else:
                        self.glb["DATES"][date]["TOTAL_VOCAL"] = \
                            self.glb["DATE"][date]["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" \
                                                                             in self.glb["DATES"][date] else diff
                    ego.stats["TOTAL_VOCAL"] = \
                        ego.stats["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" in ego.stats else diff
                    ego.stats["CAR_VOCAL"] = 0
                    return
                else:
                    diff = time.time() - ego.stats["CAR_PAROLE"] if ego.stats["CAR_PAROLE"] > 0 else 0
                    now = time.strftime("%d/%m/%Y", time.localtime())
                    debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_PAROLE"]))
                    if now != debut:
                        zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                        tempsnow = time.time() - zero
                        tempsdebut = zero - ego.stats["CAR_PAROLE"]
                        self.glb["DATES"][now]["TOTAL_PAROLE"] = \
                            self.glb["DATES"][now]["TOTAL_PAROLE"] + tempsnow if "TOTAL_PAROLE" \
                                                                                in self.glb["DATES"][
                                                                                    now] else tempsnow
                        self.glb["DATES"][debut]["TOTAL_PAROLE"] = \
                            self.glb["DATES"][debut]["TOTAL_PAROLE"] + tempsdebut if "TOTAL_PAROLE" \
                                                                                    in self.glb["DATES"][
                                                                                        debut] else tempsdebut
                    else:
                        self.glb["DATES"][date]["TOTAL_PAROLE"] = \
                            self.glb["DATE"][date]["TOTAL_PAROLE"] + diff if "TOTAL_PAROLE" \
                                                                             in self.glb["DATES"][date] else diff
                    ego.stats["TOTAL_PAROLE"] = \
                        ego.stats["TOTAL_PAROLE"] + diff if "TOTAL_PAROLE" in ego.stats else diff
                    ego.stats["CAR_PAROLE"] = 0
                    return
            if not avant.voice:
                if apres.voice.mute or apres.voice.self_mute:
                    ego.stats["CAR_VOCAL"] = time.time()  # CAR = Compte A Rebours
                else:
                    ego.stats["CAR_PAROLE"] = time.time()
            else:
                if avant.voice.mute or avant.voice.self_mute:
                    if not apres.voice.mute or not apres.voice.self_mute:
                        ego.stats["CAR_PAROLE"] = time.time()
                        diff = time.time() - ego.stats["CAR_VOCAL"] if ego.stats["CAR_VOCAL"] > 0 else 0
                        now = time.strftime("%d/%m/%Y", time.localtime())
                        debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_VOCAL"]))
                        if now != debut:
                            zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                            tempsnow = time.time() - zero
                            tempsdebut = zero - ego.stats["CAR_VOCAL"]
                            self.glb["DATES"][now]["TOTAL_VOCAL"] = \
                                self.glb["DATES"][now]["TOTAL_VOCAL"] + tempsnow if "TOTAL_VOCAL" \
                                                                                    in self.glb["DATES"][
                                                                                        now] else tempsnow
                            self.glb["DATES"][debut]["TOTAL_VOCAL"] = \
                                self.glb["DATES"][debut]["TOTAL_VOCAL"] + tempsdebut if "TOTAL_VOCAL" \
                                                                                        in self.glb["DATES"][
                                                                                            debut] else tempsdebut
                        else:
                            self.glb["DATES"][date]["TOTAL_VOCAL"] = \
                                self.glb["DATE"][date]["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" \
                                                                                in self.glb["DATES"][date] else diff
                        ego.stats["TOTAL_VOCAL"] = \
                            ego.stats["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" in ego.stats else diff
                        ego.stats["CAR_VOCAL"] = 0
                else:
                    if apres.voice.mute or apres.voice.self_mute:
                        if "CAR_PAROLE" in ego.stats:
                            ego.stats["CAR_VOCAL"] = time.time()
                            diff = time.time() - ego.stats["CAR_PAROLE"] if ego.stats["CAR_PAROLE"] > 0 else 0
                            now = time.strftime("%d/%m/%Y", time.localtime())
                            debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_PAROLE"]))
                            if now != debut:
                                zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                                tempsnow = time.time() - zero
                                tempsdebut = zero - ego.stats["CAR_PAROLE"]
                                self.glb["DATES"][now]["TOTAL_PAROLE"] = \
                                    self.glb["DATES"][now]["TOTAL_PAROLE"] + tempsnow if "TOTAL_PAROLE" \
                                                                                     in self.glb["DATES"][
                                                                                            now] else tempsnow
                                self.glb["DATES"][debut]["TOTAL_PAROLE"] = \
                                    self.glb["DATES"][debut]["TOTAL_PAROLE"] + tempsdebut if "TOTAL_PAROLE" \
                                                                                     in self.glb["DATES"][
                                                                                                debut] else tempsdebut
                            else:
                                self.glb["DATES"][date]["TOTAL_PAROLE"] = \
                                    self.glb["DATES"][date]["TOTAL_PAROLE"] + \
                                    diff if "TOTAL_PAROLE" in self.glb["DATES"][date] else diff
                            ego.stats["TOTAL_PAROLE"] = \
                                ego.stats["TOTAL_PAROLE"] + diff if "TOTAL_PAROLE" in ego.stats else diff
                            ego.stats["CAR_PAROLE"] = 0
        elif avant.voice:
            if avant.voice.self_mute or avant.voice.mute:
                if "CAR_VOCAL" in ego.stats:
                    diff = time.time() - ego.stats["CAR_VOCAL"] if ego.stats["CAR_VOCAL"] > 0 else 0
                    now = time.strftime("%d/%m/%Y", time.localtime())
                    debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_VOCAL"]))
                    if now != debut:
                        zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                        tempsnow = time.time() - zero
                        tempsdebut = zero - ego.stats["CAR_VOCAL"]
                        self.glb["DATES"][now]["TOTAL_VOCAL"] = \
                            self.glb["DATES"][now]["TOTAL_VOCAL"] + tempsnow if "TOTAL_VOCAL" \
                                                                                in self.glb["DATES"][
                                                                                    now] else tempsnow
                        self.glb["DATES"][debut]["TOTAL_VOCAL"] = \
                            self.glb["DATES"][debut]["TOTAL_VOCAL"] + tempsdebut if "TOTAL_VOCAL" \
                                                                                    in self.glb["DATES"][
                                                                                        debut] else tempsdebut
                    else:
                        self.glb["DATES"][date]["TOTAL_VOCAL"] = \
                            self.glb["DATE"][date]["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" \
                                                                            in self.glb["DATES"][date] else diff
                    ego.stats["TOTAL_VOCAL"] = \
                        ego.stats["TOTAL_VOCAL"] + diff if "TOTAL_VOCAL" in ego.stats else diff
                    ego.stats["CAR_VOCAL"] = 0
            else:
                if "CAR_PAROLE" in ego.stats:
                    diff = time.time() - ego.stats["CAR_PAROLE"] if ego.stats["CAR_PAROLE"] > 0 else 0
                    now = time.strftime("%d/%m/%Y", time.localtime())
                    debut = time.strftime("%d/%m/%Y", time.localtime(ego.stats["CAR_PAROLE"]))
                    if now != debut:
                        zero = time.mktime(time.strptime(now, "%d/%m/%Y"))
                        tempsnow = time.time() - zero
                        tempsdebut = zero - ego.stats["CAR_PAROLE"]
                        self.glb["DATES"][now]["TOTAL_PAROLE"] = \
                            self.glb["DATES"][now]["TOTAL_PAROLE"] + tempsnow if "TOTAL_PAROLE" \
                                                                                 in self.glb["DATES"][
                                                                                     now] else tempsnow
                        self.glb["DATES"][debut]["TOTAL_PAROLE"] = \
                            self.glb["DATES"][debut]["TOTAL_PAROLE"] + tempsdebut if "TOTAL_PAROLE" \
                                                                                     in self.glb["DATES"][
                                                                                         debut] else tempsdebut
                    else:
                        self.glb["DATES"][date]["TOTAL_PAROLE"] = \
                            self.glb["DATES"][date]["TOTAL_PAROLE"] + diff if "TOTAL_PAROLE" \
                                                                              in self.glb["DATES"][date] else diff
                    ego.stats["TOTAL_PAROLE"] = \
                        ego.stats["TOTAL_PAROLE"] + diff if "TOTAL_PAROLE" in ego.stats else diff
                    ego.stats["CAR_PAROLE"] = 0
        else:
            return
        fileIO("data/ego/glb.json", "save", self.glb)
        self.ego.save()

    def __unload(self):
        fileIO("data/ego/glb.json", "save", self.glb)
        if "glb.json" in os.listdir("data/ego/backup/"):
            if os.path.getsize("data/ego/backup/glb.json") < os.path.getsize("data/ego/glb.json"):
                fileIO("data/ego/backup/glb.json", "save", self.glb)
            else:
                print("ATTENTION: EGO n'a pas réalisé de backup car le fichier source est moins "
                      "volumineux que le dernier fichier backup. Un problème à pu se produire dans les données...")
        self.ego.save(backup=True)
        return True

def check_folders():
    if not os.path.exists("data/ego"):
        print("Creation du dossier EGO...")
        os.makedirs("data/ego")
    if not os.path.exists("data/ego/backup"):
        print("Creation du dossier backup d'Ego...")
        os.makedirs("data/ego/backup")


def check_files():
    if not os.path.isfile("data/ego/data.json"):
        print("Création et import de Ego/data")
        fileIO("data/ego/data.json", "save", {})
    if not os.path.isfile("data/ego/glb.json"):
        print("Création et import de Ego/glb")
        fileIO("data/ego/glb.json", "save", {"DATES": {}, "SYS": {}})
        # DATES pour les stats (datées), SYS pour le reste


def setup(bot):
    check_folders()
    check_files()
    n = Ego(bot)
    bot.add_listener(n.l_msg, "on_message")
    bot.add_listener(n.l_react, "on_reaction_add")
    bot.add_listener(n.l_join, "on_member_join")
    bot.add_listener(n.l_quit, "on_member_remove")
    bot.add_listener(n.l_profil, "on_member_update")
    bot.add_listener(n.l_ban, "on_member_ban")
    bot.add_listener(n.l_voice, "on_voice_state_update")
    bot.add_cog(n)
