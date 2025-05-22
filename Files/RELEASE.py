from openai import OpenAI
import os
import ast
import re

client = OpenAI(api_key = "API_KEY")

SAVE_FILE = "status_iniciais.txt"
HISTORICO_PREFIX = "chat_history_"

def carregar_config():
    personagens = {}
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
                    personagens[nome] = valores
                except Exception as e:
                    print(f"Erro lendo save do {nome}: {e}")
    return personagens

def salvar_config(personagens):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for personagen, valores in personagens.items():
            f.write(f"{personagen} = {valores}\n")

def criar_personagens_manual():
    personagens = {}
    n = int(input("Quantos Persongens deseja criar? "))

    for i in range(1, n+1):
        print(f"\nConfiguração do personagen {i}:")
        nome = input("Digite o nome do personagen: ").strip()
        while not nome or nome in personagens:
            if not nome:
                print("Nome inválido, digite novamente.")
            else:
                print("Nome já usado, digite outro.")
            nome = input("Digite o nome do personagen: ").strip()

        papel = input("Digite o papel (ex: Mestre de RPG, Guerreiro): ").strip()
        config_world = input("Digite a lore do mundo: ").strip()
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

        personagens[nome] = [
            papel,
            config_world,
            [vida_max],
            [mana_max],
            [energia_max],
            dinheiro,
            itens
        ]

    salvar_config(personagens)
    print("\nConfiguração criada e salva em save.txt")
    return personagens

def carregar_historico(personagen_name):
    historico = []
    arquivo = HISTORICO_PREFIX + personagen_name + ".txt"
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

def salvar_par_mensagem(personagen_name, user_msg, personagen_msg):
    arquivo = HISTORICO_PREFIX + personagen_name + ".txt"
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(str([user_msg, personagen_msg]) + "\n")

def Talk(personagen_name, papel, chat_history, texto_usuario):
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
    salvar_par_mensagem(personagen_name, texto_usuario, reply)
    return reply

def mostrar_inventario(personagen_name, estado):
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

        print(f"\n📦 Inventário de {personagen_name}:")
        print(f"  ❤️ Vida:     {vida_atual}/{vida_max}")
        print(f"  🔵 Mana:     {mana_atual}/{mana_max}")
        print(f"  ⚡ Energia:  {energia_atual}/{energia_max}")
        print(f"  💰 Dinheiro: {dinheiro}")
        print(f"  🎒 Itens:    {', '.join(itens) if itens else 'nenhum'}")
    else:
        print(f"\n📦 Inventário de {personagen_name}: não foi possível extrair os dados.")

def abrir_mercado(estados, personagens):
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
        personagen_name = input("Digite o nome do personagen que irá interagir no mercado: ").strip()
        if personagen_name.lower() == "sair":
            break
        if personagen_name not in estados:
            print("❌ Personagen não encontrado.")
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

            personagen_info = personagens[personagen_name]
            dinheiro = personagen_info[4]
            custo_total = preco * quantidade

            if dinheiro < custo_total:
                print(f"💸 Dinheiro insuficiente. Você precisa de {custo_total} moedas.")
                continue

            confirmar = input(f"Confirma compra de {quantidade}x '{item_escolhido}' por {custo_total} moedas? (sim/não) ").strip().lower()
            if confirmar != "sim":
                print("Compra cancelada.")
                continue

            # Finaliza compra
            personagen_info[4] -= custo_total
            for _ in range(quantidade):
                personagen_info[5].append(item_escolhido)
            loja[item_escolhido][1] -= quantidade

            # Atualiza papel
            config_world, papel, vida, mana, energia, dinheiro, itens = valores
            papel_completo = (
                f"Você é {papel}. Vida: {vida[0]}, Mana: {mana[0]}, "
                f"Energia: {energia[0]}, Dinheiro: {dinheiro}, Itens: {itens}.\n"
                f"Você deve obedecer a historia do mundo que é: {config_world[0]}"
                "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
                "Quando rolar um dado seja qual for o numero de lados eles devem ter chances iguais ou seja se eu tiver um lado de 6 lado cada lado tem 16.666%% e vai seguindo com esta regra"
                "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."
            )
            estados[personagen_name]["papel"] = papel_completo
            salvar_config(personagens)

            print(f"✅ {personagen_name} comprou {quantidade}x '{item_escolhido}' por {custo_total} moedas.")

        elif acao == "vender":
            personagen_info = personagens[personagen_name]
            inventario = personagen_info[5]
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
            personagen_info[4] += valor_total

            # Atualiza estoque da loja (aumenta)
            if item_escolhido in loja:
                loja[item_escolhido][1] += quantidade
            else:
                loja[item_escolhido] = [preco_venda * 2, quantidade]  # recria item com preço padrão

            # Atualiza papel
            config_world, papel, vida, mana, energia, dinheiro, itens = valores
            papel_completo = (
                f"Você é {papel}. Vida: {vida[0]}, Mana: {mana[0]}, "
                f"Energia: {energia[0]}, Dinheiro: {dinheiro}, Itens: {itens}.\n"
                f"Você deve obedecer a historia do mundo que é: {config_world[0]}"
                "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
                "Quando rolar um dado seja qual for o numero de lados eles devem ter chances iguais ou seja se eu tiver um lado de 6 lado cada lado tem 16.666%% e vai seguindo com esta regra"
                "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."
            )
            estados[personagen_name]["papel"] = papel_completo
            salvar_config(personagens)

            print(f"✅ {personagen_name} vendeu {quantidade}x '{item_escolhido}' e recebeu {valor_total} moedas.")



