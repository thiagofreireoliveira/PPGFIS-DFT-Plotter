# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

def abrir_link(url: str):
    webbrowser.open_new_tab(url)


def instalar_barra_de_ferramentas(pagina, root, splitter, scroll):
    """Barra compacta; os controles existentes ficam num painel retrátil."""
    barra = QToolBar("Ferramentas do gráfico", pagina)
    barra.setMovable(False)
    barra.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    barra.setStyleSheet("QToolBar { spacing: 7px; padding: 5px; border-bottom: 1px solid palette(mid); }")
    root.insertWidget(0, barra)
    pagina.barra_grafico = barra
    pagina.painel_configuracoes = scroll
    pagina.divisor_grafico = splitter

    ac_config = QAction("⚙  Configurações", pagina)
    ac_config.setCheckable(True)
    ac_config.setChecked(False)
    ac_config.setToolTip("Mostrar/ocultar as configurações do gráfico")
    barra.addAction(ac_config)

    def alternar(ativo):
        if ativo:
            scroll.show()
            splitter.setSizes([410, max(650, splitter.width() - 410)])
        else:
            scroll.hide()
    ac_config.toggled.connect(alternar)
    pagina.acao_configuracoes = ac_config

    barra.addSeparator()
    ac_salvar = QAction("Salvar perfil", pagina)
    ac_salvar.triggered.connect(lambda: pagina.window().salvar_perfil())
    barra.addAction(ac_salvar)
    ac_abrir = QAction("Carregar perfil", pagina)
    ac_abrir.triggered.connect(lambda: pagina.window().abrir_perfil())
    barra.addAction(ac_abrir)
    ac_padrao = QAction("Salvar padrão", pagina)
    ac_padrao.triggered.connect(lambda: pagina.window().salvar_como_padrao())
    barra.addAction(ac_padrao)

    barra.addSeparator()
    ac_atualizar = QAction("↻  Atualizar gráfico", pagina)
    def atualizar():
        if hasattr(pagina, "atualizar_plot"):
            pagina.atualizar_plot()
        elif hasattr(pagina, "plot"):
            pagina.plot.draw()
    ac_atualizar.triggered.connect(atualizar)
    barra.addAction(ac_atualizar)
    # O painel permanece oculto inicialmente, ampliando a área de visualização.
    scroll.hide()


def aplicar_visibilidade_painel(ax, cfg, xlabel, ylabel):
    """Aplica título/rótulos/ticks sem destruir locators ou limites."""
    ax.set_title(cfg.titulo.text() if cfg.show_title.isChecked() else "")
    ax.set_xlabel(xlabel if cfg.show_xlabel.isChecked() else "")
    ax.set_ylabel(ylabel if cfg.show_ylabel.isChecked() else "")
    ax.tick_params(axis="x", which="both",
                   bottom=cfg.show_xticks.isChecked(),
                   top=False,
                   labelbottom=cfg.show_xnumbers.isChecked())
    ax.tick_params(axis="y", which="both",
                   left=cfg.show_yticks.isChecked(),
                   right=False,
                   labelleft=cfg.show_ynumbers.isChecked())


class PainelVisualControls:
    """Pequeno contêiner de widgets para controlar um painel individual."""
    def __init__(self, parent, titulo_padrao):
        self.titulo = QLineEdit(titulo_padrao)
        self.show_title = QCheckBox("Título")
        self.show_xlabel = QCheckBox("Rótulo X")
        self.show_ylabel = QCheckBox("Rótulo Y")
        self.show_xticks = QCheckBox("Ticks X")
        self.show_yticks = QCheckBox("Ticks Y")
        self.show_xnumbers = QCheckBox("Números X")
        self.show_ynumbers = QCheckBox("Números Y")
        for w in (self.show_title, self.show_xlabel, self.show_ylabel,
                  self.show_xticks, self.show_yticks,
                  self.show_xnumbers, self.show_ynumbers):
            w.setChecked(True)
            w.stateChanged.connect(lambda _=0, p=parent: p.atualizar_plot())
        self.titulo.editingFinished.connect(parent.atualizar_plot)

    def add_to_form(self, form, prefixo):
        form.addRow(f"{prefixo} - título:", self.titulo)
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        for w in (self.show_title, self.show_xlabel, self.show_ylabel,
                  self.show_xticks, self.show_yticks,
                  self.show_xnumbers, self.show_ynumbers):
            lay.addWidget(w)
        form.addRow(f"{prefixo} - mostrar:", row)


