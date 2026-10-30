"""O `--help` do cambio.py quebrava com ValueError: argparse formata o texto de
ajuda com %, e o percentual do spread padrao entrava sem escapar. Ninguem notou
porque o script so era chamado com argumentos."""
import subprocess
import sys
from pathlib import Path

CAMBIO = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "cambio-br" / "scripts" / "cambio.py"


def test_help_do_cambio_nao_quebra():
    r = subprocess.run([sys.executable, str(CAMBIO), "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-300:]
    assert "%" in r.stdout
