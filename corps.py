import discord, json, requests, time
from bs4 import BeautifulSoup
from discord.ext import commands
import xml.etree.ElementTree as ET

intents = discord.Intents().all()
bot = commands.Bot(command_prefix="£", description="Eleve", intents=intents)

Data = {
    "serveurs":{
        "751409038721548349":{
            "roles":{}
        }
    },
    "utilisateurs":{}
}

def LtoStr(L):
    String = ""
    for a in L:
        String += str(a)
    return String

def SepWord(msg):
    mot = ""
    Nmsg = []
    for a in msg:
        if a == " ":
            Nmsg.append(mot)
            mot = ""
        else:
            mot += a
    if mot != "":
        Nmsg.append(mot)
    return Nmsg

def ConvertCel(Kel):
    return Kel - 273.15

def Decimal(nb, NBdecimal):
    return float(str(nb)[:(str(nb).index(".") + NBdecimal + 1)])

def GetSesaPage(pg, classe):
    ListeImage = []
    Lclasses = {
        "terminale":"mstsspe_2020",
        "exp":"mstsexp_2020"
    }
    page = pg - pg % 2
    print("page", page)
    url = "https://mep-outils.sesamath.net/manuel_numerique/index.php?ouvrage="+ Lclasses[classe] +"&page_gauche="+str(page)
    reponse = requests.get(url)
    if reponse.ok:
        soup = BeautifulSoup(reponse.text, "html.parser")
        AllStyledDiv = [a for a in soup.findAll(style=True)]
        for a in AllStyledDiv:
            if "left" in a["style"]:
                i = a["style"].index("left")
                if "width" in a["style"]:
                    j = a["style"].index("width")
                    left = int(a["style"][i+5:j-3])
                    if pg%2 == 1 and left >300 or pg%2 == 0 and left < 300:
                        width = a["style"][j+6:j+9]
                        if 150 < int(width) < 200:
                            ListeImage.append("https://zoneur.sesamath.net/imgs_produites/vign/"+ Lclasses[classe] +"/"+ a["id"][5:-2] +"-1.gif")
        return ListeImage
    else:
        print(reponse)

def foot():
    url = "https://www.maxifoot.fr/resultat-prochain.htm"
    reponse = requests.get(url)
    if reponse.ok:
        soup = BeautifulSoup(reponse.text, "html.parser")
        Titres = soup.findAll("div", {"class":"cmp1"})
        Team = []
        match = {}
        for a in soup.findAll("table", id=True):
            if a["id"][:2] == "tc":
                Team.append(a)

        for a in range(len(Titres)):
            text = ""
            for b in Team[a].findChildren("tr"):
                for c in b.findChildren("td"):
                    text += c.text + " "
                text += "\n"

            match[Titres[a].text] = text
        return match
    else:
        print(reponse)

def GetMeteo(ville):
    api_address = "http://api.openweathermap.org/data/2.5/weather?q=&appid=ad3746c385da177d0d80a7e613161a82"
    url = api_address[:49] + ville + api_address[49:]
    json_data = requests.get(url).json()
    return json_data

def GetDictTvInfo(XML):
    Lmois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
             "novembre", "décembre"]
    DtvName = {}
    for a in XML:
        if a.tag == "channel":
            DtvName[a.attrib["id"]] = {"icone":a[1].attrib["src"], "nom":a[0].text, "programme":[]}
        elif a.tag == "programme":
            Programme = {}
            for b in a:
                if b.tag == "title":
                    Programme["titre"] = b.text
                elif b.tag == "sub-title":
                    Programme["sous-titre"] = b.text
                elif b.tag == "desc":
                    Programme["desc"] = b.text
                elif b.tag == "category":
                    Programme["catégorie"] = b.text
                elif b.tag == "length":
                    Programme["longueur"] = int(b.text)
                    if b.attrib["units"] == "hours":
                        Programme["longueur"] = Programme["longueur"]*60
                elif b.tag == "icon":
                    Programme["icone"] = b.attrib["src"]
            T0 = a.attrib["start"]
            Programme["début"] = {"an": int(T0[0:4]), "mois": Lmois[int(T0[4:6])], "jour": int(T0[6:8]), "heure": int(T0[8:10]),"minute": int(T0[10:12]), "seconde": int(T0[12:14])}
            T1 = a.attrib["stop"]
            Programme["fin"] = {"an": int(T1[0:4]), "mois": Lmois[int(T1[4:6])], "jour": int(T1[6:8]), "heure": int(T1[8:10]),"minute": int(T1[10:12]), "seconde": int(T0[12:14])}
            channel = a.attrib["channel"]
            DtvName[channel]["programme"].append(Programme)
    return DtvName

