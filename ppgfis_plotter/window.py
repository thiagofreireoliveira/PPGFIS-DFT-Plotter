# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *
from .analysis import *
from .readers import *
from .exports import *
from .plotting import *
from .ui_helpers import *
from .home import HomePage
from .bands import BandsPage
from .dos import DOSPage
from .pdos import PDOSPage
from .profiles import capturar_estilo_pagina, aplicar_estilo_pagina

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PPGFIS DFT Plotter - Qt6")
        self.resize(1320, 840)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomePage(
            self.show_bands,
            self.show_dos,
            self.show_pdos
        )

        self.bands = BandsPage(
            self.show_home
        )

        self.dos = DOSPage(
            self.show_home
        )

        self.pdos = PDOSPage(
            self.show_home
        )

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.bands)
        self.stack.addWidget(self.dos)
        self.stack.addWidget(self.pdos)

        self._perfil_ativo = None
        self._config_padrao = os.path.join(APP_DIR, "ppgfis_preferencias.json")
        menu = self.menuBar().addMenu("Configurações")
        ac_salvar = QAction("Salvar perfil JSON...", self)
        ac_salvar.triggered.connect(self.salvar_perfil)
        menu.addAction(ac_salvar)
        ac_abrir = QAction("Carregar perfil JSON...", self)
        ac_abrir.triggered.connect(self.abrir_perfil)
        menu.addAction(ac_abrir)
        ac_padrao = QAction("Salvar como padrão", self)
        ac_padrao.triggered.connect(self.salvar_como_padrao)
        menu.addAction(ac_padrao)
        if os.path.isfile(self._config_padrao):
            self._carregar_perfil(self._config_padrao, avisar=False)
        self.show_home()

    def _dados_perfil(self):
        return {"versao": 1, "aplicativo": "PPGFIS DFT Plotter",
                "abas": {nome: capturar_estilo_pagina(getattr(self, nome))
                         for nome in ("bands", "dos", "pdos")}}

    def _salvar_perfil(self, caminho):
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(self._dados_perfil(), arquivo, ensure_ascii=False, indent=2)
        self._perfil_ativo = caminho

    def salvar_perfil(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar configurações", "perfil_graficos.json", "Arquivos JSON (*.json)")
        if caminho:
            try:
                self._salvar_perfil(caminho)
                QMessageBox.information(self, "Configurações", "Perfil salvo com sucesso.")
            except OSError as erro:
                QMessageBox.warning(self, "Erro ao salvar", str(erro))

    def salvar_como_padrao(self):
        try:
            self._salvar_perfil(self._config_padrao)
            QMessageBox.information(self, "Configurações", "Padrão salvo. Será carregado na próxima abertura.")
        except OSError as erro:
            QMessageBox.warning(self, "Erro ao salvar", str(erro))

    def _carregar_perfil(self, caminho, avisar=True):
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if dados.get("aplicativo") != "PPGFIS DFT Plotter" or not isinstance(dados.get("abas"), dict):
                raise ValueError("Arquivo não é um perfil válido do PPGFIS DFT Plotter.")
            for nome in ("bands", "dos", "pdos"):
                if nome in dados["abas"]:
                    aplicar_estilo_pagina(getattr(self, nome), dados["abas"][nome])
            self._perfil_ativo = caminho
            if avisar:
                QMessageBox.information(self, "Configurações", "Perfil carregado nas três abas.")
        except (OSError, ValueError, TypeError, AttributeError) as erro:
            if avisar:
                QMessageBox.warning(self, "Erro ao carregar perfil", str(erro))

    def abrir_perfil(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Carregar configurações", APP_DIR, "Arquivos JSON (*.json)")
        if caminho:
            self._carregar_perfil(caminho)

    def show_home(self):
        self.stack.setCurrentWidget(self.home)

    def show_bands(self):
        self.stack.setCurrentWidget(self.bands)

    def show_dos(self):
        self.stack.setCurrentWidget(self.dos)

    def show_pdos(self):
        self.stack.setCurrentWidget(self.pdos)


