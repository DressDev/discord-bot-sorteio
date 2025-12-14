# 🎁 Bot de Sorteios Discord (DiscordBR)

Um bot simples, persistente e visual para gerenciar sorteios no seu servidor Discord. Ele utiliza **Slash Commands**, **Botões** e **Modais** para uma experiência moderna e intuitiva.

## ✨ Funcionalidades

| **Funcionalidade** | **Descrição** | 
| :--- | :--- | 
| **🏆 Criação Fácil** | Inicie um painel com um único comando `/sorteio`. | 
| **✏️ Editor Visual** | Edite título, prêmio, imagem e regras usando formulários interativos (sem comandos complexos). | 
| **💾 Persistência** | Se o bot reiniciar, os sorteios continuam funcionando e os dados não são perdidos (`data.json`). | 
| **⏱️ Timer Automático** | O sorteio encerra automaticamente após o tempo definido. | 
| **🔄 Reroll** | O ganhador sumiu? Rode o sorteio novamente com um clique. | 
| **🖼️ Imagens** | Suporte a banners personalizados no embed do sorteio. | 

## 🚀 Como Usar (Guia Passo a Passo)

### 1️⃣ Criando o Painel

Digite o comando `/sorteio` em qualquer canal.

> *O bot criará uma mensagem "rascunho" visível para todos, mas o menu de controle é secreto (apenas você vê).*

### 2️⃣ Configurando (Menu Admin)

Ao criar o sorteio, clique no botão cinza **⚙️ Painel Admin**. Um menu exclusivo aparecerá para você:

* **✏️ Editar Título:** Defina o nome do evento.

* **📜 Editar Regras:** Escreva o que é necessário para ganhar.

* **🏆 Editar Prêmio:** O que está sendo sorteado?

* **🖼️ Editar Imagem:** Cole um link direto de imagem (JPG/PNG) para ilustrar.

* **⏱️ Duração:** Defina quantos **dias** o sorteio vai durar.

* **👥 Qtd. Ganhadores:** Quantas pessoas vão ganhar.

### 3️⃣ Iniciando

Quando tudo estiver pronto, clique no botão verde **▶️ INICIAR SORTEIO** no Painel Admin.

> *O status muda para "Running", o cronômetro começa e o botão de "Participar" é liberado para os membros.*

### 4️⃣ Finalização

* **Automática:** Quando o tempo acabar, o bot escolhe os vencedores, anuncia no chat e fecha o sorteio.

* **Manual:** Use o comando `/sortearagora [ID_DA_MENSAGEM]` para encerrar imediatamente.

### 5️⃣ Reroll (Resortear)

O sorteio acabou mas o ganhador não respondeu? Um botão vermelho **🔄 Resortear** aparecerá na mensagem do sorteio encerrado (visível apenas para admins).

## 🎨 Guia Completo de Personalização (Markdown)

Você pode usar toda a formatação suportada pelo Discord nos campos de **Regras** e **Prêmio** para deixar seu sorteio profissional.

### 📝 Formatação Básica

| Estilo | Como digitar | Resultado Visual |
| :--- | :--- | :--- |
| **Negrito** | `**Texto**` | **Texto** |
| *Itálico* | `*Texto*` ou `_Texto_` | *Texto* |
| __Sublinhado__ | `__Texto__` | __Texto__ |
| ~~Riscado~~ | `~~Texto~~` | ~~Texto~~ |
| Spoiler | `||Texto Oculto||` | ||Texto Oculto|| |

### 📑 Títulos e Citações

Use `#` no início da linha para criar títulos (apenas em mensagens, não funciona em embeds, mas útil saber).

* `# Título Grande (H1)`
* `## Título Médio (H2)`
* `### Título Pequeno (H3)`

Para destacar um bloco de texto ou regra importante, use citações:
* `> Texto` para uma linha.
* `>>> Texto` para citar todo o parágrafo.

### 💻 Blocos de Código

Para destacar comandos ou códigos:

* **Linha única:** Use crases simples `` `comando` ``.
* **Bloco multilinhas:** Use três crases:
````
    ```
    Seu texto aqui
    Fica dentro de um bloco
    ```
````

### 🌈 Texto Colorido (Syntax Highlighting)

O Discord não suporta cores de texto nativamente, mas podemos usar "truques" de linguagens de programação dentro de blocos de código para simular cores.

**⚠️ Importante:** Você deve colocar o nome da linguagem logo após as três crases iniciais (ex: ` ```diff `).

#### 🔴 Vermelho (Diff)
````
```diff
- Texto em Vermelho
```
````

#### 🟢 Verde (Diff ou JSON)
````
```diff
+ Texto em Verde
```
````
````
```json
"Texto em Verde"
```
````

#### 🔵 Azul (Ini ou CSS)
````
```ini
[Texto em Azul]
```
````
````
```css
.TextoAzul
```
````

#### 🟡 Amarelo (Fix)
````
```fix
Texto em Amarelo
```
````

#### 🟠 Laranja (CSS)
````
```css
[Texto em Laranja]
```
````

#### 🌊 Ciano (Yaml)
````
```yaml
Texto em Ciano
```
````

## 🛠️ Instalação Técnica

### Pré-requisitos

* Python 3.8+

* Conta no [Discord Developer Portal](https://discord.com/developers/applications)

### 1. Clonar e Instalar Dependências

```bash
# Instale as bibliotecas necessárias
pip install discord.py python-dotenv
````

### 2\. Configurar o `.env`

Crie um arquivo chamado `.env` na mesma pasta do código e adicione o token do seu bot:

```ini
DISCORD_TOKEN=seu_token_aqui_super_secreto
```

### 3\. Rodar o Bot

```bash
python app.py
```

## 📂 Estrutura do Projeto

  * `app.py`: Código principal contendo toda a lógica, interface e comandos.

  * `data.json`: Banco de dados automático (criado na primeira execução) que salva sorteios e participantes.

  * `.env`: Arquivo de segurança para guardar seu Token.

## 📸 Permissões Necessárias

No portal de desenvolvedor do Discord, certifique-se de ativar:

1.  **Message Content Intent** (Necessário para ler mensagens, embora este bot use Slash Commands).

2.  No servidor, o bot precisa de permissão para **"Ver Canais"**, **"Enviar Mensagens"** e **"Inserir Links"**.