@bot.event
async def on_ready():
    global Data
    f = open("data.json", "rt")
    Data = json.loads(f.read())
    f.close()
    print(Data)
    print("Prêt !")

@bot.event
async def on_message(msg):
    f = open("data.json", "wt")
    f.write(json.dumps(Data, indent=4))
    f.close()
    await bot.process_commands(msg)

@bot.event
async def on_raw_reaction_add(emoji):
    print(emoji)
    if str(emoji.message_id) in Data["serveurs"][str(emoji.guild_id)]["roles"]:
        print("Role presque ajouté")
        if emoji.emoji.name in Data["serveurs"][str(emoji.guild_id)]["roles"][str(emoji.message_id)]:
            print("Role ajouté")
            roleID = Data["serveurs"][str(emoji.guild_id)]["roles"][str(emoji.message_id)][emoji.emoji.name]
            guildID = emoji.guild_id
            for a in bot.guilds:
                if a.id == guildID:
                    guild = a
            role = guild.get_role(roleID)
            await emoji.member.add_roles(role)

@bot.command()
async def Tv(ctx, canal=None):
    url = "https://xmltv.ch/xmltv/xmltv-tnt.xml"
    reponse = requests.get(url)
    if reponse.ok:
        arbreXML = ET.fromstring(reponse.content)
        DictTv = GetDictTvInfo(arbreXML)
        if canal in [DictTv[a]["nom"] for a in DictTv]:
            id = ""
            for a in DictTv:
                if DictTv[a]["nom"] == canal:
                    id = a

            Emb = discord.Embed(title=canal, description="Identifiant: " + id)
            Emb.set_thumbnail(url=DictTv[id]["icone"])
            await ctx.send(embed=Emb)

            for a in DictTv[id]["programme"]:
                t = ""
                if "sous-titre" in a:
                    t += "Épisode : " + a["sous-titre"] + "\n"
                if "catégorie" in a:
                    t += "Catégorie : " + a["catégorie"] + "\n"
                t += "Longueur : " + str(a["longueur"]) + " minutes\n"
                t += "Début : " + str(a["début"]) + "\n"
                t += "Fin : " + str(a["fin"]) + "\n"
                Emb = discord.Embed(title=a["titre"], description=t)
                await ctx.send(embed=Emb)

            else:
                t = "Veuillez entrer une chaîne après votre commande parmis celle-ci:"
                for a in DictTv:
                    t += "\n" + DictTv[a]["nom"]
                await ctx.send(t)
        else:
            await ctx.send(str(reponse))

@bot.command()
async def foot(ctx):
    url = "https://www.maxifoot.fr/resultat-prochain.htm"
    reponse = requests.get(url)
    if reponse.ok:
        soup = BeautifulSoup(reponse.text, "html.parser")
        Titres = soup.findAll("div", {"class":"cmp1"})
        Team = []
        match = {}
        for a in soup.findAll("table", id=True):
            if a["id"][:2] == "tc":
                Team.append(a)

        for a in range(len(Titres)):
            text = ""
            for b in Team[a].findChildren("tr"):
                for c in b.findChildren("td"):
                    text += c.text + " "
                text += "\n"

            match[Titres[a].text] = text
        await ctx.send(json.dumps(match, indent=4)[:1900])
    else:
        print(reponse)

