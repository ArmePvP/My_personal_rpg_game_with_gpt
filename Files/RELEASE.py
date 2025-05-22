from openai import OpenAI
import os
import ast
import re

client = OpenAI(api_key = "API_KEY")

SAVE_FILE = "status_iniciais.txt"
HISTORICO_PREFIX = "chat_history_"

def carregar_config():
    bots = {}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or "=" not in linha:
                    continue
                nome, dados = linha.split("=", 1)
                nome = nome.strip()
                try:
                    valores = ast.literal_eval(dados.strip())
                    bots[nome] = valores
                except Exception as e:
                    print(f"Erro lendo save do {nome}: {e}")
    return bots

def salvar_config(bots):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for bot, valores in bots.items():
            f.write(f"{bot} = {valores}\n")

def criar_bots_manual():
    bots = {}
    n = int(input("Quantos bots deseja criar? "))

    for i in range(1, n+1):
        print(f"\nConfiguração do bot {i}:")
        nome = input("Digite o nome do bot: ").strip()
        while not nome or nome in bots:
            if not nome:
                print("Nome inválido, digite novamente.")
            else:
                print("Nome já usado, digite outro.")
            nome = input("Digite o nome do bot: ").strip()

        papel = input("Digite o papel (ex: Mestre de RPG, Guerreiro): ").strip()

        def obter_inteiro(mensagem):
            while True:
                valor_str = input(mensagem).strip()
                if valor_str.isdigit() or (valor_str.startswith('-') and valor_str[1:].isdigit()):
                    return int(valor_str)
                else:
                    print("Valor inválido! Digite um número inteiro (pode ser negativo).")

        vida_max = obter_inteiro("Digite VIDA MÁXIMA: ")
        mana_max = obter_inteiro("Digite MANA MÁXIMA: ")
        energia_max = obter_inteiro("Digite ENERGIA MÁXIMA: ")

        vida_atual = vida_max
        mana_atual = mana_max
        energia_atual = energia_max

        dinheiro = obter_inteiro("Digite dinheiro (número inteiro): ")



        itens_str = input("Digite os itens separados por vírgula (ex: espada, escudo): ").strip()
        itens = [item.strip() for item in itens_str.split(",")] if itens_str else []

        bots[nome] = [
            papel,
            [vida_atual, vida_max],
            [mana_atual, mana_max],
            [energia_atual, energia_max],
            dinheiro,
            itens
        ]

    salvar_config(bots)
    print("\nConfiguração criada e salva em save.txt")
    return bots

def carregar_historico(bot_name):
    historico = []
    arquivo = HISTORICO_PREFIX + bot_name + ".txt"
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    par = ast.literal_eval(linha.strip())
                    if isinstance(par, list) and len(par) == 2:
                        historico.append({"role": "user", "content": par[0]})
                        historico.append({"role": "assistant", "content": par[1]})
                except:
                    continue
    return historico

def salvar_par_mensagem(bot_name, user_msg, bot_msg):
    arquivo = HISTORICO_PREFIX + bot_name + ".txt"
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(str([user_msg, bot_msg]) + "\n")

def Talk(bot_name, papel, chat_history, texto_usuario):
    mensagens = [{"role": "system", "content": papel}]
    mensagens += [msg for msg in chat_history if msg["role"] != "system"]
    mensagens.append({"role": "user", "content": texto_usuario})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens
    )
    reply = resposta.choices[0].message.content
    chat_history.append({"role": "user", "content": texto_usuario})
    chat_history.append({"role": "assistant", "content": reply})
    salvar_par_mensagem(bot_name, texto_usuario, reply)
    return reply

def mostrar_inventario(bot_name, estado):
    papel = estado["papel"]

    # Extração limpa das informações
    
    match = re.search(
        r"Vida:\s*(\d+)/(\d+),\s*Mana:\s*(\d+)/(\d+),\s*Energia:\s*(\d+)/(\d+),\s*Dinheiro:\s*(\d+),\s*Itens:\s*(\[.*?\])",
        papel
    )
    if match:
        vida_atual, vida_max = match.group(1), match.group(2)
        mana_atual, mana_max = match.group(3), match.group(4)
        energia_atual, energia_max = match.group(5), match.group(6)
        dinheiro = match.group(7)
        itens_str = match.group(8)
        try:
            itens = ast.literal_eval(itens_str)
        except:
            itens = []

        print(f"\n📦 Inventário de {bot_name}:")
        print(f"  ❤️ Vida:     {vida_atual}/{vida_max}")
        print(f"  🔵 Mana:     {mana_atual}/{mana_max}")
        print(f"  ⚡ Energia:  {energia_atual}/{energia_max}")
        print(f"  💰 Dinheiro: {dinheiro}")
        print(f"  🎒 Itens:    {', '.join(itens) if itens else 'nenhum'}")
    else:
        print(f"\n📦 Inventário de {bot_name}: não foi possível extrair os dados.")

