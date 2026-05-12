import os
import sys
from datetime import datetime

import requests

# Identificador da unidade na API (Sapiranga = 4). Teste /api/occupancy/1, 2, … até aparecer sua filial.
OCCUPANCY_BRANCH_ID = (os.environ.get("OCCUPANCY_BRANCH_ID") or "4").strip()

# Base da API (mesmo domínio do site; não usar webhook aqui).
OCCUPANCY_API_TEMPLATE = os.environ.get(
    "OCCUPANCY_API_TEMPLATE",
    "https://26fit.com.br/api/occupancy/{branch_id}",
).strip()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()


def _valid_http(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def fetch_occupancy():
    """Lê ocupação pela API REST usada pelo site (não depende do React no browser)."""
    if not OCCUPANCY_BRANCH_ID:
        raise ValueError(
            "Defina OCCUPANCY_BRANCH_ID (ex.: 4 para 26FIT Sapiranga). "
            "Outras unidades: teste https://26fit.com.br/api/occupancy/1 até achar pelo nome da filial."
        )

    api_url = OCCUPANCY_API_TEMPLATE.format(branch_id=OCCUPANCY_BRANCH_ID)
    if not _valid_http(api_url):
        raise ValueError(
            "OCCUPANCY_API_TEMPLATE precisa começar com https:// "
            '(ex.: "https://26fit.com.br/api/occupancy/{branch_id}").'
        )

    r = requests.get(
        api_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; monitor/1.0)", "Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()

    if not data.get("success") or not data.get("current"):
        raise ValueError("API retornou sem dados de ocupação (current vazio).")

    cur = data["current"]
    name = str(cur.get("name", "Unidade")).strip()
    alunos = int(cur.get("occupation", 0))
    cap = int(cur.get("maxOccupation") or 0)
    if cap <= 0:
        pct = None
    else:
        pct = max(0, min(100, round(100 * alunos / cap)))

    last = str(data.get("lastUpdated") or "").strip()
    return name, alunos, cap, pct, last


def send_discord(name: str, alunos: int, cap: int, pct: int | None, last: str):
    if not _valid_http(DISCORD_WEBHOOK_URL):
        print(
            "Discord: defina DISCORD_WEBHOOK_URL com uma URL https:// válida. "
            "Mensagem não enviada."
        )
        return

    now = datetime.now().strftime("%H:%M")
    if pct is not None and cap > 0:
        msg = f"🕒 {now} | 🏋️ {name}\n**{pct}%** da capacidade · **{alunos}** alunos (máx. {cap})"
    else:
        msg = f"🕒 {now} | 🏋️ {name}\n**{alunos}** alunos (capacidade não informada)"
    if last:
        msg += f"\n_Atualizado: {last}_"

    requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": msg},
        timeout=30,
    )


def main():
    try:
        if os.environ.get("GITHUB_ACTIONS") == "true" and not _valid_http(
            DISCORD_WEBHOOK_URL
        ):
            raise ValueError(
                "Configure o secret DISCORD_WEBHOOK_URL em Settings → Secrets "
                "and variables → Actions neste repositório."
            )
        name, alunos, cap, pct, last = fetch_occupancy()
        send_discord(name, alunos, cap, pct, last)
        print("OK")
    except Exception as e:
        print(e, file=sys.stderr)
        if _valid_http(DISCORD_WEBHOOK_URL):
            try:
                requests.post(
                    DISCORD_WEBHOOK_URL,
                    json={"content": f"ERRO: {e}"},
                    timeout=30,
                )
            except Exception as post_err:
                print(post_err, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