def main():
    personagens = carregar_config()
    if not personagens:
        personagens = criar_personagens_manual()

    estados = {}
    for personagen_name, valores in personagens.items():
        config_world, papel, vida, mana, energia, dinheiro, itens = valores
        papel_completo = (
            f"Você é {papel}. Vida: {vida[0]}, Mana: {mana[0]}, "
            f"Energia: {energia[0]}, Dinheiro: {dinheiro}, Itens: {itens}.\n"
            f"Você deve obedecer a historia do mundo que é: {config_world[0]}"
            "Você é um personagem de RPG e deve responder somente dentro do contexto do jogo. "
            "Quando rolar um dado seja qual for o numero de lados eles devem ter chances iguais ou seja se eu tiver um lado de 6 lado cada lado tem 16.666%% e vai seguindo com esta regra"
            "Nunca diga que é uma IA ou que ajuda fora do jogo. Seja criativo e mantenha o papel."

        )
        chat_history = carregar_historico(personagen_name)
        estados[personagen_name] = {"papel": papel_completo, "history": chat_history}

    personagen_ativo = None

    def escolher_personagen():
        nonlocal personagen_ativo
        print("Personagens disponíveis:")
        print("0. Geral (todos os personagens)")
        for i, personagen_name in enumerate(estados.keys(), 1):
            print(f"{i}. {personagen_name}")
        escolha = input("Escolha o número do personagen para usar: ").strip()
        if escolha.isdigit():
            indice = int(escolha)
            if indice == 0:
                personagen_ativo = "geral"
                print("Modo geral ativado: mensagens enviadas para todos os personagens.\n")
            elif 1 <= indice <= len(estados):
                personagen_ativo = list(estados.keys())[indice - 1]
                print(f"Personagen ativo: {personagen_ativo}\n")
            else:
                print("Número inválido.\n")
                escolher_personagen()
        else:
            print("Entrada inválida. Digite o número do personagen.\n")
            escolher_personagen()

    escolher_personagen()

    print("Console geral ativo. Digite 'exit' para sair.")
    print("Digite 'trocar' para mudar o personagen ativo.")
    print("Digite 'inventario' para ver inventário do personagen ativo (não disponível no modo geral).")
    print("Digite 'mercado' para abrir mercado.\n")

    while True:
        prompt = f"{personagen_ativo} > " if personagen_ativo != "geral" else "Geral > "
        texto = input(prompt).strip()

        if texto.lower() == "exit":
            print("Finalizando o console. Até mais!")
            break

        if texto.lower() == "trocar":
            escolher_personagen()
            continue

        if texto.lower() == "inventario":
            if personagen_ativo == "geral":
                print("No modo geral não é possível mostrar inventário. Escolha um personagen específico.\n")
            else:
                mostrar_inventario(personagen_ativo, estados[personagen_ativo])
            continue

        if texto.lower() == "mercado":
            abrir_mercado(estados, personagens)
            continue

        # Enviar para personagen específico usando PersonagenNome: mensagem
        if ":" in texto:
            possivel_personagen, mensagem = texto.split(":", 1)
            possivel_personagen = possivel_personagen.strip()
            mensagem = mensagem.strip()
            if possivel_personagen in estados:
                resposta = Talk(possivel_personagen, estados[possivel_personagen]["papel"], estados[possivel_personagen]["history"], mensagem)
                print(f"{possivel_personagen}: {resposta}\n")
                continue
            else:
                print(f"Personagen '{possivel_personagen}' não encontrado.\n")
                continue

        # Se modo geral, envia para todos
        if personagen_ativo == "geral":
            for personagen_name, estado in estados.items():
                resposta = Talk(personagen_name, estado["papel"], estado["history"], texto)
                print(f"{personagen_name}: {resposta}")
            print()
        else:
            resposta = Talk(personagen_ativo, estados[personagen_ativo]["papel"], estados[personagen_ativo]["history"], texto)
            print(f"{personagen_ativo}: {resposta}\n")


if __name__ == "__main__":
    main()