def abrir_mercado(estados, bots):
    # Estoque da loja: item -> [preço, quantidade disponível]
    loja = {
        "poção de vida": [10, 20],
        "poção de mana": [12, 15],
        "espada de ferro": [50, 5],
        "escudo de madeira": [30, 7]
    }

    while True:
        print("\n🛒 Loja de Itens:")
        for item, (preco, qtd) in loja.items():
            print(f"  - {item.title()} (Preço: {preco} moedas, Estoque: {qtd})")

        print("\nDigite 'sair' para voltar.")
        bot_name = input("Digite o nome do bot que irá interagir no mercado: ").strip()
        if bot_name.lower() == "sair":
            break
        if bot_name not in estados:
            print("❌ Bot não encontrado.")
            continue

        acao = input("Deseja [comprar] ou [vender]? ").strip().lower()
        if acao == "sair":
            break
        if acao not in ["comprar", "vender"]:
            print("Opção inválida. Tente novamente.")
            continue

        if acao == "comprar":
            item_escolhido = input("Digite o nome do item para comprar: ").strip().lower()
            if item_escolhido not in loja:
                print("❌ Item não encontrado na loja.")
                continue
            preco, estoque = loja[item_escolhido]
            if estoque == 0:
                print("❌ Item esgotado na loja.")
                continue

            try:
                quantidade = int(input(f"Quantas unidades de '{item_escolhido}' deseja comprar? (estoque: {estoque}): "))
            except:
                print("Quantidade inválida.")
                continue
            if quantidade <= 0 or quantidade > estoque:
                print("Quantidade inválida ou acima do estoque.")
                continue

            bot_info = bots[bot_name]
            dinheiro = bot_info[4]
            custo_total = preco * quantidade

            if dinheiro < custo_total:
                print(f"💸 Dinheiro insuficiente. Você precisa de {custo_total} moedas.")
                continue

            confirmar = input(f"Confirma compra de {quantidade}x '{item_escolhido}' por {custo_total} moedas? (sim/não) ").strip().lower()
            if confirmar != "sim":
                print("Compra cancelada.")
                continue

            # Finaliza compra
            bot_info[4] -= custo_total
            for _ in range(quantidade):
                bot_info[5].append(item_escolhido)
            loja[item_escolhido][1] -= quantidade

            # Atualiza papel
            papel, vida, mana, energia, dinheiro, itens = bot_info
            papel_completo = (
                f"Você é {papel}. Vida: {vida[0]}/{vida[1]}, Mana: {mana[0]}/{mana[1]}, "
                f"Energia: {energia[0]}/{energia[1]}, Dinheiro: {bot_info[4]}, Itens: {bot_info[5]}.\n"
                "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
                "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."
            )
            estados[bot_name]["papel"] = papel_completo
            salvar_config(bots)

            print(f"✅ {bot_name} comprou {quantidade}x '{item_escolhido}' por {custo_total} moedas.")

        elif acao == "vender":
            bot_info = bots[bot_name]
            inventario = bot_info[5]
            if not inventario:
                print("❌ Inventário vazio, nada para vender.")
                continue
            print(f"Seu inventário: {', '.join(inventario)}")
            item_escolhido = input("Digite o nome do item para vender: ").strip().lower()
            if item_escolhido not in inventario:
                print("❌ Item não encontrado no inventário.")
                continue

            quantidade_disponivel = inventario.count(item_escolhido)
            try:
                quantidade = int(input(f"Quantas unidades de '{item_escolhido}' deseja vender? (você tem: {quantidade_disponivel}): "))
            except:
                print("Quantidade inválida.")
                continue
            if quantidade <= 0 or quantidade > quantidade_disponivel:
                print("Quantidade inválida.")
                continue

            # Define preço de venda (ex: 50% do preço da loja ou preço fixo)
            preco_venda = loja.get(item_escolhido, [0, 0])[0] // 2
            if preco_venda == 0:
                preco_venda = 1  # preço mínimo

            valor_total = preco_venda * quantidade
            confirmar = input(f"Confirma venda de {quantidade}x '{item_escolhido}' por {valor_total} moedas? (sim/não) ").strip().lower()
            if confirmar != "sim":
                print("Venda cancelada.")
                continue

            # Remove do inventário
            for _ in range(quantidade):
                inventario.remove(item_escolhido)

            # Adiciona dinheiro
            bot_info[4] += valor_total

            # Atualiza estoque da loja (aumenta)
            if item_escolhido in loja:
                loja[item_escolhido][1] += quantidade
            else:
                loja[item_escolhido] = [preco_venda * 2, quantidade]  # recria item com preço padrão

            # Atualiza papel
            papel, vida, mana, energia, dinheiro, itens = bot_info
            papel_completo = (
                f"Você é {papel}. Vida: {vida[0]}/{vida[1]}, Mana: {mana[0]}/{mana[1]}, "
                f"Energia: {energia[0]}/{energia[1]}, Dinheiro: {bot_info[4]}, Itens: {bot_info[5]}.\n"
                "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
                "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."
            )
            estados[bot_name]["papel"] = papel_completo
            salvar_config(bots)

            print(f"✅ {bot_name} vendeu {quantidade}x '{item_escolhido}' e recebeu {valor_total} moedas.")



