from pathlib import Path
from collections import defaultdict, Counter
import csv
import random
import shutil

ORIGEM = Path("./dataset_classificacao")
DESTINO = Path("./dataset_yolo")

SEMENTE = 42
PROPORCOES = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15,
}

CLASSES = [
    "1_Muito_Desgastada",
    "2_Desgastada",
    "3_Conservada",
]

EXTENSOES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def identificar_imagem(caminho):
    """
    Espera nomes no formato:
    classe_rua_tag_num.ext

    Exemplo:
    1_Muito_Desgastada_Andrade_Neves_a_1.jpg
    """
    stem = caminho.stem

    classe = next(
        (c for c in CLASSES if stem.startswith(c + "_")),
        None,
    )

    if classe is None:
        raise ValueError(
            f"Não foi possível identificar a classe: {caminho.name}"
        )

    restante = stem[len(classe) + 1:]
    partes = restante.split("_")

    if len(partes) < 3 or not partes[-1].isdigit():
        raise ValueError(
            f"Nome fora do padrão classe_rua_tag_num: {caminho.name}"
        )

    # O número final identifica a imagem.
    # A penúltima parte identifica a tag.
    # As partes intermediárias identificam a rua.
    rua = "_".join(partes[:-2])
    tag = partes[-2]

    if not rua or not tag:
        raise ValueError(f"Rua ou tag inválida: {caminho.name}")

    return classe, rua, tag


def distribuir_grupos(grupos):
    """
    Distribui grupos inteiros entre train, val e test.
    Busca aproximar as proporções por classe sem dividir grupos.
    """
    rng = random.Random(SEMENTE)

    imagens_por_classe = Counter()
    for grupo in grupos.values():
        imagens_por_classe[grupo["classe"]] += len(grupo["imagens"])

    total = sum(imagens_por_classe.values())

    alvos = {
        split: {
            classe: total_classe * proporcao
            for classe, total_classe in imagens_por_classe.items()
        }
        for split, proporcao in PROPORCOES.items()
    }

    alvos_total = {
        split: total * proporcao
        for split, proporcao in PROPORCOES.items()
    }

    # Grupos maiores primeiro; desempate aleatório reproduzível.
    itens = list(grupos.items())
    rng.shuffle(itens)
    itens.sort(key=lambda item: len(item[1]["imagens"]), reverse=True)

    distribuicao = {
        split: Counter()
        for split in PROPORCOES
    }
    atribuicoes = {}

    for chave, grupo in itens:
        classe = grupo["classe"]
        tamanho = len(grupo["imagens"])

        melhor_split = None
        melhor_custo = float("inf")

        for split in PROPORCOES:
            custo = 0.0

            # Erro de quantidade total do conjunto.
            novo_total = sum(distribuicao[split].values()) + tamanho
            custo += (
                (novo_total - alvos_total[split])
                / max(alvos_total[split], 1)
            ) ** 2

            # Erro na quantidade desta classe.
            atual = distribuicao[split][classe]
            alvo = alvos[split][classe]

            custo += 2.0 * (
                (atual + tamanho - alvo)
                / max(alvo, 1)
            ) ** 2

            if custo < melhor_custo:
                melhor_custo = custo
                melhor_split = split

        atribuicoes[chave] = melhor_split
        distribuicao[melhor_split][classe] += tamanho

    return atribuicoes


def preparar_dataset():
    if not ORIGEM.is_dir():
        raise FileNotFoundError(
            f"Dataset original não encontrado: {ORIGEM.resolve()}"
        )

    # Evita misturar arquivos de execuções anteriores.
    if DESTINO.exists() and any(DESTINO.iterdir()):
        raise FileExistsError(
            f"O destino não está vazio: {DESTINO.resolve()}\n"
            "Escolha outra pasta ou esvazie o destino manualmente."
        )

    DESTINO.mkdir(parents=True, exist_ok=True)

    # Cada grupo representa classe + rua + tag.
    grupos = defaultdict(lambda: {
        "classe": None,
        "imagens": [],
    })

    for imagem in sorted(ORIGEM.rglob("*")):
        if not imagem.is_file():
            continue

        if imagem.suffix.lower() not in EXTENSOES:
            continue

        classe, rua, tag = identificar_imagem(imagem)

        chave = (classe, rua, tag)
        grupos[chave]["classe"] = classe
        grupos[chave]["imagens"].append(imagem)

    if not grupos:
        raise RuntimeError("Nenhuma imagem válida encontrada.")

    atribuicoes = distribuir_grupos(grupos)

    manifest = []

    for chave, grupo in grupos.items():
        split = atribuicoes[chave]
        classe = grupo["classe"]

        pasta = DESTINO / split / classe
        pasta.mkdir(parents=True, exist_ok=True)

        for imagem in grupo["imagens"]:
            destino = pasta / imagem.name

            if destino.exists():
                raise FileExistsError(
                    f"Arquivo duplicado no destino: {destino}"
                )

            shutil.copy2(imagem, destino)

            manifest.append({
                "split": split,
                "classe": classe,
                "rua": chave[1],
                "tag": chave[2],
                "nome": imagem.name,
                "origem": str(imagem),
                "destino": str(destino),
            })

    # Manifesto para auditoria e rastreabilidade.
    arquivo_manifesto = DESTINO / "manifest.csv"

    campos = [
        "split", "classe", "rua", "tag",
        "nome", "origem", "destino",
    ]

    with arquivo_manifesto.open(
        "w", newline="", encoding="utf-8-sig"
    ) as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(manifest)

    # Relatório de distribuição.
    contagem = {
        split: Counter()
        for split in PROPORCOES
    }

    for item in manifest:
        contagem[item["split"]][item["classe"]] += 1

    print("\nQuantidade de imagens por conjunto:")
    for split in PROPORCOES:
        total_split = sum(contagem[split].values())
        print(f"\n{split}: {total_split} imagens")
        for classe in CLASSES:
            print(f"  {classe}: {contagem[split][classe]}")

    # Confirma que nenhum grupo foi dividido entre conjuntos.
    splits_por_grupo = defaultdict(set)

    for item in manifest:
        chave = (item["classe"], item["rua"], item["tag"])
        splits_por_grupo[chave].add(item["split"])

    vazamentos = {
        chave: splits
        for chave, splits in splits_por_grupo.items()
        if len(splits) > 1
    }

    if vazamentos:
        raise RuntimeError(
            f"Data leakage detectado em {len(vazamentos)} grupos."
        )

    print("\nVerificação de leakage: OK")
    print(f"Grupos: {len(grupos)}")
    print(f"Dataset: {DESTINO.resolve()}")
    print(f"Manifesto: {arquivo_manifesto.resolve()}")


if __name__ == "__main__":
    preparar_dataset()
