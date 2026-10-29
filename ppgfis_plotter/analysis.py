# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

def calcular_bordas_por_bandas(bandas, referencia):
    """
    Calcula VBM, CBM e gap diretamente das energias de bandas.

    Para um sistema com banda cruzando a referência (EF), classifica como
    metálico/sem gap. VBM e CBM continuam sendo reportados como os níveis
    amostrados mais próximos de EF, para rastreabilidade numérica.
    """
    if not bandas:
        raise ValueError("Nenhuma banda disponível para calcular VBM/CBM.")

    energias = np.concatenate([np.asarray(b[:, 1], dtype=float) for b in bandas])
    rel = energias - float(referencia)

    ocupadas = rel[rel <= 0.0]
    vazias = rel[rel > 0.0]

    vbm_rel = float(np.max(ocupadas)) if ocupadas.size else np.nan
    cbm_rel = float(np.min(vazias)) if vazias.size else np.nan

    cruza_ef = any(
        np.min(np.asarray(b[:, 1], dtype=float) - referencia) <= 0.0
        and np.max(np.asarray(b[:, 1], dtype=float) - referencia) >= 0.0
        for b in bandas
    )

    if cruza_ef:
        gap = 0.0
        tipo = "metallico/sem gap"
    elif np.isfinite(vbm_rel) and np.isfinite(cbm_rel):
        gap = max(0.0, cbm_rel - vbm_rel)
        tipo = "com gap" if gap > 1.0e-8 else "sem gap"
    else:
        gap = np.nan
        tipo = "indeterminado"

    return {
        "vbm_abs": float(referencia + vbm_rel) if np.isfinite(vbm_rel) else np.nan,
        "cbm_abs": float(referencia + cbm_rel) if np.isfinite(cbm_rel) else np.nan,
        "vbm_rel": vbm_rel,
        "cbm_rel": cbm_rel,
        "gap": gap,
        "tipo": tipo,
        "metodo": "estrutura de bandas",
    }


def calcular_bordas_por_dos(energia_rel, dos, referencia, limiar_rel=1.0e-4):
    """
    Estima VBM/CBM a partir do início da DOS.

    O limiar é relativo ao máximo da DOS (padrão: 1e-4). Essa estimativa
    depende da malha/broadening; por isso o CSV registra explicitamente
    o método e o limiar utilizado.
    """
    energia_rel = np.asarray(energia_rel, dtype=float)
    dos = np.abs(np.asarray(dos, dtype=float))

    if energia_rel.size != dos.size or energia_rel.size == 0:
        raise ValueError("Energia e DOS incompatíveis para cálculo do gap.")

    max_dos = float(np.max(dos))
    if max_dos <= 0.0:
        return {
            "vbm_abs": np.nan, "cbm_abs": np.nan,
            "vbm_rel": np.nan, "cbm_rel": np.nan,
            "gap": np.nan, "tipo": "indeterminado",
            "metodo": f"DOS (limiar relativo={limiar_rel:g})",
        }

    limiar = max_dos * float(limiar_rel)
    ativo = dos > limiar

    # Se houver DOS significativa no ponto amostrado mais próximo de EF,
    # o sistema é tratado como sem gap pela DOS.
    i0 = int(np.argmin(np.abs(energia_rel)))
    metal = bool(ativo[i0])

    occ = energia_rel[(energia_rel <= 0.0) & ativo]
    emp = energia_rel[(energia_rel > 0.0) & ativo]

    vbm_rel = float(np.max(occ)) if occ.size else np.nan
    cbm_rel = float(np.min(emp)) if emp.size else np.nan

    if metal:
        gap = 0.0
        tipo = "metallico/sem gap"
    elif np.isfinite(vbm_rel) and np.isfinite(cbm_rel):
        gap = max(0.0, cbm_rel - vbm_rel)
        tipo = "com gap" if gap > 1.0e-8 else "sem gap"
    else:
        gap = np.nan
        tipo = "indeterminado"

    return {
        "vbm_abs": float(referencia + vbm_rel) if np.isfinite(vbm_rel) else np.nan,
        "cbm_abs": float(referencia + cbm_rel) if np.isfinite(cbm_rel) else np.nan,
        "vbm_rel": vbm_rel,
        "cbm_rel": cbm_rel,
        "gap": gap,
        "tipo": tipo,
        "metodo": f"DOS (limiar relativo={limiar_rel:g})",
    }


def remover_ruido_gap(energia, dos, limiar):
    energia = np.asarray(energia)
    dos = np.asarray(dos)

    if limiar <= 0:
        return dos.copy(), None, None

    idx0 = np.argmin(np.abs(energia))
    mascara_baixa = dos <= limiar

    if not mascara_baixa[idx0]:
        candidatos = np.where(mascara_baixa)[0]

        if len(candidatos) == 0:
            return dos.copy(), None, None

        idx0 = candidatos[
            np.argmin(np.abs(energia[candidatos]))
        ]

    esquerda = idx0
    direita = idx0

    while esquerda > 0 and mascara_baixa[esquerda - 1]:
        esquerda -= 1

    while direita < len(dos) - 1 and mascara_baixa[direita + 1]:
        direita += 1

    dos_limpa = dos.copy()
    dos_limpa[esquerda:direita + 1] = 0.0

    return dos_limpa, energia[esquerda], energia[direita]


def limites_bandas_gap(janela, ef_dos, spin):
    b = janela.bands
    grupos = {'UP': b.bandas_up, 'DOWN': b.bandas_down} if spin else {'TOTAL': b.bandas}
    limites = {}
    for canal, curvas in grupos.items():
        if curvas is None or len(curvas) == 0:
            raise ValueError(f'Carregue primeiro as bandas {canal} na aba Bandas.')
        r = calcular_bordas_por_bandas(curvas, b.energia_ref)
        if r['tipo'] != 'com gap':
            raise ValueError(f'Não foi identificado gap no canal {canal}.')
        limites[canal] = (r['vbm_abs'] - ef_dos, r['cbm_abs'] - ef_dos)
    return limites


def corte_gap_bandas(energia, valores, intervalo):
    saida = np.array(valores, copy=True)
    a, b = intervalo
    saida[(energia > a) & (energia < b)] = 0.0
    return saida


