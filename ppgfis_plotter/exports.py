# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

def salvar_resultados_eletronicos_csv(arquivo_base, sistema, modulo, referencia,
                                      tipo_referencia, resultados):
    """
    Cria/atualiza <sistema>_resultados_eletronicos.csv no diretório do
    arquivo principal. Uma linha é mantida por combinação módulo + spin.
    """
    diretorio = os.path.dirname(os.path.abspath(str(arquivo_base))) or os.getcwd()
    caminho = os.path.join(diretorio, f"{sistema}_resultados_eletronicos.csv")

    campos = [
        "sistema", "modulo", "spin",
        "referencia_tipo", "referencia_eV",
        "VBM_eV", "CBM_eV",
        "VBM_rel_EF_eV", "CBM_rel_EF_eV",
        "gap_eV", "classificacao", "metodo",
        "arquivo_origem",
    ]

    existentes = []
    if os.path.isfile(caminho):
        try:
            with open(caminho, "r", newline="", encoding="utf-8") as f:
                existentes = list(csv.DictReader(f))
        except Exception:
            existentes = []

    novas = []
    origem = os.path.abspath(str(arquivo_base))
    for spin, r in resultados:
        def fmt(v):
            return "" if not np.isfinite(v) else f"{float(v):.8f}"

        novas.append({
            "sistema": sistema,
            "modulo": modulo,
            "spin": spin,
            "referencia_tipo": tipo_referencia,
            "referencia_eV": fmt(float(referencia)),
            "VBM_eV": fmt(r["vbm_abs"]),
            "CBM_eV": fmt(r["cbm_abs"]),
            "VBM_rel_EF_eV": fmt(r["vbm_rel"]),
            "CBM_rel_EF_eV": fmt(r["cbm_rel"]),
            "gap_eV": fmt(r["gap"]),
            "classificacao": r["tipo"],
            "metodo": r["metodo"],
            "arquivo_origem": origem,
        })

    chaves_novas = {(r["modulo"], r["spin"]) for r in novas}
    existentes = [
        r for r in existentes
        if (r.get("modulo", ""), r.get("spin", "")) not in chaves_novas
    ]
    existentes.extend(novas)

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(existentes)

    return caminho


