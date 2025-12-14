import discord
from discord import ui
from discord.ext import commands, tasks
import json
import os
import time
import datetime
import random
import asyncio
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de Intents
intents = discord.Intents.default()
intents.message_content = True

# Defina seu bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Nome do arquivo de banco de dados
DB_FILE = "data.json"

# --- Constantes de ID para Componentes (Devem ser INT) ---
ID_TITLE = 100
ID_RULES = 101
ID_PRIZE = 102
ID_IMAGE = 103
ID_DATE = 104
ID_WINNERS_COUNT = 105
ID_BTN_PARTICIPATE = 106
ID_BTN_PARTICIPANTS_COUNT = 107
ID_WINNER_SECTION_BASE = 200 # Base para IDs dinâmicos de ganhadores

# --- Gerenciamento de Banco de Dados JSON ---
class Database:
    def __init__(self, filename):
        self.filename = filename
        self.check_file()

    def check_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump({"giveaways": {}}, f, indent=4)

    def load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"giveaways": {}}

    def save(self, data):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_giveaway(self, message_id):
        data = self.load()
        return data["giveaways"].get(str(message_id))

    def update_giveaway(self, message_id, update_data):
        data = self.load()
        str_id = str(message_id)
        if str_id not in data["giveaways"]:
            data["giveaways"][str_id] = {}
        data["giveaways"][str_id].update(update_data)
        self.save(data)
    
    def end_giveaway_db(self, message_id):
        """Marca um sorteio como finalizado no DB sem apagar os dados"""
        self.update_giveaway(message_id, {"status": "ended"})

    def add_participant(self, message_id, user_id):
        data = self.load()
        str_id = str(message_id)
        if str_id in data["giveaways"]:
            if "participants" not in data["giveaways"][str_id]:
                data["giveaways"][str_id]["participants"] = []
            
            # Verifica se já existe (int ou str) para evitar duplicatas
            participants = data["giveaways"][str_id]["participants"]
            if user_id not in participants and str(user_id) not in participants:
                # Salva sempre como INT para padronizar
                data["giveaways"][str_id]["participants"].append(int(user_id))
                self.save(data)
                return True
        return False

db = Database(DB_FILE)

# --- Modais de Edição ---

class EditStringModal(ui.Modal):
    def __init__(self, title, label, key, view_ref, placeholder=None, style=discord.TextStyle.paragraph, default_value=None):
        super().__init__(title=title)
        self.key = key
        self.view_ref = view_ref
        
        default_str = str(default_value) if default_value is not None else None
        
        self.input_field = ui.TextInput(
            label=label, 
            style=style, 
            placeholder=placeholder, 
            default=default_str,
            required=True
        )
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        self.view_ref.data[self.key] = self.input_field.value
        db.update_giveaway(self.view_ref.message_id, {self.key: self.input_field.value})
        
        new_view = SorteioView(self.view_ref.message_id, self.view_ref.data)
        await interaction.response.edit_message(view=new_view)

class EditIntModal(ui.Modal):
    def __init__(self, title, label, key, view_ref, placeholder="Digite apenas números inteiros", default_value=None):
        super().__init__(title=title)
        self.key = key
        self.view_ref = view_ref
        
        default_str = str(default_value) if default_value is not None else None
        
        self.input_field = ui.TextInput(
            label=label, 
            style=discord.TextStyle.short, 
            placeholder=placeholder, 
            default=default_str,
            required=True
        )
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.input_field.value)
            if value < 1: raise ValueError
            
            self.view_ref.data[self.key] = value
            
            if self.key == "duration_days":
                now = int(time.time())
                end_ts = now + (value * 86400)
                self.view_ref.data["end_timestamp"] = end_ts
                db.update_giveaway(self.view_ref.message_id, {
                    "duration_days": value,
                    "end_timestamp": end_ts
                })
            else:
                db.update_giveaway(self.view_ref.message_id, {self.key: value})

            new_view = SorteioView(self.view_ref.message_id, self.view_ref.data)
            await interaction.response.edit_message(view=new_view)
        except ValueError:
            await interaction.response.send_message("Por favor, insira um número inteiro válido.", ephemeral=True)

# --- View Principal (LayoutView) ---