def main():
    bots = carregar_config()
    if not bots:
        bots = criar_bots_manual()

    estados = {}
    for bot_name, valores in bots.items():
        papel, vida, mana, energia, dinheiro, itens = valores
        papel_completo = (
            f"Você é {papel}. Vida: {vida[0]}/{vida[1]}, Mana: {mana[0]}/{mana[1]}, "
            f"Energia: {energia[0]}/{energia[1]}, Dinheiro: {dinheiro}, Itens: {itens}.\n"
            "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
            "Quando rolar um dado seja qual for o numero de lados eles devem ter chances iguais ou seja se eu tiver um lado de 6 lado cada lado tem 16.666%% e vai seguindo com esta regra"           "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."
        )
        chat_history = carregar_historico(bot_name)
        estados[bot_name] = {"papel": papel_completo, "history": chat_history}

    bot_ativo = None

    def escolher_bot():
        nonlocal bot_ativo
        print("Bots disponíveis:")
        print("0. Geral (todos os bots)")
        for i, bot_name in enumerate(estados.keys(), 1):
            print(f"{i}. {bot_name}")
        escolha = input("Escolha o número do bot para usar: ").strip()
        if escolha.isdigit():
            indice = int(escolha)
            if indice == 0:
                bot_ativo = "geral"
                print("Modo geral ativado: mensagens enviadas para todos os bots.\n")
            elif 1 <= indice <= len(estados):
                bot_ativo = list(estados.keys())[indice - 1]
                print(f"Bot ativo: {bot_ativo}\n")
            else:
                print("Número inválido.\n")
                escolher_bot()
        else:
            print("Entrada inválida. Digite o número do bot.\n")
            escolher_bot()

    escolher_bot()

    print("Console geral ativo. Digite 'exit' para sair.")
    print("Digite 'trocar' para mudar o bot ativo.")
    print("Digite 'inventario' para ver inventário do bot ativo (não disponível no modo geral).")
    print("Digite 'mercado' para abrir mercado.\n")

    while True:
        prompt = f"{bot_ativo} > " if bot_ativo != "geral" else "Geral > "
        texto = input(prompt).strip()

        if texto.lower() == "exit":
            print("Finalizando o console. Até mais!")
            break

        if texto.lower() == "trocar":
            escolher_bot()
            continue

        if texto.lower() == "inventario":
            if bot_ativo == "geral":
                print("No modo geral não é possível mostrar inventário. Escolha um bot específico.\n")
            else:
                mostrar_inventario(bot_ativo, estados[bot_ativo])
            continue

        if texto.lower() == "mercado":
            abrir_mercado(estados, bots)
            continue

        # Enviar para bot específico usando BotNome: mensagem
        if ":" in texto:
            possivel_bot, mensagem = texto.split(":", 1)
            possivel_bot = possivel_bot.strip()
            mensagem = mensagem.strip()
            if possivel_bot in estados:
                resposta = Talk(possivel_bot, estados[possivel_bot]["papel"], estados[possivel_bot]["history"], mensagem)
                print(f"{possivel_bot}: {resposta}\n")
                continue
            else:
                print(f"Bot '{possivel_bot}' não encontrado.\n")
                continue

        # Se modo geral, envia para todos
        if bot_ativo == "geral":
            for bot_name, estado in estados.items():
                resposta = Talk(bot_name, estado["papel"], estado["history"], texto)
                print(f"{bot_name}: {resposta}")
            print()
        else:
            resposta = Talk(bot_ativo, estados[bot_ativo]["papel"], estados[bot_ativo]["history"], texto)
            print(f"{bot_ativo}: {resposta}\n")


if __name__ == "__main__":
    main()