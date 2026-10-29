# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *
from .analysis import *
from .readers import *
from .exports import *
from .plotting import *
from .ui_helpers import *

class PDOSPage(QWidget):

    def __init__(self, back_callback, parent=None):
        super().__init__(parent)

        self.back_callback = back_callback

        self.energia = None

        # Dados originais carregados dos arquivos
        self.dos_total_original = None
        self.pdos_original = None
        self.pdos_elementos_original = {}

        # Dados efetivamente mostrados no gráfico.
        # Podem receber a limpeza de ruído sem alterar os originais.
        self.dos_total = None
        self.pdos = None
        self.pdos_elementos = {}

        # Dados nspin=2
        self.dos_total_up = None
        self.dos_total_down = None
        self.pdos_up = None
        self.pdos_down = None
        self.pdos_elementos_up = {}
        self.pdos_elementos_down = {}

        self.usados = None
        self.usados_elementos = {}
        self.element_checkboxes = {}
        self.element_widgets = []
        self.fermi = None

        self.cores = {
            "total": "#000000",
            "s": "#1f77b4",
            "p": "#2ca02c",
            "d": "#ff7f0e",
            "f": "#9467bd",
            "fermi": "#d62728",
        }

        self.estilos_linha = {
            "total": "-",
            "s": "-",
            "p": "-",
            "d": "-",
            "f": "-",
            "fermi": "--",
        }

        self.paleta_elementos = [
            "#17becf",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#aec7e8",
            "#ff9896",
            "#98df8a",
            "#c5b0d5",
            "#c49c94",
        ]

        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(410)

        panel = QWidget()
        self.form = QVBoxLayout(panel)
        self.form.setContentsMargins(8, 8, 8, 8)
        self.form.setSpacing(8)

        scroll.setWidget(panel)
        splitter.addWidget(scroll)

        self.plot = PlotWidget()
        self.plot.style_controls = self
        splitter.addWidget(self.plot)
        splitter.setStretchFactor(1, 1)
        instalar_barra_de_ferramentas(self, root, splitter, scroll)

        self._build_controls()

    def _build_controls(self):

        nav = QHBoxLayout()
        voltar = QPushButton("← Início")
        voltar.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        voltar.setMinimumWidth(0)
        voltar.clicked.connect(self.back_callback)
        nav.addWidget(voltar)
        nav.addStretch()
        self.form.addLayout(nav)

        # ----------------------------------------------------
        # Arquivos
        # ----------------------------------------------------
        box = QGroupBox("Arquivos PDOS")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.dos_file = QLineEdit("hBN2D.dos")
        self.pdos_tot_file = QLineEdit("hBN2D.pdos_tot")
        self.orbitals_dir = QLineEdit("orbitals")

        btn = QPushButton("Abrir")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_dos)
        row = QHBoxLayout()
        row.addWidget(self.dos_file)
        row.addWidget(btn)
        form.addRow("Arquivo .dos:", row)

        btn = QPushButton("Abrir")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_pdos_tot)
        row = QHBoxLayout()
        row.addWidget(self.pdos_tot_file)
        row.addWidget(btn)
        form.addRow("Arquivo .pdos_tot:", row)

        btn = QPushButton("Selecionar")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_orbitals)
        row = QHBoxLayout()
        row.addWidget(self.orbitals_dir)
        row.addWidget(btn)
        form.addRow("Pasta orbitals:", row)

        self.spin_checkbox = QCheckBox("Cálculo com polarização de spin (nspin = 2)")
        self.spin_checkbox.stateChanged.connect(
            lambda _state: self.atualizar_modo_spin()
        )
        form.addRow(self.spin_checkbox)

        self.mirror_down = QCheckBox("Espelhar canal DOWN (valores negativos)")
        # Como DOWN é desenhado em painel separado, o padrão é positivo.
        # Espelhar continua disponível, mas exige limites Y negativos.
        self.mirror_down.setChecked(False)
        self.mirror_down.stateChanged.connect(
            lambda _state: self.atualizar_modo_spin()
        )
        form.addRow(self.mirror_down)

        btn = QPushButton("Carregar PDOS")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.carregar_dados)
        form.addRow(btn)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Organizador
        # ----------------------------------------------------
        box = QGroupBox("Organizar arquivos do projwfc.x")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.origem_dir = QLineEdit(".")
        self.destino_dir = QLineEdit("orbitals")

        btn = QPushButton("Selecionar")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_origem)
        row = QHBoxLayout()
        row.addWidget(self.origem_dir)
        row.addWidget(btn)
        form.addRow("Diretório origem:", row)

        btn = QPushButton("Selecionar")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_destino)
        row = QHBoxLayout()
        row.addWidget(self.destino_dir)
        row.addWidget(btn)
        form.addRow("Diretório destino:", row)

        btn = QPushButton("Organizar orbitais s/p/d/f")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.organizar_orbitais)
        form.addRow(btn)

        info = QLabel(
            "Os arquivos são identificados automaticamente por padrões "
            "como _wfc#1(s), _wfc#2(p), _wfc#3(d) e _wfc#4(f)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666666; font-size: 9pt;")
        form.addRow(info)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Curvas
        # ----------------------------------------------------
        box = QGroupBox("Curvas exibidas e aparência")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Curvas orbitais com a mesma estética usada nas curvas por elemento:
        # [checkbox/nome] [tipo de linha] [Cor]
        self.show_total = QCheckBox("DOS total")
        self.show_s = QCheckBox("Orbital s")
        self.show_p = QCheckBox("Orbital p")
        self.show_d = QCheckBox("Orbital d")
        self.show_f = QCheckBox("Orbital f")

        self.orbital_curve_rows = []

        for chave, checkbox in [
            ("total", self.show_total),
            ("s", self.show_s),
            ("p", self.show_p),
            ("d", self.show_d),
            ("f", self.show_f),
        ]:
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.atualizar_plot)

            container = QWidget()
            linha = QHBoxLayout(container)
            linha.setContentsMargins(0, 0, 0, 0)
            linha.setSpacing(8)

            combo_estilo = QComboBox()
            for nome_estilo, valor_estilo in [
                ("Sólida", "-"),
                ("Tracejada", "--"),
                ("Pontilhada", ":"),
                ("Traço-ponto", "-."),
            ]:
                combo_estilo.addItem(nome_estilo, valor_estilo)

            idx_estilo = combo_estilo.findData(self.estilos_linha[chave])
            if idx_estilo >= 0:
                combo_estilo.setCurrentIndex(idx_estilo)

            combo_estilo.currentIndexChanged.connect(
                lambda _=None, k=chave, c=combo_estilo:
                self.alterar_estilo_linha(k, c.currentData())
            )

            botao_cor = QPushButton("Cor")
            botao_cor.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            botao_cor.setMinimumWidth(0)
            botao_cor.setMaximumWidth(70)
            botao_cor.clicked.connect(
                lambda checked=False, k=chave: self.escolher_cor(k)
            )

            linha.addWidget(checkbox)
            linha.addSpacing(8)
            # A aparência agora é editada exclusivamente na pré-visualização.
            combo_estilo.hide()
            botao_cor.hide()
            linha.addStretch(1)

            form.addRow(container)
            self.orbital_curve_rows.append(container)

        # O grupo permanece aberto logicamente: os controles de
        # cor/linha serão acrescentados a este mesmo QFormLayout abaixo.
        curvas_box = box
        curvas_form = form

        # ----------------------------------------------------
        # PDOS por elemento
        # Integrado ao grupo "Curvas exibidas e aparência".
        # ----------------------------------------------------
        separador_elementos = QLabel("PDOS por elemento")
        separador_elementos.setStyleSheet(
            "font-weight: bold; margin-top: 8px;"
        )
        curvas_form.addRow(separador_elementos)

        self.element_box = QWidget()
        self.element_layout = QVBoxLayout(self.element_box)
        self.element_layout.setContentsMargins(0, 0, 0, 0)

        self.element_info = QLabel(
            "Os elementos serão detectados automaticamente "
            "a partir dos nomes dos arquivos do projwfc.x."
        )
        self.element_info.setWordWrap(True)
        self.element_info.setStyleSheet(
            "color: #666666; font-size: 9pt;"
        )

        self.element_layout.addWidget(self.element_info)
        curvas_form.addRow(self.element_box)

        # Exibe imediatamente o grupo unificado. Assim os controles
        # dinâmicos por elemento permanecem visíveis no mesmo bloco.
        self.form.addWidget(curvas_box)

        # ----------------------------------------------------
        # Rótulos
        # ----------------------------------------------------
        box = QGroupBox("Eixos e rótulos")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.title_edit = QLineEdit()
        self.xlabel_edit = QLineEdit("Energy (eV)")
        self.ylabel_edit = QLineEdit("PDOS (states/eV/unit cell)")

        form.addRow("Título:", self.title_edit)
        form.addRow("Eixo X:", self.xlabel_edit)
        form.addRow("Eixo Y:", self.ylabel_edit)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Eixos
        # ----------------------------------------------------
        box = QGroupBox("Eixos")
        self.pdos_eixos_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.xmin = self.dspin(-1000, 1000, -8, 0.5)
        self.xmax = self.dspin(-1000, 1000, 8, 0.5)
        self.ymin = self.dspin(-10000, 10000, 0, 1)
        self.ymax = self.dspin(-10000, 10000, 80, 1)
        self.xmajor = self.dspin(0.01, 1000, 2, 0.5)
        self.ymajor = self.dspin(0.01, 10000, 20, 1)
        self.xminor = self.ispin(1, 20, 4)
        self.yminor = self.ispin(1, 20, 4)

        form.addRow("X mínimo:", self.xmin)
        form.addRow("X máximo:", self.xmax)
        form.addRow("Y mínimo:", self.ymin)
        form.addRow("Y máximo:", self.ymax)
        form.addRow("Incremento X:", self.xmajor)
        form.addRow("Incremento Y:", self.ymajor)
        form.addRow("Subdivisões minor X:", self.xminor)
        form.addRow("Subdivisões minor Y:", self.yminor)

        # Limites independentes para as duas linhas da matriz nspin=2.
        # Cada conjunto é aplicado tanto ao painel por elemento quanto ao
        # painel por orbital do respectivo spin.
        self.pdos_up_xmin = self.dspin(-1000, 1000, -8, 0.5)
        self.pdos_up_xmax = self.dspin(-1000, 1000, 8, 0.5)
        self.pdos_up_ymin = self.dspin(-10000, 10000, 0, 1)
        self.pdos_up_ymax = self.dspin(-10000, 10000, 80, 1)

        self.pdos_dn_xmin = self.dspin(-1000, 1000, -8, 0.5)
        self.pdos_dn_xmax = self.dspin(-1000, 1000, 8, 0.5)
        self.pdos_dn_ymin = self.dspin(-10000, 10000, 0, 1)
        self.pdos_dn_ymax = self.dspin(-10000, 10000, 80, 1)

        # Incrementos locais para a linha UP da matriz PDOS.
        self.pdos_up_xmajor = self.dspin(0.01, 1000, 2, 0.5)
        self.pdos_up_ymajor = self.dspin(0.01, 10000, 10, 1)
        self.pdos_up_xminor = QSpinBox()
        self.pdos_up_yminor = QSpinBox()
        self.pdos_up_xminor.setRange(1, 20)
        self.pdos_up_yminor.setRange(1, 20)
        self.pdos_up_xminor.setValue(2)
        self.pdos_up_yminor.setValue(2)

        # Incrementos locais para a linha DOWN da matriz PDOS.
        self.pdos_dn_xmajor = self.dspin(0.01, 1000, 2, 0.5)
        self.pdos_dn_ymajor = self.dspin(0.01, 10000, 10, 1)
        self.pdos_dn_xminor = QSpinBox()
        self.pdos_dn_yminor = QSpinBox()
        self.pdos_dn_xminor.setRange(1, 20)
        self.pdos_dn_yminor.setRange(1, 20)
        self.pdos_dn_xminor.setValue(2)
        self.pdos_dn_yminor.setValue(2)

        for w in (
            self.pdos_up_xmajor, self.pdos_up_ymajor,
            self.pdos_up_xminor, self.pdos_up_yminor,
            self.pdos_dn_xmajor, self.pdos_dn_ymajor,
            self.pdos_dn_xminor, self.pdos_dn_yminor,
        ):
            w.valueChanged.connect(self.atualizar_plot)

        form.addRow("UP - X mínimo:", self.pdos_up_xmin)
        form.addRow("UP - X máximo:", self.pdos_up_xmax)
        form.addRow("UP - Incremento X:", self.pdos_up_xmajor)
        form.addRow("UP - Subdivisões minor X:", self.pdos_up_xminor)
        form.addRow("UP - Y mínimo:", self.pdos_up_ymin)
        form.addRow("UP - Y máximo:", self.pdos_up_ymax)
        form.addRow("UP - Incremento Y:", self.pdos_up_ymajor)
        form.addRow("UP - Subdivisões minor Y:", self.pdos_up_yminor)

        form.addRow("DOWN - X mínimo:", self.pdos_dn_xmin)
        form.addRow("DOWN - X máximo:", self.pdos_dn_xmax)
        form.addRow("DOWN - Incremento X:", self.pdos_dn_xmajor)
        form.addRow("DOWN - Subdivisões minor X:", self.pdos_dn_xminor)
        form.addRow("DOWN - Y mínimo:", self.pdos_dn_ymin)
        form.addRow("DOWN - Y máximo:", self.pdos_dn_ymax)
        form.addRow("DOWN - Incremento Y:", self.pdos_dn_ymajor)
        form.addRow("DOWN - Subdivisões minor Y:", self.pdos_dn_yminor)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Painéis nspin=2
        # ----------------------------------------------------
        box = QGroupBox("Painéis PDOS (nspin = 2)")
        self.pdos_spin_panels_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.pdos_elem_up_visual = PainelVisualControls(
            self, "PDOS por elemento - UP"
        )
        self.pdos_orb_up_visual = PainelVisualControls(
            self, "PDOS por orbital - UP"
        )
        self.pdos_elem_dn_visual = PainelVisualControls(
            self, "PDOS por elemento - DOWN"
        )
        self.pdos_orb_dn_visual = PainelVisualControls(
            self, "PDOS por orbital - DOWN"
        )

        self.pdos_elem_up_visual.add_to_form(form, "Elemento UP")
        self.pdos_orb_up_visual.add_to_form(form, "Orbital UP")
        self.pdos_elem_dn_visual.add_to_form(form, "Elemento DOWN")
        self.pdos_orb_dn_visual.add_to_form(form, "Orbital DOWN")

        self.pdos_wspace = self.dspin(0.0, 2.0, 0.30, 0.05)
        self.pdos_hspace = self.dspin(0.0, 2.0, 0.35, 0.05)
        self.pdos_wspace.valueChanged.connect(self.atualizar_plot)
        self.pdos_hspace.valueChanged.connect(self.atualizar_plot)
        form.addRow("Espaçamento horizontal:", self.pdos_wspace)
        form.addRow("Espaçamento vertical:", self.pdos_hspace)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Fontes
        # ----------------------------------------------------
        box = QGroupBox("Fontes")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.font_axis = self.ispin(6, 60, 16)
        self.font_tick = self.ispin(6, 60, 14)
        self.font_title = self.ispin(6, 60, 16)
        self.font_legend = self.ispin(6, 60, 12)

        form.addRow("Fonte eixos:", self.font_axis)
        form.addRow("Tamanho números/ticks:", self.font_tick)
        form.addRow("Fonte título:", self.font_title)
        form.addRow("Fonte legenda:", self.font_legend)

        self.bold_title = QCheckBox("Título em negrito")
        self.bold_axis = QCheckBox("Rótulos em negrito")
        self.bold_ticks = QCheckBox("Números/ticks em negrito")
        self.bold_legend = QCheckBox("Legenda em negrito")

        for w in (
            self.bold_title,
            self.bold_axis,
            self.bold_ticks,
            self.bold_legend,
        ):
            w.stateChanged.connect(self.atualizar_plot)
            form.addRow(w)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # LaTeX
        # ----------------------------------------------------
        box = QGroupBox("LaTeX / mhchem")
        v = QVBoxLayout(box)

        self.latex_global = QCheckBox(
            "Usar LaTeX / mhchem em toda a figura"
        )
        self.latex_global.stateChanged.connect(self.atualizar_plot)
        v.addWidget(self.latex_global)

        info = QLabel(
            r"Exemplos: \ce{CO2}, \ce{O2}, $E-E_F$, $E_{\mathrm{ads}}$"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666666; font-size: 9pt;")
        v.addWidget(info)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Cores / aparência das curvas
        # Agora fazem parte do mesmo campo "Curvas exibidas e aparência".
        # ----------------------------------------------------
        box = curvas_box
        form = curvas_form

        separador_curvas = QLabel("Aparência das curvas")
        separador_curvas.setStyleSheet(
            "font-weight: bold; margin-top: 8px;"
        )
        form.addRow(separador_curvas)

        # Cor e estilo de DOS total/s/p/d/f já ficam ao lado de cada curva,
        # seguindo a mesma estética das curvas por elemento.
        btn = QPushButton("Cor de EF")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(
            lambda checked=False: self.escolher_cor("fermi")
        )
        form.addRow(btn)

        self.linewidth = self.dspin(0.1, 10, 1.5, 0.1)
        self.fermi_width = self.dspin(0.1, 10, 0.8, 0.1)

        form.addRow("Espessura curvas:", self.linewidth)
        form.addRow("Espessura EF:", self.fermi_width)

        self.style_fermi = self.criar_combo_estilo("fermi", "--")
        form.addRow("Linha de EF:", self.style_fermi)

        self.show_fermi = QCheckBox("Mostrar EF")
        self.show_fermi.setChecked(True)

        self.show_grid = QCheckBox("Mostrar grade")
        self.show_legend = QCheckBox("Mostrar legenda")
        self.show_legend.setChecked(True)
        self.legend_frame = QCheckBox("Exibir moldura da legenda")
        self.legend_frame.setChecked(True)


        for w in (
            self.show_fermi,
            self.show_grid,
            self.show_legend,
            self.legend_frame,
        ):
            w.stateChanged.connect(self.atualizar_plot)
            form.addRow(w)

        # ----------------------------------------------------
        # Ruído no gap
        # ----------------------------------------------------
        box = QGroupBox("Ruído no gap")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.noise_threshold = self.dspin(
            0.0, 1000.0, 0.01, 0.001
        )
        self.noise_threshold.setDecimals(6)

        form.addRow(
            "Limiar da DOS total:",
            self.noise_threshold
        )

        btn = QPushButton("Eliminar ruído no gap")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.eliminar_ruido_gap_pdos)
        form.addRow(btn)
        self.auto_gap_bandas = QCheckBox('Aplicar corte na lacuna (gap)')
        self.auto_gap_bandas.setChecked(False)
        self.auto_gap_bandas.toggled.connect(self.atualizar_plot)
        form.addRow(self.auto_gap_bandas)
        btn_bandas = QPushButton('Zerar DOS/PDOS pelo gap das bandas')
        btn_bandas.clicked.connect(self.cortar_pdos_bandas)
        form.addRow(btn_bandas)

        btn = QPushButton("Restaurar PDOS original")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.restaurar_pdos_original)
        form.addRow(btn)

        info_ruido = QLabel(
            "O intervalo do gap é identificado a partir da DOS total. "
            "Depois, esse mesmo intervalo é zerado na DOS total, nas "
            "contribuições s/p/d/f e nas curvas por elemento."
        )
        info_ruido.setWordWrap(True)
        info_ruido.setStyleSheet(
            "color: #666666; font-size: 9pt;"
        )
        form.addRow(info_ruido)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Figura / exportação
        # ----------------------------------------------------
        box = QGroupBox("Figura")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.fig_w = self.dspin(3, 30, 9, 0.5)
        self.fig_h = self.dspin(3, 30, 7, 0.5)
        self.dpi = self.ispin(72, 2400, 300)

        form.addRow("Largura exportação:", self.fig_w)
        form.addRow("Altura exportação:", self.fig_h)
        form.addRow("DPI:", self.dpi)

        self.form.addWidget(box)

        btn = QPushButton("Atualizar prévia")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.atualizar_plot)
        self.form.addWidget(btn)

        btn = QPushButton("Limpar gráfico")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.plot.clear)
        self.form.addWidget(btn)

        btn = QPushButton("Salvar figura")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.salvar_figura)
        self.form.addWidget(btn)

        self.status = QLabel(
            "Organize os arquivos e carregue a PDOS."
        )
        self.status.setWordWrap(True)
        self.form.addWidget(self.status)

        self.form.addStretch()

        self.atualizar_modo_spin()

    def criar_combo_estilo(self, chave, padrao="-"):
        combo = QComboBox()

        estilos = [
            ("Sólida", "-"),
            ("Tracejada", "--"),
            ("Pontilhada", ":"),
            ("Traço-ponto", "-."),
        ]

        for nome, valor in estilos:
            combo.addItem(nome, valor)

        indice = combo.findData(padrao)
        if indice >= 0:
            combo.setCurrentIndex(indice)

        combo.currentIndexChanged.connect(
            lambda _=None, k=chave, c=combo:
            self.alterar_estilo_linha(k, c.currentData())
        )

        self.estilos_linha[chave] = padrao
        return combo

    def alterar_estilo_linha(self, chave, estilo):
        self.estilos_linha[chave] = estilo
        self.atualizar_plot()

    def dspin(self, mn, mx, value, step):
        w = QDoubleSpinBox()
        w.setRange(mn, mx)
        w.setValue(value)
        w.setSingleStep(step)
        w.valueChanged.connect(self.atualizar_plot)
        return w

    def ispin(self, mn, mx, value):
        w = QSpinBox()
        w.setRange(mn, mx)
        w.setValue(value)
        w.valueChanged.connect(self.atualizar_plot)
        return w

    def atualizar_controles_elementos(self):
        """
        Recria os controles dos elementos encontrados sem
        acumular widgets de carregamentos anteriores.
        """

        # Remove containers criados anteriormente
        for widget in self.element_widgets:
            self.element_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

        self.element_widgets = []
        self.element_checkboxes = {}

        elementos = sorted(self.usados_elementos.keys())

        if not elementos:
            aviso = QLabel(
                "Nenhum elemento químico foi identificado nos "
                "nomes dos arquivos PDOS."
            )
            aviso.setStyleSheet(
                "color: #a33; font-size: 9pt;"
            )
            aviso.setWordWrap(True)

            self.element_layout.addWidget(aviso)
            self.element_widgets.append(aviso)
            return

        for i, elemento in enumerate(elementos):

            container = QWidget()
            linha = QHBoxLayout(container)
            linha.setContentsMargins(0, 0, 0, 0)
            linha.setSpacing(8)

            checkbox = QCheckBox(
                f"{elemento} "
                f"({self.usados_elementos[elemento]} arquivos)"
            )
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.atualizar_plot)

            self.element_checkboxes[elemento] = checkbox

            if elemento not in self.cores:
                self.cores[elemento] = self.paleta_elementos[
                    i % len(self.paleta_elementos)
                ]

            if elemento not in self.estilos_linha:
                self.estilos_linha[elemento] = "--"

            combo_estilo = QComboBox()
            for nome_estilo, valor_estilo in [
                ("Sólida", "-"),
                ("Tracejada", "--"),
                ("Pontilhada", ":"),
                ("Traço-ponto", "-."),
            ]:
                combo_estilo.addItem(nome_estilo, valor_estilo)

            idx_estilo = combo_estilo.findData(
                self.estilos_linha[elemento]
            )
            if idx_estilo >= 0:
                combo_estilo.setCurrentIndex(idx_estilo)

            combo_estilo.currentIndexChanged.connect(
                lambda _=None, e=elemento, c=combo_estilo:
                self.alterar_estilo_linha(e, c.currentData())
            )

            botao_cor = QPushButton("Cor")
            botao_cor.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            botao_cor.setMinimumWidth(0)
            botao_cor.setMaximumWidth(70)
            botao_cor.clicked.connect(
                lambda checked=False, e=elemento:
                self.escolher_cor(e)
            )

            linha.addWidget(checkbox)
            linha.addSpacing(8)
            # A aparência agora é editada exclusivamente na pré-visualização.
            combo_estilo.hide()
            botao_cor.hide()
            linha.addStretch(1)

            self.element_layout.addWidget(container)
            self.element_widgets.append(container)


    def escolher_dos(self):
        nome, _ = QFileDialog.getOpenFileName(self, "Arquivo .dos")
        if nome:
            self.dos_file.setText(nome)

    def escolher_pdos_tot(self):
        nome, _ = QFileDialog.getOpenFileName(self, "Arquivo .pdos_tot")
        if nome:
            self.pdos_tot_file.setText(nome)

    def escolher_orbitals(self):
        nome = QFileDialog.getExistingDirectory(
            self, "Pasta orbitals"
        )
        if nome:
            self.orbitals_dir.setText(nome)

    def escolher_origem(self):
        nome = QFileDialog.getExistingDirectory(
            self, "Diretório com arquivos PDOS"
        )
        if nome:
            self.origem_dir.setText(nome)

    def escolher_destino(self):
        nome = QFileDialog.getExistingDirectory(
            self, "Diretório destino"
        )
        if nome:
            self.destino_dir.setText(nome)

    def escolher_cor(self, chave):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cores[chave] = c.name()
            self.atualizar_plot()

    def organizar_orbitais(self):
        try:
            contagem = organizar_arquivos_pdos(
                self.origem_dir.text(),
                self.destino_dir.text(),
            )

            self.orbitals_dir.setText(
                os.path.abspath(self.destino_dir.text())
            )

            self.status.setText(
                "Arquivos organizados: "
                + ", ".join(
                    f"{k}={v}" for k, v in contagem.items()
                )
            )

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def atualizar_modo_spin(self):
        """Mostra somente os controles pertinentes ao modo PDOS selecionado."""
        spin2 = self.spin_checkbox.isChecked()
        espelhado = spin2 and self.mirror_down.isChecked()
        globais = not spin2 or espelhado
        separados = spin2 and not espelhado

        def visivel_no_form(layout, widget, visible):
            widget.setVisible(visible)
            label = layout.labelForField(widget)
            if label is not None:
                label.setVisible(visible)

        eixos_layout = self.pdos_eixos_box.layout()

        # Eixos globais: somente nspin=1.
        for w in (
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.xmajor, self.ymajor, self.xminor, self.yminor,
        ):
            visivel_no_form(eixos_layout, w, globais)

        # Limites e incrementos UP/DOWN: somente nspin=2.
        for w in (
            self.pdos_up_xmin, self.pdos_up_xmax,
            self.pdos_up_ymin, self.pdos_up_ymax,
            self.pdos_dn_xmin, self.pdos_dn_xmax,
            self.pdos_dn_ymin, self.pdos_dn_ymax,
            self.pdos_up_xmajor, self.pdos_up_ymajor,
            self.pdos_up_xminor, self.pdos_up_yminor,
            self.pdos_dn_xmajor, self.pdos_dn_ymajor,
            self.pdos_dn_xminor, self.pdos_dn_yminor,
        ):
            visivel_no_form(eixos_layout, w, separados)

        self.pdos_spin_panels_box.setVisible(spin2)
        self.mirror_down.setVisible(spin2)

        # Mantém os checkboxes de seleção de curvas, mas centraliza
        # exclusivamente no editor visual cor, espessura e tipo de linha.
        for widget in (self.linewidth, self.fermi_width, self.style_fermi):
            PlotWidget.ocultar_controle_de_estilo(widget)
        for widget in getattr(self, '_pdos_botoes_estilo_extra', []):
            PlotWidget.ocultar_controle_de_estilo(widget)
        if getattr(self, '_ultimo_modo_editor', None) != spin2:
            self.plot._estilos_personalizados.clear()
            self._ultimo_modo_editor = spin2

        # Na primeira ativação, ampliar o limite global inferior para DOWN negativo.
        if espelhado and self.ymin.value() >= 0:
            self.ymin.setValue(-self.ymax.value())

        self.atualizar_plot()

    def carregar_dados(self):
        try:
            self.fermi = extrair_fermi_dos(self.dos_file.text())

            if self.spin_checkbox.isChecked():
                (
                    energia_abs,
                    dos_up, dos_down,
                    total_up, total_down
                ) = ler_pdos_tot_spin(
                    self.pdos_tot_file.text()
                )
                self.energia = energia_abs - self.fermi

                (
                    orb_up, orb_down,
                    elem_up, elem_down,
                    usados_orb, usados_elem
                ) = somar_pdos_spin(
                    self.orbitals_dir.text(), energia_abs
                )

                self.dos_total_up = total_up.copy()
                self.dos_total_down = total_down.copy()
                self.pdos_up = {k: v.copy() for k, v in orb_up.items()}
                self.pdos_down = {k: v.copy() for k, v in orb_down.items()}
                self.pdos_elementos_up = {k: v.copy() for k, v in elem_up.items()}
                self.pdos_elementos_down = {k: v.copy() for k, v in elem_down.items()}

                self._orig_spin = {
                    'total_up': self.dos_total_up.copy(),
                    'total_down': self.dos_total_down.copy(),
                    'orb_up': {k: v.copy() for k, v in self.pdos_up.items()},
                    'orb_down': {k: v.copy() for k, v in self.pdos_down.items()},
                    'elem_up': {k: v.copy() for k, v in self.pdos_elementos_up.items()},
                    'elem_down': {k: v.copy() for k, v in self.pdos_elementos_down.items()},
                }

                # Validação física/numérica: a soma de todos os WFCs deve
                # reconstruir as colunas PDOSup/PDOSdown do *.pdos_tot.
                reconstruido_up = np.zeros_like(total_up)
                reconstruido_down = np.zeros_like(total_down)
                for orbital in ("s", "p", "d", "f"):
                    reconstruido_up += orb_up[orbital]
                    reconstruido_down += orb_down[orbital]

                erro_up = float(np.max(np.abs(reconstruido_up - total_up)))
                erro_down = float(np.max(np.abs(reconstruido_down - total_down)))

                self.usados = usados_orb
                self.usados_elementos = usados_elem

                # Mantém as chaves usadas pela criação dinâmica dos controles.
                self.pdos_elementos = self.pdos_elementos_up
                self.atualizar_controles_elementos()

                max_up = float(np.max(np.abs(self.dos_total_up)))
                max_down = float(np.max(np.abs(self.dos_total_down)))

                self.status.setText(
                    f"nspin=2 | EFermi={self.fermi:.6f} eV | "
                    f"PDOS total max: UP={max_up:.4g}, DOWN={max_down:.4g} | "
                    f"erro soma WFC: UP={erro_up:.3g}, DOWN={erro_down:.3g} | "
                    f"orbitais: {', '.join(f'{k}:{v}' for k,v in usados_orb.items())} | "
                    f"elementos: {', '.join(f'{k}:{v}' for k,v in usados_elem.items())}"
                )
            else:
                (
                    self.energia,
                    self.dos_total,
                    self.pdos,
                    self.usados,
                ) = somar_pdos_por_orbital(
                    self.pdos_tot_file.text(),
                    self.orbitals_dir.text(),
                    self.fermi,
                )

                (
                    self.pdos_elementos,
                    self.usados_elementos,
                ) = somar_pdos_por_elemento(
                    self.energia,
                    self.orbitals_dir.text(),
                )

                self.dos_total_original = self.dos_total.copy()
                self.pdos_original = {
                    orbital: densidade.copy()
                    for orbital, densidade in self.pdos.items()
                }
                self.pdos_elementos_original = {
                    elemento: densidade.copy()
                    for elemento, densidade in self.pdos_elementos.items()
                }
                self.atualizar_controles_elementos()

                resumo_orb = ", ".join(f"{k}:{v}" for k,v in self.usados.items())
                resumo_elem = ", ".join(
                    f"{k}:{v}" for k,v in self.usados_elementos.items()
                )
                self.status.setText(
                    f"EFermi={self.fermi:.6f} eV | "
                    f"orbitais: {resumo_orb} | elementos: {resumo_elem}"
                )

            # -------------------------------------------------
            # VBM / CBM / GAP + CSV
            # Na aba PDOS, as bordas eletrônicas são obtidas do arquivo
            # de DOS total importado, evitando inferir gap de uma projeção.
            # -------------------------------------------------
            arquivo_dos = self.dos_file.text()
            dados_dos = np.loadtxt(arquivo_dos)
            if dados_dos.ndim != 2 or dados_dos.shape[1] < 2:
                raise ValueError(
                    "Arquivo DOS inválido para calcular VBM/CBM/gap."
                )

            energia_dos = dados_dos[:, 0] - self.fermi
            sistema = nome_sistema_de_arquivo(arquivo_dos)
            resultados_csv = []

            if self.spin_checkbox.isChecked():
                if dados_dos.shape[1] < 3:
                    raise ValueError(
                        "Para nspin=2, o DOS total deve conter "
                        "energia, DOS UP e DOS DOWN."
                    )
                r_up = calcular_bordas_por_dos(
                    energia_dos, dados_dos[:, 1], self.fermi
                )
                r_down = calcular_bordas_por_dos(
                    energia_dos, dados_dos[:, 2], self.fermi
                )
                r_total = calcular_bordas_por_dos(
                    energia_dos,
                    dados_dos[:, 1] + dados_dos[:, 2],
                    self.fermi,
                )
                resultados_csv.extend([
                    ("UP", r_up), ("DOWN", r_down), ("TOTAL", r_total)
                ])
            else:
                r_total = calcular_bordas_por_dos(
                    energia_dos, dados_dos[:, 1], self.fermi
                )
                resultados_csv.append(("TOTAL", r_total))

            caminho_csv = salvar_resultados_eletronicos_csv(
                arquivo_dos,
                sistema,
                "PDOS",
                self.fermi,
                "Fermi energy",
                resultados_csv,
            )

            self.status.setText(
                self.status.text()
                + f" | gap={resultados_csv[-1][1]['gap']:.6f} eV"
                + f" | CSV: {os.path.basename(caminho_csv)}"
            )

            self.atualizar_plot()
        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def cortar_pdos_bandas(self):
        if self.energia is None:
            QMessageBox.warning(self, 'PDOS', 'Carregue primeiro a PDOS.')
            return
        try:
            spin = self.spin_checkbox.isChecked()
            limites = limites_bandas_gap(self.window(), self.fermi, spin)
            if spin:
                orig = self._orig_spin
                for sufixo, canal in (('up', 'UP'), ('down', 'DOWN')):
                    lim = limites[canal]
                    setattr(self, 'dos_total_' + sufixo,
                            corte_gap_bandas(self.energia, orig['total_' + sufixo], lim))
                    setattr(self, 'pdos_' + sufixo, {
                        k: corte_gap_bandas(self.energia, v, lim)
                        for k, v in orig['orb_' + sufixo].items()})
                    setattr(self, 'pdos_elementos_' + sufixo, {
                        k: corte_gap_bandas(self.energia, v, lim)
                        for k, v in orig['elem_' + sufixo].items()})
                self.pdos_elementos = self.pdos_elementos_up
            else:
                lim = limites['TOTAL']
                self.dos_total = corte_gap_bandas(self.energia, self.dos_total_original, lim)
                self.pdos = {k: corte_gap_bandas(self.energia, v, lim)
                             for k, v in self.pdos_original.items()}
                self.pdos_elementos = {k: corte_gap_bandas(self.energia, v, lim)
                                      for k, v in self.pdos_elementos_original.items()}
            self.status.setText('Corte aplicado: ' + '; '.join(
                f'{k}: {v[0]:.4f} a {v[1]:.4f} eV' for k, v in limites.items()))
            self.atualizar_plot()
        except Exception as e:
            QMessageBox.warning(self, 'Corte pelo gap', str(e))

    def eliminar_ruido_gap_pdos(self):
        """
        Determina a região de baixa DOS que contém E=0 usando
        a DOS total e zera exatamente o mesmo intervalo em todas
        as contribuições projetadas.
        """
        if (
            self.energia is None
            or self.dos_total_original is None
        ):
            return

        try:
            limiar = self.noise_threshold.value()

            dos_limpa, e1, e2 = remover_ruido_gap(
                self.energia,
                self.dos_total_original,
                limiar
            )

            if e1 is None or e2 is None:
                self.status.setText(
                    "Nenhuma região de gap foi encontrada "
                    "com o limiar informado."
                )
                return

            # Índices do intervalo encontrado na DOS total
            mascara_gap = (
                (self.energia >= e1)
                & (self.energia <= e2)
            )

            # DOS total filtrada
            self.dos_total = dos_limpa

            # Orbitais filtrados usando o MESMO intervalo
            self.pdos = {}

            for orbital, densidade in self.pdos_original.items():
                limpa = densidade.copy()
                limpa[mascara_gap] = 0.0
                self.pdos[orbital] = limpa

            # Elementos filtrados usando o MESMO intervalo
            self.pdos_elementos = {}

            for elemento, densidade in self.pdos_elementos_original.items():
                limpa = densidade.copy()
                limpa[mascara_gap] = 0.0
                self.pdos_elementos[elemento] = limpa

            self.status.setText(
                f"Ruído removido no intervalo do gap: "
                f"{e1:.4f} a {e2:.4f} eV "
                f"(limiar DOS total = {limiar:g})."
            )

            self.atualizar_plot()

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )

    def restaurar_pdos_original(self):
        """
        Restaura todos os dados originais sem necessidade
        de reler os arquivos.
        """
        if self.spin_checkbox.isChecked():
            if not hasattr(self, '_orig_spin'):
                return
            orig = self._orig_spin
            for sufixo in ('up', 'down'):
                setattr(self, 'dos_total_' + sufixo, orig['total_' + sufixo].copy())
                setattr(self, 'pdos_' + sufixo,
                        {k: v.copy() for k, v in orig['orb_' + sufixo].items()})
                setattr(self, 'pdos_elementos_' + sufixo,
                        {k: v.copy() for k, v in orig['elem_' + sufixo].items()})
            self.pdos_elementos = self.pdos_elementos_up
            self.status.setText('PDOS original restaurada (UP/DOWN).')
            self.atualizar_plot()
            return
        if self.dos_total_original is None:
            return

        self.dos_total = self.dos_total_original.copy()

        self.pdos = {
            orbital: densidade.copy()
            for orbital, densidade in self.pdos_original.items()
        }

        self.pdos_elementos = {
            elemento: densidade.copy()
            for elemento, densidade in self.pdos_elementos_original.items()
        }

        self.status.setText(
            "DOS/PDOS originais restauradas."
        )

        self.atualizar_plot()

    def atualizar_plot(self):
        if self.energia is None:
            return
        if not self.auto_gap_bandas.isChecked():
            # Recupera as densidades originais de todos os canais.
            if self.spin_checkbox.isChecked() and getattr(self, '_orig_spin', None):
                orig = self._orig_spin
                for sufixo in ('up', 'down'):
                    if 'total_' + sufixo in orig:
                        setattr(self, 'dos_total_' + sufixo, orig['total_' + sufixo].copy())
                    if 'orb_' + sufixo in orig:
                        setattr(self, 'pdos_' + sufixo, {k: v.copy() for k, v in orig['orb_' + sufixo].items()})
                    if 'elem_' + sufixo in orig:
                        setattr(self, 'pdos_elementos_' + sufixo, {k: v.copy() for k, v in orig['elem_' + sufixo].items()})
            elif self.dos_total_original is not None:
                self.dos_total = self.dos_total_original.copy()
                self.pdos = {k: v.copy() for k, v in self.pdos_original.items()}
                self.pdos_elementos = {k: v.copy() for k, v in self.pdos_elementos_original.items()}
        if self.auto_gap_bandas.isChecked():
            try:
                spin = self.spin_checkbox.isChecked()
                limites = limites_bandas_gap(self.window(), self.fermi, spin)
                if spin:
                    orig = self._orig_spin
                    for sufixo, canal in (('up', 'UP'), ('down', 'DOWN')):
                        lim = limites[canal]
                        setattr(self, 'dos_total_' + sufixo,
                                corte_gap_bandas(self.energia, orig['total_' + sufixo], lim))
                        setattr(self, 'pdos_' + sufixo, {k: corte_gap_bandas(self.energia, v, lim)
                                for k, v in orig['orb_' + sufixo].items()})
                        setattr(self, 'pdos_elementos_' + sufixo, {k: corte_gap_bandas(self.energia, v, lim)
                                for k, v in orig['elem_' + sufixo].items()})
                else:
                    lim = limites['TOTAL']
                    self.dos_total = corte_gap_bandas(self.energia, self.dos_total_original, lim)
                    self.pdos = {k: corte_gap_bandas(self.energia, v, lim)
                                 for k, v in self.pdos_original.items()}
                    self.pdos_elementos = {k: corte_gap_bandas(self.energia, v, lim)
                                           for k, v in self.pdos_elementos_original.items()}
            except (ValueError, AttributeError, TypeError):
                pass  # Sem bandas carregadas, não supor um gap.

        if self.spin_checkbox.isChecked():
            if self.dos_total_up is None or self.dos_total_down is None:
                return
        elif self.dos_total is None:
            return

        try:
            mpl.rcParams["text.usetex"] = bool(
                self.latex_global.isChecked()
            )

            if self.latex_global.isChecked():
                mpl.rcParams["text.latex.preamble"] = (
                    r"\usepackage[version=4]{mhchem}"
                    r"\usepackage{amsmath}"
                    r"\usepackage{bm}"
                )

            # ==================================================
            # nspin = 2 -> matriz 2x2
            # linha 1: UP   | elemento | orbital
            # linha 2: DOWN | elemento | orbital
            # ==================================================
            if self.spin_checkbox.isChecked():
                espelhado = self.mirror_down.isChecked()
                if espelhado:
                    axes = self.plot.reset_pdos_mirrored_axes()
                    ax_elem_up = ax_elem_dn = axes[0]
                    ax_orb_up = ax_orb_dn = axes[1]
                else:
                    axes = self.plot.reset_pdos_spin_axes()
                    ax_elem_up = axes[0, 0]
                    ax_orb_up  = axes[0, 1]
                    ax_elem_dn = axes[1, 0]
                    ax_orb_dn  = axes[1, 1]

                # DOWN é mostrado em seu próprio painel. Se o usuário mantiver
                # "Espelhar DOWN", a densidade é desenhada negativa.
                sinal_down = -1.0 if self.mirror_down.isChecked() else 1.0

                # ---------- DOS total nos quatro painéis ----------
                # A curva total serve como referência tanto para a decomposição
                # por elemento quanto para a decomposição por orbital.
                if self.show_total.isChecked():
                    label_total = texto_latex_negrito(
                        "DOS total",
                        self.bold_legend.isChecked(),
                        self.latex_global.isChecked()
                    )

                    for ax_total, densidade_total in (
                        (ax_elem_up, self.dos_total_up),
                        (ax_orb_up, self.dos_total_up),
                        (ax_elem_dn, sinal_down * self.dos_total_down),
                        (ax_orb_dn, sinal_down * self.dos_total_down),
                    ):
                        ax_total.plot(
                            self.energia,
                            densidade_total,
                            color=self.cores["total"],
                            linewidth=self.linewidth.value(),
                            linestyle=self.estilos_linha["total"],
                            label=(label_total + (" DOWN" if espelhado and ax_total in (ax_elem_dn, ax_orb_dn) and densidade_total is not self.dos_total_up else "")),
                        )

                # ---------- PDOS por elemento: UP ----------
                for elemento, checkbox in self.element_checkboxes.items():
                    if checkbox.isChecked() and elemento in self.pdos_elementos_up:
                        ax_elem_up.plot(
                            self.energia,
                            self.pdos_elementos_up[elemento],
                            color=self.cores[elemento],
                            linewidth=self.linewidth.value(),
                            linestyle=self.estilos_linha.get(elemento, "-"),
                            label=texto_latex_negrito(
                                elemento,
                                self.bold_legend.isChecked(),
                                self.latex_global.isChecked()
                            ),
                        )

                # ---------- PDOS por elemento: DOWN ----------
                for elemento, checkbox in self.element_checkboxes.items():
                    if checkbox.isChecked() and elemento in self.pdos_elementos_down:
                        ax_elem_dn.plot(
                            self.energia,
                            sinal_down * self.pdos_elementos_down[elemento],
                            color=self.cores[elemento],
                            linewidth=self.linewidth.value(),
                            linestyle="--" if espelhado else self.estilos_linha.get(elemento, "-"),
                            label=texto_latex_negrito(
                                elemento + (" DOWN" if espelhado else ""),
                                self.bold_legend.isChecked(),
                                self.latex_global.isChecked()
                            ),
                        )

                # ---------- PDOS por orbital ----------
                config = [
                    ("s", self.show_s),
                    ("p", self.show_p),
                    ("d", self.show_d),
                    ("f", self.show_f),
                ]

                for orbital, checkbox in config:
                    if checkbox.isChecked() and self.usados.get(orbital, 0) > 0:
                        label = texto_latex_negrito(
                            f"Orbital {orbital}",
                            self.bold_legend.isChecked(),
                            self.latex_global.isChecked()
                        )

                        ax_orb_up.plot(
                            self.energia,
                            self.pdos_up[orbital],
                            color=self.cores[orbital],
                            linewidth=self.linewidth.value(),
                            linestyle=self.estilos_linha[orbital],
                            label=label,
                        )

                        ax_orb_dn.plot(
                            self.energia,
                            sinal_down * self.pdos_down[orbital],
                            color=self.cores[orbital],
                            linewidth=self.linewidth.value(),
                            linestyle="--" if espelhado else self.estilos_linha[orbital],
                            label=(label + " DOWN" if espelhado else label),
                        )

                # ---------- Formatação dos quatro painéis ----------
                painel_info = [
                    (
                        ax_elem_up, self.pdos_elem_up_visual,
                        self.pdos_up_xmin.value(), self.pdos_up_xmax.value(),
                        self.pdos_up_ymin.value(), self.pdos_up_ymax.value(),
                        self.pdos_up_xmajor.value(), self.pdos_up_ymajor.value(),
                        self.pdos_up_xminor.value(), self.pdos_up_yminor.value()
                    ),
                    (
                        ax_orb_up, self.pdos_orb_up_visual,
                        self.pdos_up_xmin.value(), self.pdos_up_xmax.value(),
                        self.pdos_up_ymin.value(), self.pdos_up_ymax.value(),
                        self.pdos_up_xmajor.value(), self.pdos_up_ymajor.value(),
                        self.pdos_up_xminor.value(), self.pdos_up_yminor.value()
                    ),
                    (
                        ax_elem_dn, self.pdos_elem_dn_visual,
                        self.pdos_dn_xmin.value(), self.pdos_dn_xmax.value(),
                        self.pdos_dn_ymin.value(), self.pdos_dn_ymax.value(),
                        self.pdos_dn_xmajor.value(), self.pdos_dn_ymajor.value(),
                        self.pdos_dn_xminor.value(), self.pdos_dn_yminor.value()
                    ),
                    (
                        ax_orb_dn, self.pdos_orb_dn_visual,
                        self.pdos_dn_xmin.value(), self.pdos_dn_xmax.value(),
                        self.pdos_dn_ymin.value(), self.pdos_dn_ymax.value(),
                        self.pdos_dn_xmajor.value(), self.pdos_dn_ymajor.value(),
                        self.pdos_dn_xminor.value(), self.pdos_dn_yminor.value()
                    ),
                ]

                if espelhado:
                    # Ambos os painéis usam os mesmos limites e ticks globais.
                    painel_info = [(
                        ax, cfg,
                        self.xmin.value(), self.xmax.value(),
                        self.ymin.value(), self.ymax.value(),
                        self.xmajor.value(), self.ymajor.value(),
                        self.xminor.value(), self.yminor.value(),
                    ) for ax, cfg in (
                        (ax_elem_up, self.pdos_elem_up_visual),
                        (ax_orb_up, self.pdos_orb_up_visual),
                    )]

                xlabel = self.xlabel_edit.text()
                ylabel = self.ylabel_edit.text()

                if self.bold_axis.isChecked() and not self.latex_global.isChecked():
                    xlabel = negrito_mathtext(xlabel)
                    ylabel = negrito_mathtext(ylabel)

                xlabel = texto_latex_negrito(
                    xlabel,
                    self.bold_axis.isChecked(),
                    self.latex_global.isChecked()
                )
                ylabel = texto_latex_negrito(
                    ylabel,
                    self.bold_axis.isChecked(),
                    self.latex_global.isChecked()
                )

                def fmt(v, pos):
                    if abs(v) < 1e-12:
                        v = 0.0
                    s = (
                        str(int(round(v)))
                        if abs(v - round(v)) < 1e-10
                        else f"{v:g}"
                    )
                    return r"$\mathbf{" + s + r"}$"

                for (
                    ax, cfg, xmin, xmax, ymin, ymax,
                    xmajor, ymajor, xminor, yminor
                ) in painel_info:
                    titulo_painel = cfg.titulo.text()
                    if xmin >= xmax:
                        raise ValueError(
                            f"{titulo_painel}: X mínimo deve ser menor que X máximo."
                        )
                    if ymin >= ymax:
                        raise ValueError(
                            f"{titulo_painel}: Y mínimo deve ser menor que Y máximo."
                        )

                    if self.show_fermi.isChecked():
                        ax.axvline(
                            0.0,
                            color=self.cores["fermi"],
                            linestyle=self.estilos_linha["fermi"],
                            linewidth=self.fermi_width.value(),
                        )

                    ax.set_xlim(xmin, xmax)
                    ax.set_ylim(ymin, ymax)

                    ax.xaxis.set_major_locator(MultipleLocator(xmajor))
                    ax.yaxis.set_major_locator(MultipleLocator(ymajor))

                    if xminor > 1:
                        ax.xaxis.set_minor_locator(AutoMinorLocator(xminor))
                    if yminor > 1:
                        ax.yaxis.set_minor_locator(AutoMinorLocator(yminor))

                    if self.bold_ticks.isChecked() and self.latex_global.isChecked():
                        ax.xaxis.set_major_formatter(FuncFormatter(fmt))
                        ax.yaxis.set_major_formatter(FuncFormatter(fmt))
                    else:
                        ax.xaxis.set_major_formatter(ScalarFormatter())
                        ax.yaxis.set_major_formatter(ScalarFormatter())

                    ax.set_xlabel(
                        xlabel if cfg.show_xlabel.isChecked() else "",
                        fontsize=self.font_axis.value(),
                        fontweight="bold" if self.bold_axis.isChecked() else "normal"
                    )
                    ax.set_ylabel(
                        ylabel if cfg.show_ylabel.isChecked() else "",
                        fontsize=self.font_axis.value(),
                        fontweight="bold" if self.bold_axis.isChecked() else "normal"
                    )

                    ax.set_title(
                        texto_latex_negrito(
                            titulo_painel,
                            self.bold_title.isChecked(),
                            self.latex_global.isChecked()
                        ) if cfg.show_title.isChecked() else "",
                        fontsize=self.font_title.value(),
                        fontweight="bold" if self.bold_title.isChecked() else "normal"
                    )

                    ax.tick_params(
                        axis="x", which="both",
                        bottom=cfg.show_xticks.isChecked(),
                        labelbottom=cfg.show_xnumbers.isChecked()
                    )
                    ax.tick_params(
                        axis="y", which="both",
                        left=cfg.show_yticks.isChecked(),
                        labelleft=cfg.show_ynumbers.isChecked()
                    )

                    ax.tick_params(
                        axis="x", which="major",
                        labelsize=self.font_tick.value(),
                        bottom=cfg.show_xticks.isChecked(),
                        labelbottom=cfg.show_xnumbers.isChecked()
                    )
                    ax.tick_params(
                        axis="y", which="major",
                        labelsize=self.font_tick.value(),
                        left=cfg.show_yticks.isChecked(),
                        labelleft=cfg.show_ynumbers.isChecked()
                    )

                    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                        lbl.set_fontsize(self.font_tick.value())
                        lbl.set_fontweight(
                            "bold" if self.bold_ticks.isChecked() else "normal"
                        )

                    if self.show_grid.isChecked():
                        ax.grid(True, alpha=0.25)

                    if self.show_legend.isChecked():
                        handles, labels = ax.get_legend_handles_labels()
                        if handles:
                            leg = ax.legend(
                                fontsize=self.font_legend.value(),
                                frameon=self.legend_frame.isChecked()
                            )
                            for txt in leg.get_texts():
                                txt.set_fontsize(self.font_legend.value())
                                txt.set_fontweight(
                                    "bold"
                                    if self.bold_legend.isChecked()
                                    else "normal"
                                )

                # Título global opcional informado pelo usuário.
                if self.title_edit.text().strip():
                    self.plot.figure.suptitle(
                        texto_latex_negrito(
                            self.title_edit.text().strip(),
                            self.bold_title.isChecked(),
                            self.latex_global.isChecked()
                        ),
                        fontsize=self.font_title.value(),
                        fontweight="bold" if self.bold_title.isChecked() else "normal"
                    )

                # Não redimensiona a Figure na prévia: evita ghosting no Qt.
                self.plot.figure.subplots_adjust(
                    left=0.10, right=0.98, bottom=0.10,
                    top=0.88 if self.title_edit.text().strip() else 0.94,
                    wspace=self.pdos_wspace.value(),
                    hspace=self.pdos_hspace.value()
                )
                self.plot.redraw(use_tight_layout=False)
                return

            # ==================================================
            # nspin = 1 -> comportamento original da aba PDOS
            # ==================================================
            axes = self.plot.reset_pdos_mirrored_axes()
            ax_elem, ax_orb = axes[0], axes[1]
            ax = ax_elem

            if self.show_total.isChecked():
                for ax in (ax_elem, ax_orb):
                    ax.plot(
                        self.energia,
                        self.dos_total,
                        color=self.cores["total"],
                        linewidth=self.linewidth.value(),
                        linestyle=self.estilos_linha["total"],
                        label=texto_latex_negrito(
                            "DOS total",
                            self.bold_legend.isChecked(),
                            self.latex_global.isChecked()
                        ),
                    )

            config = [
                ("s", self.show_s),
                ("p", self.show_p),
                ("d", self.show_d),
                ("f", self.show_f),
            ]

            for orbital, checkbox in config:
                if checkbox.isChecked() and self.usados.get(orbital, 0) > 0:
                    ax_orb.plot(
                        self.energia,
                        self.pdos[orbital],
                        color=self.cores[orbital],
                        linewidth=self.linewidth.value(),
                        linestyle=self.estilos_linha[orbital],
                        label=texto_latex_negrito(
                            f"Orbital {orbital}",
                            self.bold_legend.isChecked(),
                            self.latex_global.isChecked()
                        ),
                    )

            for elemento, checkbox in self.element_checkboxes.items():
                if checkbox.isChecked() and elemento in self.pdos_elementos:
                    ax_elem.plot(
                        self.energia,
                        self.pdos_elementos[elemento],
                        color=self.cores[elemento],
                        linewidth=self.linewidth.value(),
                        linestyle=self.estilos_linha.get(elemento, "--"),
                        label=texto_latex_negrito(
                            elemento,
                            self.bold_legend.isChecked(),
                            self.latex_global.isChecked()
                        ),
                    )

            if self.show_fermi.isChecked():
                for ax in (ax_elem, ax_orb):
                    ax.axvline(
                        0.0,
                        color=self.cores["fermi"],
                        linestyle=self.estilos_linha["fermi"],
                        linewidth=self.fermi_width.value(),
                        label=r"$E_F$",
                    )

            for ax, titulo_painel in ((ax_elem, "PDOS por espécie"), (ax_orb, "PDOS por orbital")):
                ax.set_xlim(self.xmin.value(), self.xmax.value())
                ax.set_ylim(self.ymin.value(), self.ymax.value())

                ax.xaxis.set_major_locator(MultipleLocator(self.xmajor.value()))
                ax.yaxis.set_major_locator(MultipleLocator(self.ymajor.value()))

                if self.xminor.value() > 1:
                    ax.xaxis.set_minor_locator(AutoMinorLocator(self.xminor.value()))
                if self.yminor.value() > 1:
                    ax.yaxis.set_minor_locator(AutoMinorLocator(self.yminor.value()))

                if self.bold_ticks.isChecked() and self.latex_global.isChecked():
                    def fmt_single(v, pos):
                        if abs(v) < 1e-12:
                            v = 0.0
                        s = (
                            str(int(round(v)))
                            if abs(v-round(v)) < 1e-10
                            else f"{v:g}"
                        )
                        return r"$\mathbf{" + s + r"}$"

                    ax.xaxis.set_major_formatter(FuncFormatter(fmt_single))
                    ax.yaxis.set_major_formatter(FuncFormatter(fmt_single))
                else:
                    ax.xaxis.set_major_formatter(ScalarFormatter())
                    ax.yaxis.set_major_formatter(ScalarFormatter())

                xlabel = self.xlabel_edit.text()
                ylabel = self.ylabel_edit.text()

                if self.bold_axis.isChecked() and not self.latex_global.isChecked():
                    xlabel = negrito_mathtext(xlabel)
                    ylabel = negrito_mathtext(ylabel)

                xlabel = texto_latex_negrito(
                    xlabel, self.bold_axis.isChecked(), self.latex_global.isChecked()
                )
                ylabel = texto_latex_negrito(
                    ylabel, self.bold_axis.isChecked(), self.latex_global.isChecked()
                )

                ax.set_xlabel(
                    xlabel,
                    fontsize=self.font_axis.value(),
                    fontweight="bold" if self.bold_axis.isChecked() else "normal"
                )
                ax.set_ylabel(
                    ylabel,
                    fontsize=self.font_axis.value(),
                    fontweight="bold" if self.bold_axis.isChecked() else "normal"
                )

                ax.set_title(
                    texto_latex_negrito(
                        titulo_painel,
                        self.bold_title.isChecked(),
                        self.latex_global.isChecked()
                    ),
                    fontsize=self.font_title.value(),
                    fontweight="bold" if self.bold_title.isChecked() else "normal"
                )

                tamanho = self.font_tick.value()
                ax.tick_params(axis="both", which="major", labelsize=tamanho)

                for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                    lbl.set_fontsize(tamanho)
                    lbl.set_fontweight(
                        "bold" if self.bold_ticks.isChecked() else "normal"
                    )

                if self.show_grid.isChecked():
                    ax.grid(True, alpha=0.25)

                if self.show_legend.isChecked():
                    handles, labels = ax.get_legend_handles_labels()
                    if handles:
                        leg = ax.legend(
                            fontsize=self.font_legend.value(),
                            frameon=self.legend_frame.isChecked()
                        )
                        for txt in leg.get_texts():
                            txt.set_fontsize(self.font_legend.value())
                            txt.set_fontweight(
                                "bold" if self.bold_legend.isChecked() else "normal"
                            )

                if self.title_edit.text().strip():
                    self.plot.figure.suptitle(
                        texto_latex_negrito(self.title_edit.text(), self.bold_title.isChecked(), self.latex_global.isChecked()),
                        fontsize=self.font_title.value(),
                        fontweight="bold" if self.bold_title.isChecked() else "normal"
                    )
                self.plot.figure.subplots_adjust(left=0.10, right=0.98, bottom=0.12,
                    top=0.86 if self.title_edit.text().strip() else 0.90,
                    wspace=self.pdos_wspace.value())
                self.plot.redraw(use_tight_layout=False)

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))


    def salvar_figura(self):
        if self.energia is None:
            return

        nome, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar figura",
            "pdos.pdf",
            "PDF (*.pdf);;PNG (*.png);;SVG (*.svg)",
        )

        if not nome:
            return

        tamanho_original = (
            self.plot.figure.get_size_inches().copy()
        )

        try:
            self.plot.figure.set_size_inches(
                self.fig_w.value(),
                self.fig_h.value(),
                forward=False,
            )

            self.plot.figure.savefig(
                nome,
                dpi=self.dpi.value(),
                bbox_inches="tight",
            )

        finally:
            self.plot.figure.set_size_inches(
                tamanho_original[0],
                tamanho_original[1],
                forward=False,
            )
            self.plot.canvas.draw()


