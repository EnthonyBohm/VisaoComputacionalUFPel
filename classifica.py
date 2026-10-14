from pathlib import Path
import csv
import re
import shutil
import unicodedata

ORIGEM = Path("./dataset_original")
DESTINO = Path("./dataset_classificacao")

CLASSES = {
    "1. Muito Desgastada": "1_Muito_Desgastada",
    "2. Desgastada": "2_Desgastada",
    "3. Conservada": "3_Conservada",
}

EXTENSOES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def normalizar(texto):
    """Normaliza nomes para uso em arquivos e diretórios."""
    texto = texto.strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9_-]+", "_", texto)
    return texto.strip("_")



def organizar_dataset():
    if not ORIGEM.is_dir():
        raise FileNotFoundError(
            f"Diretório de origem não encontrado: {ORIGEM.resolve()}"
        )

    DESTINO.mkdir(parents=True, exist_ok=True)

    manifest = []
    contadores = {}

    for classe_original, classe_nova in CLASSES.items():
        pasta_classe = ORIGEM / classe_original

        if not pasta_classe.is_dir():
            print(f"[AVISO] Pasta não encontrada: {pasta_classe}")
            continue

        for imagem in sorted(pasta_classe.rglob("*")):
            if not imagem.is_file():
                continue

            if imagem.suffix.lower() not in EXTENSOES:
                continue

            relativo = imagem.relative_to(pasta_classe)

            # Primeira pasta relativa = rua
            rua_original = (
                relativo.parts[0]
                if len(relativo.parts) > 1
                else "SemRua"
            )
            rua = normalizar(rua_original) or "SemRua"

            # Segunda pasta relativa = tag, se existir.
            # Ex.: Andrade Neves/a/imagem.jpg -> tag "a"
            # Ex.: Goncalves/imagem.jpg -> tag "SemTag"
            tag_original = (
                relativo.parts[1]
                if len(relativo.parts) > 2
                else "SemTag"
            )
            tag = normalizar(tag_original) or "SemTag"

            # Contador independente para cada combinação
            # de classe, rua e tag.
            grupo = (classe_nova, rua, tag)
            contadores[grupo] = contadores.get(grupo, 0) + 1

            destino_pasta = DESTINO / classe_nova
            destino_pasta.mkdir(parents=True, exist_ok=True)

            extensao = imagem.suffix.lower()

            while True:
                numero = contadores[grupo]
                nome_novo = (
                    f"{classe_nova}_{rua}_{tag}_{numero}{extensao}"
                )
                destino_imagem = destino_pasta / nome_novo

                contadores[grupo] += 1

                if not destino_imagem.exists():
                    break

            shutil.copy2(imagem, destino_imagem)

            manifest.append({
                "classe": classe_original,
                "rua": rua_original,
                "tag": tag_original,
                "nome_original": imagem.name,
                "caminho_original": str(imagem),
                "nome_novo": nome_novo,
                "caminho_novo": str(destino_imagem),
            })

    arquivo_csv = DESTINO / "manifest.csv"

    campos = [
        "classe",
        "rua",
        "tag",
        "nome_original",
        "caminho_original",
        "nome_novo",
        "caminho_novo",
    ]

    with arquivo_csv.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(manifest)

    print(f"Imagens organizadas: {len(manifest)}")
    print(f"Dataset: {DESTINO.resolve()}")
    print(f"Manifesto: {arquivo_csv.resolve()}")


if __name__ == "__main__":
    organizar_dataset()
