"""Atualiza o trvl.exe sozinho, com volta para a versao anterior se o Windows bloquear.

Roda no inicio de cada sessao do Claude Code (hook SessionStart), no maximo uma vez
por dia. Delega a atualizacao ao `trvl self-update`, que ja verifica SHA-256 e a
assinatura ML-DSA-65 antes de trocar o binario e aborta sem tocar em nada se algo
falhar.

O que o self-update nao cobre, e este script cobre: o Controle de Aplicativo do
Windows. Ele bloqueou o trvl uma vez, e um binario novo tem hash novo - pode ser
bloqueado de novo. Sem protecao, a atualizacao trocaria um trvl que funciona por um
que nao abre. Por isso: copia de seguranca antes, teste depois, e volta a copia se a
versao nova nao rodar.

Nunca derruba a sessao: qualquer erro vira aviso e o script sai com codigo 0.

Uso:
    python ferramentas/atualizar_trvl.py            # respeita o intervalo de 1 dia
    python ferramentas/atualizar_trvl.py --forcar   # checa agora
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INTERVALO = 24 * 3600


def avisar(texto):
    """SessionStart mostra `systemMessage` ao usuario; silencio quando nada mudou."""
    print(json.dumps({"systemMessage": texto}, ensure_ascii=False))


def binario():
    try:
        mcp = json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8"))
        return Path(mcp["mcpServers"]["trvl"]["command"])
    except (OSError, ValueError, KeyError):
        return None


def rodar(exe, *args, timeout=60):
    """(codigo, saida). Binario bloqueado pelo Windows levanta OSError: vira codigo -1."""
    try:
        r = subprocess.run([str(exe), *args], capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, str(e)


def versao(exe):
    cod, saida = rodar(exe, "version")
    m = re.search(r"trvl\s+v?(\d+\.\d+\.\d+)", saida)
    return (m.group(1) if cod == 0 and m else None), saida


def principal(forcar):
    exe = binario()
    if exe is None or not exe.is_file():
        return  # sem trvl configurado nesta maquina: nada a fazer

    marca = exe.parent / ".ultima-checagem-partiu"
    if not forcar and marca.is_file() and time.time() - marca.stat().st_mtime < INTERVALO:
        return

    atual, _ = versao(exe)
    if atual is None:
        avisar("trvl nao abre (bloqueado pelo Windows?). Atualizacao automatica "
               "pulada; libere em Seguranca do Windows > Controle de aplicativos.")
        return

    cod, saida = rodar(exe, "self-update", "--check")
    marca.touch()
    m = re.search(r"update to v?(\d+\.\d+\.\d+) is available", saida)
    if cod != 0 or not m:
        return  # em dia, ou checagem sem resposta: tenta de novo amanha
    alvo = m.group(1)

    copia = exe.with_name(exe.name + ".anterior")
    shutil.copy2(exe, copia)

    cod, saida = rodar(exe, "self-update", timeout=300)
    nova, detalhe = versao(exe)

    if nova == alvo:
        avisar(f"trvl atualizado sozinho: {atual} -> {nova}.")
        return

    if nova == atual:
        # O self-update abortou sem tocar no binario - comportamento dele em
        # verificacao falha. Nada a desfazer.
        avisar(f"trvl {alvo} disponivel, mas a atualizacao nao foi aplicada "
               f"(verificacao do self-update). Continua em {atual}.")
        return

    # Binario trocado e nao roda: o caso que o self-update nao cobre.
    try:
        shutil.copy2(copia, exe)
        voltou, _ = versao(exe)
    except OSError as e:
        voltou, detalhe = None, str(e)
    if voltou == atual:
        avisar(f"trvl {alvo} foi baixado mas nao abre - provavelmente bloqueado pelo "
               f"Controle de Aplicativo do Windows. Voltei para {atual}, que funciona. "
               f"Para usar a nova, libere o trvl em Seguranca do Windows e rode "
               f"`python ferramentas/atualizar_trvl.py --forcar`.")
    else:
        avisar(f"ATENCAO: a atualizacao do trvl para {alvo} falhou e a volta para "
               f"{atual} tambem. A copia esta em {copia}. Detalhe: {detalhe[:200]}")


if __name__ == "__main__":
    try:
        principal("--forcar" in sys.argv)
    except Exception as e:  # nunca derrubar o inicio da sessao
        avisar(f"Atualizacao automatica do trvl falhou: {e}")
    sys.exit(0)