@bot.command()
async def meteo(ctx, ville):
    json_data = GetMeteo(ville)
    temp = json_data["main"]["temp"]
    Ciel = json_data["weather"][0]["description"]
    tempmax = json_data["main"]["temp_max"]
    tempmin = json_data["main"]["temp_min"]
    ressentit = json_data["main"]["feels_like"]
    pression = json_data["main"]["pressure"]
    vent = json_data["wind"]["speed"]
    LeveDeSoleil = [time.gmtime(json_data["sys"]["sunrise"])[3], time.gmtime(json_data["sys"]["sunrise"])[4],
                    time.gmtime(json_data["sys"]["sunrise"])[5]]
    CoucheDeSoleil = [time.gmtime(json_data["sys"]["sunset"])[3], time.gmtime(json_data["sys"]["sunset"])[4],
                      time.gmtime(json_data["sys"]["sunset"])[5]]
    t = "À " + str(ville) + " :\nIl fait " + str(Decimal(ConvertCel(temp), 2)) + "C° avec un ressentit de " + str(
        Decimal(ConvertCel(ressentit), 2)) + "C°.\nNous avons une pression de " + str(
        pression) + "hpa.\nEt la vitesse du vent est de " + str(vent) + " m/s."
    Emb = discord.Embed(title="**Météo du jour**", description="Voici les prévisions météos du jour à " + ville + " :")
    Emb.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/759401880773459987/763795809719418900/AWnatCZvddI0AAAAAElFTkSuQmCC.png")
    Emb.add_field(name="**Température (mesuré):**", value=str(Decimal(ConvertCel(temp), 2)) + "**C°**")
    Emb.add_field(name="**Température (ressentit):**", value=str(Decimal(ConvertCel(ressentit), 2)) + "**C°**")
    Emb.add_field(name="**Pression de l'air:**", value=str(pression) + "**hPa**")
    Emb.add_field(name="**Vitesse du vent :**", value=str(vent) + "**m/s**")
    await ctx.send(embed=Emb)

@bot.command()
async def sesamath(ctx, page, classe="terminale"):
    data = GetSesaPage(int(page), classe)
    await ctx.send("Page " + str(page)+":")
    if data != []:
        for a in data:
            await ctx.send(a)
    else:
        await ctx.send("Aucun exercice")

@bot.command()
async def role(ctx):
    # Rjson → {":grinning:" : {"RoleId":883810835900825660, "text":"blablabla"}}
    # Rjson → [[883810835900825660, text]]
    Rep = LtoStr(SepWord(ctx.message.content)[1:])
    Rjson = json.loads(Rep)
    Lemojis = ctx.message.guild.emojis[len(Rjson):]

    text = "Choisissez un role parmi les suivants en réagissant à ce message :\n"
    for a in range(len(Rjson)):
        text += str(Lemojis[a]) + "→ " + Rjson[a][1] + "\n"
    Nmsg = await ctx.send(text)
    Data["serveurs"][str(ctx.message.guild.id)]["roles"][str(Nmsg.id)] = {}
    for a in range(len(Rjson)):
        await Nmsg.add_reaction(Lemojis[a])
        Nemoji = str(Lemojis[a])[2:(len(str(Lemojis[a].id))+2)*-1]
        Data["serveurs"][str(ctx.message.guild.id)]["roles"][str(Nmsg.id)][Nemoji] = Rjson[a][0]
    await ctx.message.delete()

@bot.command()
async def addrole(ctx):
    roleID = 883810835900825660
    role = ctx.message.guild.get_role(roleID)
    userID = 713804267135303752
    user = ctx.message.guild.get_member(userID)
    await user.add_roles(role)

@bot.command()
async def emoji(ctx):
    for a in ctx.guild.emojis:
        print(a)

bot.run("NzUxNzcwMjUyMzQ5ODAwNDY4.X1N6mw.Zqf0WZhAxcpT3VbRV9adZh8YF90")
