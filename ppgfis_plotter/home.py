# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *
from .analysis import *
from .readers import *
from .exports import *
from .plotting import *
from .ui_helpers import *

class HomePage(QWidget):

    def __init__(self, open_bands, open_dos, open_pdos, parent=None):
        super().__init__(parent)

        main = QVBoxLayout(self)
        main.setContentsMargins(30, 24, 30, 24)
        main.setSpacing(12)

        titulo = QLabel("PPGFIS DFT Plotter")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont(UI_FONT, 26, QFont.Bold))
        main.addWidget(titulo)

        subtitulo = QLabel(
            "Ferramenta gráfica para análise e preparação de figuras de cálculos DFT"
        )
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setFont(QFont(UI_FONT, 12))
        main.addWidget(subtitulo)

        descricao = QLabel(
            "O software reúne ferramentas para visualizar e formatar estruturas de "
            "bandas e densidades de estados obtidas com o Quantum ESPRESSO. "
            "É possível ajustar fontes, rótulos, cores, limites, ticks, legendas, "
            "nível de Fermi, LaTeX, exportação de figuras e, no módulo de DOS, "
            "remover de forma controlada pequenas caudas numéricas dentro do gap."
        )
        descricao.setWordWrap(True)
        descricao.setAlignment(Qt.AlignCenter)
        descricao.setFont(QFont(UI_FONT, 11))
        descricao.setMaximumWidth(950)

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(descricao)
        wrap.addStretch()
        main.addLayout(wrap)

        logos_layout = QGridLayout()
        logos_layout.setHorizontalSpacing(18)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        for coluna_logo in range(4):
            logos_layout.setColumnStretch(coluna_logo, 1)

        instituicoes = [
            ("ufam.png", "UFAM", "Universidade Federal \ndo Amazonas", URLS_INSTITUCIONAIS["UFAM"]),
            ("ppgfis.png", "PPGFIS", "Programa de Pós-Graduação \nem Física", URLS_INSTITUCIONAIS["PPGFIS"]),
            ("dfmat.png", "DFMat", "Departamento de Física \nde Materiais", URLS_INSTITUCIONAIS["DFMat"]),
            ("capes.png", "CAPES", "Coordenação de Aperfeiçoamento \nde Pessoal de Nível Superior", URLS_INSTITUCIONAIS["CAPES"]),
        ]

        for col, (arquivo, sigla, nome, url) in enumerate(instituicoes):

            box = QVBoxLayout()
            box.setAlignment(Qt.AlignHCenter)
            box.setSpacing(8)

            botao_logo = QPushButton()
            botao_logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            botao_logo.setFixedSize(190, 120)
            botao_logo.setCursor(Qt.PointingHandCursor)
            botao_logo.setFlat(True)
            botao_logo.setMinimumHeight(120)

            caminho = os.path.join(LOGO_DIR, arquivo)

            if os.path.exists(caminho):
                pix = QPixmap(caminho)

                if not pix.isNull():
                    botao_logo.setIcon(pix)
                    botao_logo.setIconSize(pix.scaled(
                        150, 100,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ).size())
            else:
                botao_logo.setText(sigla)
                botao_logo.setFont(QFont(UI_FONT, 17, QFont.Bold))

            botao_logo.clicked.connect(lambda checked=False, u=url: abrir_link(u))

            nome_lbl = QPushButton(f"{sigla}\n{nome}")
            nome_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            nome_lbl.setFixedWidth(210)
            nome_lbl.setCursor(Qt.PointingHandCursor)
            nome_lbl.setFlat(True)
            nome_lbl.setFont(QFont(UI_FONT, 9))
            nome_lbl.clicked.connect(lambda checked=False, u=url: abrir_link(u))

            box.addWidget(botao_logo, alignment=Qt.AlignHCenter)
            box.addWidget(nome_lbl, alignment=Qt.AlignHCenter)

            cell = QWidget()
            cell.setLayout(box)

            logos_layout.addWidget(cell, 0, col, alignment=Qt.AlignCenter)

        main.addLayout(logos_layout)

        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        main.addWidget(linha)

        escolha = QLabel("Escolha um módulo")
        escolha.setAlignment(Qt.AlignCenter)
        escolha.setFont(QFont(UI_FONT, 14, QFont.Bold))
        main.addWidget(escolha)

        botoes = QHBoxLayout()
        botoes.addStretch()

        btn_bandas = QPushButton("Estrutura de Bandas (BANDS)")
        btn_bandas.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn_bandas.setMinimumWidth(0)
        btn_bandas.setMinimumSize(250, 52)
        btn_bandas.setFont(QFont(UI_FONT, 12, QFont.Bold))
        btn_bandas.clicked.connect(open_bands)

        btn_dos = QPushButton("Densidade de Estados (DOS)")
        btn_dos.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn_dos.setMinimumWidth(0)
        btn_dos.setMinimumSize(250, 52)
        btn_dos.setFont(QFont(UI_FONT, 12, QFont.Bold))
        btn_dos.clicked.connect(open_dos)

        btn_pdos = QPushButton("DOS Projetada (PDOS)")
        btn_pdos.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn_pdos.setMinimumWidth(0)
        btn_pdos.setMinimumSize(250, 52)
        btn_pdos.setFont(QFont(UI_FONT, 12, QFont.Bold))
        btn_pdos.clicked.connect(open_pdos)

        botoes.addWidget(btn_bandas)
        botoes.addSpacing(15)
        botoes.addWidget(btn_dos)
        botoes.addSpacing(15)
        botoes.addWidget(btn_pdos)
        botoes.addStretch()

        main.addLayout(botoes)
        main.addStretch()

        autor = QLabel(
            'Desenvolvido por <a href="lattes">Thiago Freire de Oliveira</a> '
            ' | <a href="lattes">Currículo Lattes</a>'
        )
        autor.setOpenExternalLinks(False)
        autor.setTextFormat(Qt.RichText)
        autor.setAlignment(Qt.AlignCenter)
        autor.setFont(QFont(UI_FONT, 10))
        autor.linkActivated.connect(lambda _: abrir_link(LATTES_URL))

        main.addWidget(autor)