class SorteioView(ui.LayoutView):
    def __init__(self, message_id, data=None):
        super().__init__()
        self.message_id = str(message_id)
        
        # Dados padrão
        self.data = data or {}
        
        # Valores Default
        defaults = {
            "title": "Sorteio Incrível",
            "rules": "1 - Entre no servidor\n2 - Clique em participar",
            "prize": "Prêmio Surpresa",
            "image_url": "https://www.falamart.com.br/wp-content/uploads/2023/09/sorteio-de-brindes.jpg",
            "duration_days": 5,
            "end_timestamp": int(time.time()) + (5 * 86400),
            "winners_count": 1,
            "status": "setup",
            "participants": [],
            "winners": []
        }
        
        # Mescla defaults com data existente
        for key, value in defaults.items():
            if key not in self.data:
                self.data[key] = value

        # Garante que dados existam no DB se não vieram
        if not data:
            db.update_giveaway(self.message_id, self.data)

        # Constrói a UI inicial
        self.build_ui()
        self.update_components_visuals()

    def build_ui(self):
        # Container Principal
        self.container = ui.Container(accent_colour=discord.Colour(3948357))

        is_setup = self.data['status'] == 'setup'

        # --- Helper para adicionar itens configuráveis ---
        def add_config_item(text_component, edit_key=None):
            if is_setup and edit_key:
                self.container.add_item(
                    ui.Section(text_component, accessory=self._create_edit_btn(edit_key))
                )
            else:
                self.container.add_item(text_component)

        # --- Seção Título ---
        add_config_item(
            ui.TextDisplay(content=f"# 🚩 {self.data['title']}", id=ID_TITLE),
            "edit_title"
        )
        
        self.container.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        # --- Seção Regras ---
        self.container.add_item(ui.TextDisplay(content="### 🧐 Regras para participar"))
        add_config_item(
            ui.TextDisplay(content=self.data['rules'], id=ID_RULES),
            "edit_rules"
        )
        self.container.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        # --- Seção Prêmios ---
        self.container.add_item(ui.TextDisplay(content="### 🏆 Prêmio(s)"))
        add_config_item(
            ui.TextDisplay(content=self.data['prize'], id=ID_PRIZE),
            "edit_prize"
        )

        # --- Galeria de Mídia (Imagem) ---
        img_url = self.data.get("image_url")
        
        # Constrói a galeria se houver URL válida
        if img_url and len(str(img_url).strip()) > 0:
            self.media_gallery = ui.MediaGallery(
                # CORREÇÃO AQUI: discord.MediaGalleryItem (não ui.MediaGalleryItem)
                discord.MediaGalleryItem(media=str(img_url).strip()),
                id=ID_IMAGE
            )
            self.container.add_item(self.media_gallery)

        # Botão editar imagem (Apenas setup)
        if is_setup:
            row_img = ui.ActionRow(
                ui.Button(style=discord.ButtonStyle.secondary, label="Editar Imagem (URL)", custom_id=f"edit_image_{self.message_id}")
            )
            self.container.add_item(row_img)

        self.container.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        # --- Seção Data ---
        self.container.add_item(ui.TextDisplay(content="### 📅 Dia do sorteio"))
        add_config_item(
            ui.TextDisplay(content="...", id=ID_DATE),
            "edit_date"
        )
        self.container.add_item(ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        # --- Seção Ganhadores (Count) ---
        self.container.add_item(ui.TextDisplay(content="### 🥇 Ganhadores"))
        add_config_item(
            ui.TextDisplay(content="...", id=ID_WINNERS_COUNT),
            "edit_winners"
        )

        # Adiciona o container à View
        self.add_item(self.container)

        # --- Action Row Principal (Botões) ---
        self.action_row = ui.ActionRow()
        
        if is_setup:
            self.action_row.add_item(ui.Button(style=discord.ButtonStyle.success, label="Iniciar", custom_id=f"start_{self.message_id}"))
        
        if self.data['status'] == 'running':
            self.action_row.add_item(ui.Button(style=discord.ButtonStyle.primary, label="Participar", emoji="🎉", custom_id=f"join_{self.message_id}", id=ID_BTN_PARTICIPATE))
        
        # Contador de participantes
        count = len(self.data.get("participants", []))
        self.action_row.add_item(ui.Button(style=discord.ButtonStyle.secondary, label=f"{count} participando", disabled=True, id=ID_BTN_PARTICIPANTS_COUNT))

        self.add_item(self.action_row)

    def _create_edit_btn(self, type_key):
        return ui.Button(style=discord.ButtonStyle.primary, label="Editar", emoji="✏️", custom_id=f"{type_key}_{self.message_id}")

    def update_components_visuals(self):
        # Título
        t_title = self.find_item(ID_TITLE)
        if t_title: t_title.content = f"# 🚩 {self.data['title']}"

        # Regras
        t_rules = self.find_item(ID_RULES)
        if t_rules: t_rules.content = self.data['rules']

        # Prêmio
        t_prize = self.find_item(ID_PRIZE)
        if t_prize: t_prize.content = self.data['prize']

        # Data
        t_date = self.find_item(ID_DATE)
        if t_date:
            ts = self.data['end_timestamp']
            
            if self.data['status'] == 'ended':
                 dt_val = datetime.datetime.fromtimestamp(ts)
                 date_str = dt_val.strftime("%d/%m/%Y às %H:%M")
                 t_date.content = f"Finalizado em **{date_str}**"
            else:
                 now = int(time.time())
                 remaining = max(0, ts - now)
                 
                 days = remaining // 86400
                 remaining %= 86400
                 hours = remaining // 3600
                 remaining %= 3600
                 minutes = remaining // 60
                 
                 dt_val = datetime.datetime.fromtimestamp(ts)
                 date_str = dt_val.strftime("%d/%m/%Y às %H:%M")
                 
                 t_date.content = (
                     f"O resultado dos ganhadores será em **{days} dias, {hours} horas e {minutes} minutos** "
                     f"`({date_str})`"
                 )

        # Contagem Ganhadores (Texto)
        t_w_count = self.find_item(ID_WINNERS_COUNT)
        if t_w_count: t_w_count.content = f"`{self.data['winners_count']}` ganhador(es) não revelados 🥳"

        # Participantes Count (Botão)
        b_part = self.find_item(ID_BTN_PARTICIPANTS_COUNT)
        if b_part: 
            count = len(self.data.get("participants", []))
            b_part.label = f"{count} participando"

        # Se status == ended, adiciona seções de ganhadores se não existirem
        if self.data['status'] == 'ended':
            self._render_winners_list()

    def _render_winners_list(self):
        winners = self.data.get("winners", [])
        
        for i, winner_id in enumerate(winners):
            section_id = ID_WINNER_SECTION_BASE + i
            
            if not self.find_item(section_id):
                user_text = f"### 🥇 <@{winner_id}> - `{winner_id}`"
                section = ui.Section(
                    ui.TextDisplay(content=user_text),
                    accessory=ui.Button(style=discord.ButtonStyle.secondary, emoji="🔄", custom_id=f"reroll_{self.message_id}_{i}")
                )
                section.id = section_id 
                self.container.add_item(section)


# --- Gerenciador de Eventos Global ---

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data.get('custom_id'):
        return

    custom_id = interaction.data['custom_id']
    
    parts = custom_id.split('_')
    if len(parts) < 2: return
    
    action = parts[0]
    
    # Tratamento para IDs
    if action == "edit":
        action = f"{parts[0]}_{parts[1]}"
        msg_id = parts[2]
    elif action == "reroll":
        msg_id = parts[1]
        winner_index = int(parts[2])
    else:
        msg_id = parts[1]

    # Carregar dados
    data = db.get_giveaway(msg_id)
    if not data:
        return

    # Cria view
    view = SorteioView(msg_id, data)

    # Permissão Admin
    is_admin = interaction.user.guild_permissions.administrator
    if action in ["edit_title", "edit_rules", "edit_prize", "edit_image", "edit_date", "edit_winners", "start", "reroll"] and not is_admin:
        await interaction.response.send_message("Apenas administradores podem gerenciar o sorteio.", ephemeral=True)
        return

    # --- Ações ---

    if action == "edit_title":
        await interaction.response.send_modal(EditStringModal("Editar Título", "Novo Título", "title", view, default_value=data.get('title')))
    
    elif action == "edit_rules":
        await interaction.response.send_modal(EditStringModal("Editar Regras", "Regras", "rules", view, style=discord.TextStyle.paragraph, default_value=data.get('rules')))
        
    elif action == "edit_prize":
        await interaction.response.send_modal(EditStringModal("Editar Prêmio", "Prêmio", "prize", view, default_value=data.get('prize')))
        
    elif action == "edit_image":
        await interaction.response.send_modal(EditStringModal("Imagem URL", "URL da Imagem", "image_url", view, placeholder="https://...", default_value=data.get('image_url')))

    elif action == "edit_date":
        await interaction.response.send_modal(EditIntModal("Tempo do Sorteio", "Duração em DIAS", "duration_days", view, default_value=data.get('duration_days')))

    elif action == "edit_winners":
        await interaction.response.send_modal(EditIntModal("Quantidade de Ganhadores", "Número de Ganhadores", "winners_count", view, default_value=data.get('winners_count')))

    elif action == "start":
        duration_days = data.get("duration_days", 5)
        new_end = int(time.time()) + (duration_days * 86400)
        
        data["status"] = "running"
        data["end_timestamp"] = new_end
        db.update_giveaway(msg_id, data)
        
        new_view = SorteioView(msg_id, data)
        await interaction.response.edit_message(view=new_view)
        await interaction.followup.send(f"Sorteio iniciado! Acaba em <t:{new_end}:R>.", ephemeral=True)

    elif action == "join":
        # Verifica se o ID (inteiro OU string) está na lista de participantes
        user_id = interaction.user.id
        participants = data.get("participants", [])
        
        if user_id in participants or str(user_id) in participants:
            await interaction.response.send_message("Tenha calma, você já está participando❗", ephemeral=True)
            return
            
        db.add_participant(msg_id, user_id)
        
        # Recarrega dados e recria view
        data = db.get_giveaway(msg_id) 
        new_view = SorteioView(msg_id, data)
        await interaction.response.edit_message(view=new_view)
        await interaction.followup.send("Você entrou no sorteio! Boa sorte! 🍀", ephemeral=True)

    elif action == "reroll":
        if data["status"] != "ended": return
        
        participants = data["participants"]
        winners = data["winners"]
        
        if not participants:
            await interaction.response.send_message("Sem participantes suficientes.", ephemeral=True)
            return

        current_winner_id = winners[winner_index]
        available = [p for p in participants if p not in winners or p == current_winner_id]
        
        if not available:
            await interaction.response.send_message("Não há outros participantes para sortear.", ephemeral=True)
            return
            
        new_winner = random.choice(available)
        winners[winner_index] = new_winner
        
        db.update_giveaway(msg_id, {"winners": winners})
        
        final_view = SorteioView(msg_id, db.get_giveaway(msg_id))
        await interaction.response.edit_message(view=final_view)
        await interaction.followup.send(f"Ganhador atualizado: <@{new_winner}>", ephemeral=True)

# --- Detector de Exclusão de Mensagem ---
@bot.event
async def on_message_delete(message):
    msg_id = str(message.id)
    data_all = db.load()
    
    if msg_id in data_all["giveaways"]:
        giveaway = data_all["giveaways"][msg_id]
        if giveaway["status"] != "ended":
            print(f"Sorteio na mensagem {msg_id} foi excluído manualmente.")
            db.end_giveaway_db(msg_id)

# --- Tarefa em Background ---
@tasks.loop(seconds=60)
async def check_giveaways():
    data = db.load()
    now = int(time.time())
    
    for msg_id, g_data in list(data["giveaways"].items()):
        if g_data["status"] == "running" and now >= g_data["end_timestamp"]:
            await end_giveaway(msg_id, g_data)

async def end_giveaway(message_id, data):
    participants = data.get("participants", [])
    count = data.get("winners_count", 1)
    
    winners = []
    if len(participants) >= count:
        winners = random.sample(participants, count)
    else:
        winners = participants 
    
    data["status"] = "ended"
    data["winners"] = winners
    db.update_giveaway(message_id, data)
    
    channel_id = data.get("channel_id")
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                msg = await channel.fetch_message(int(message_id))
                view = SorteioView(message_id, data)
                await msg.edit(view=view)
            except discord.NotFound:
                print(f"Mensagem {message_id} não encontrada. Finalizando DB.")
                db.end_giveaway_db(message_id)
            except Exception as e:
                print(f"Erro ao finalizar {message_id}: {e}")

# --- Comando Slash: Criar Sorteio ---
@bot.tree.command(name="sorteio", description="Cria um novo sorteio configurável")
async def sorteio(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permissão negada.", ephemeral=True)
        return

    await interaction.response.send_message("Criando painel de sorteio...", ephemeral=True)
    
    placeholder_view = ui.LayoutView() 
    placeholder_view.add_item(ui.TextDisplay("Iniciando configuração..."))
    
    msg = await interaction.channel.send(view=placeholder_view)
    
    initial_data = {
        "channel_id": interaction.channel_id,
        "title": "Sorteio Novo",
        "rules": "1 - Entre no servidor\n2 - Participe!",
        "prize": "Um prêmio legal",
        "image_url": "https://i.imgur.com/joSz2Qb.png",
        "duration_days": 5,
        "end_timestamp": int(time.time()) + (5 * 86400),
        "winners_count": 1,
        "status": "setup",
        "participants": [],
        "winners": []
    }
    db.update_giveaway(msg.id, initial_data)
    
    view = SorteioView(msg.id, initial_data)
    await msg.edit(view=view)

# --- Comando Slash: Sortear Agora ---
@bot.tree.command(name="sortearagora", description="Finaliza um sorteio imediatamente")
async def sortear_agora(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permissão negada.", ephemeral=True)
        return

    data = db.get_giveaway(message_id)
    if not data:
        await interaction.response.send_message("Sorteio não encontrado.", ephemeral=True)
        return
        
    if data["status"] == "ended":
        await interaction.response.send_message("Sorteio já finalizado.", ephemeral=True)
        return

    await interaction.response.send_message(f"Encerrando sorteio {message_id}...", ephemeral=True)
    
    data['end_timestamp'] = int(time.time())
    db.update_giveaway(message_id, data)
    
    await end_giveaway(message_id, data)


@bot.event
async def on_ready():
    print(f'Bot logado como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash.")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")
    
    check_giveaways.start()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
