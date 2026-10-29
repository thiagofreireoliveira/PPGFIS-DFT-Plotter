# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

CAMPOS_ARQUIVO = ("file_edit", "scf_edit", "band_edit", "band_up_edit",
                  "band_down_edit", "pdos_tot_normal_edit", "orbitals_normal_edit",
                  "pdos_tot_spin_edit", "orbitals_spin_edit", "pasta_edit",
                  "dir_edit", "path_edit")

def capturar_estilo_pagina(pagina):
    campos = {}
    for nome, widget in vars(pagina).items():
        if nome.startswith("_") or nome in CAMPOS_ARQUIVO:
            continue
        if isinstance(widget, QLineEdit):
            campos[nome] = {"tipo": "texto", "valor": widget.text()}
        elif isinstance(widget, QCheckBox):
            campos[nome] = {"tipo": "check", "valor": widget.isChecked()}
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            campos[nome] = {"tipo": "numero", "valor": widget.value()}
        elif isinstance(widget, QComboBox):
            campos[nome] = {"tipo": "combo", "valor": widget.currentText()}
    # Cores e estilos simples configuráveis (não incluem matrizes ou resultados).
    atributos = {}
    for nome, valor in vars(pagina).items():
        if nome.startswith("cor_") and isinstance(valor, str):
            atributos[nome] = valor
        elif nome in ("cores", "estilos_linha", "cores_orbitais_spin") and isinstance(valor, dict):
            if all(isinstance(k, str) and isinstance(v, str) for k, v in valor.items()):
                atributos[nome] = dict(valor)
    return {"campos": campos, "atributos": atributos}


def aplicar_estilo_pagina(pagina, perfil):
    for nome, item in perfil.get("campos", {}).items():
        if nome in CAMPOS_ARQUIVO:
            continue
        widget = getattr(pagina, nome, None)
        try:
            tipo, valor = item["tipo"], item["valor"]
            if tipo == "texto" and isinstance(widget, QLineEdit):
                widget.setText(str(valor))
            elif tipo == "check" and isinstance(widget, QCheckBox):
                widget.setChecked(bool(valor))
            elif tipo == "numero" and isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.setValue(float(valor) if isinstance(widget, QDoubleSpinBox) else int(valor))
            elif tipo == "combo" and isinstance(widget, QComboBox):
                idx = widget.findText(str(valor))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        except (TypeError, ValueError, KeyError):
            continue
    for nome, valor in perfil.get("atributos", {}).items():
        atual = getattr(pagina, nome, None)
        if nome.startswith("cor_") and isinstance(atual, str) and isinstance(valor, str):
            setattr(pagina, nome, valor)
        elif nome in ("cores", "estilos_linha", "cores_orbitais_spin") and isinstance(atual, dict) and isinstance(valor, dict):
            atual.update({k: v for k, v in valor.items() if isinstance(k, str) and isinstance(v, str)})
    try:
        pagina.atualizar_plot()
    except (AttributeError, ValueError, TypeError):
        pass  # Página sem dados carregados.


