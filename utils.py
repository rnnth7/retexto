def autoriaFormatada(autoresList):
    if not autoresList:  # Verifica se a lista está vazia
        return ""

    if len(autoresList) == 1:
        return autoresList[0] + "."

    return ", ".join(autoresList[:-1]) + " e " + autoresList[-1] + "."