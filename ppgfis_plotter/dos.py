# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *
from .analysis import *
from .readers import *
from .exports import *
from .plotting import *
from .ui_helpers import *

class DOSPage(QWidget):

    def __init__(self, back_callback, parent=None):
        super().__init__(parent)

        self.back_callback = back_callback

        self.energia = None
        self.dos_original = None
        self.dos_plot = None
        self.dos_up_original = None
        self.dos_down_original = None
        self.dos_up_plot = None
        self.dos_down_plot = None
        self.fermi = None

        self.cor_dos = "#000000"
        self.cor_dos_up = "#1f77b4"
        self.cor_dos_down = "#d62728"
        self.cor_fermi = "#d62728"

        root = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)

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

    # --------------------------------------------------------
    # CONTROLES
    # --------------------------------------------------------

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
        # Arquivo
        # ----------------------------------------------------

        box = QGroupBox("Arquivo DOS")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.file_edit = QLineEdit("hBN2D.dos")

        btn = QPushButton("Abrir")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_arquivo)

        row = QHBoxLayout()
        row.addWidget(self.file_edit)
        row.addWidget(btn)

        form.addRow("Arquivo:", row)

        self.spin_checkbox = QCheckBox("Cálculo com polarização de spin (nspin = 2)")
        self.spin_checkbox.stateChanged.connect(
            lambda _state: self.atualizar_modo_spin()
        )
        form.addRow(self.spin_checkbox)

        self.mirror_down = QCheckBox("Espelhar canal DOWN (valores negativos)")
        self.mirror_down.setChecked(False)
        self.mirror_down.stateChanged.connect(
            lambda _state: self.atualizar_modo_spin()
        )
        form.addRow(self.mirror_down)

        btn = QPushButton("Carregar dados")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.carregar_dados)
        form.addRow(btn)

        self.form.addWidget(box)

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
        self.ylabel_edit = QLineEdit("DOS (states/eV/unit cell)")

        form.addRow("Título:", self.title_edit)
        form.addRow("Eixo X:", self.xlabel_edit)
        form.addRow("Eixo Y:", self.ylabel_edit)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Eixos
        # ----------------------------------------------------

        box = QGroupBox("Eixos")
        self.dos_eixos_box = box
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

        # Limites independentes usados somente no modo nspin=2.
        self.dos_up_xmin = self.dspin(-1000, 1000, -8, 0.5)
        self.dos_up_xmax = self.dspin(-1000, 1000, 8, 0.5)
        self.dos_up_ymin = self.dspin(-10000, 10000, 0, 1)
        self.dos_up_ymax = self.dspin(-10000, 10000, 80, 1)

        self.dos_dn_xmin = self.dspin(-1000, 1000, -8, 0.5)
        self.dos_dn_xmax = self.dspin(-1000, 1000, 8, 0.5)
        self.dos_dn_ymin = self.dspin(-10000, 10000, 0, 1)
        self.dos_dn_ymax = self.dspin(-10000, 10000, 80, 1)

        # Incrementos locais do painel UP.
        self.dos_up_xmajor = self.dspin(0.01, 1000, 2, 0.5)
        self.dos_up_ymajor = self.dspin(0.01, 10000, 10, 1)
        self.dos_up_xminor = QSpinBox()
        self.dos_up_yminor = QSpinBox()
        self.dos_up_xminor.setRange(1, 20)
        self.dos_up_yminor.setRange(1, 20)
        self.dos_up_xminor.setValue(2)
        self.dos_up_yminor.setValue(2)

        # Incrementos locais do painel DOWN.
        self.dos_dn_xmajor = self.dspin(0.01, 1000, 2, 0.5)
        self.dos_dn_ymajor = self.dspin(0.01, 10000, 10, 1)
        self.dos_dn_xminor = QSpinBox()
        self.dos_dn_yminor = QSpinBox()
        self.dos_dn_xminor.setRange(1, 20)
        self.dos_dn_yminor.setRange(1, 20)
        self.dos_dn_xminor.setValue(2)
        self.dos_dn_yminor.setValue(2)

        for w in (
            self.dos_up_xmajor, self.dos_up_ymajor,
            self.dos_up_xminor, self.dos_up_yminor,
            self.dos_dn_xmajor, self.dos_dn_ymajor,
            self.dos_dn_xminor, self.dos_dn_yminor,
        ):
            w.valueChanged.connect(self.atualizar_plot)

        form.addRow("UP - X mínimo:", self.dos_up_xmin)
        form.addRow("UP - X máximo:", self.dos_up_xmax)
        form.addRow("UP - Incremento X:", self.dos_up_xmajor)
        form.addRow("UP - Subdivisões minor X:", self.dos_up_xminor)
        form.addRow("UP - Y mínimo:", self.dos_up_ymin)
        form.addRow("UP - Y máximo:", self.dos_up_ymax)
        form.addRow("UP - Incremento Y:", self.dos_up_ymajor)
        form.addRow("UP - Subdivisões minor Y:", self.dos_up_yminor)

        form.addRow("DOWN - X mínimo:", self.dos_dn_xmin)
        form.addRow("DOWN - X máximo:", self.dos_dn_xmax)
        form.addRow("DOWN - Incremento X:", self.dos_dn_xmajor)
        form.addRow("DOWN - Subdivisões minor X:", self.dos_dn_xminor)
        form.addRow("DOWN - Y mínimo:", self.dos_dn_ymin)
        form.addRow("DOWN - Y máximo:", self.dos_dn_ymax)
        form.addRow("DOWN - Incremento Y:", self.dos_dn_ymajor)
        form.addRow("DOWN - Subdivisões minor Y:", self.dos_dn_yminor)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Painéis nspin=2
        # ----------------------------------------------------
        box = QGroupBox("Painéis DOS (nspin = 2)")
        self.dos_spin_panels_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.dos_up_visual = PainelVisualControls(self, "DOS UP")
        self.dos_dn_visual = PainelVisualControls(self, "DOS DOWN")
        self.dos_up_visual.add_to_form(form, "UP")
        self.dos_dn_visual.add_to_form(form, "DOWN")

        self.dos_wspace = self.dspin(0.0, 2.0, 0.30, 0.05)
        self.dos_wspace.valueChanged.connect(self.atualizar_plot)
        form.addRow("Espaçamento horizontal:", self.dos_wspace)

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

        nota_ticks = QLabel(
            "O tamanho dos números é aplicado diretamente aos ticks "
            "depois da criação dos locators/formatters."
        )
        nota_ticks.setWordWrap(True)
        nota_ticks.setStyleSheet("color: #666666; font-size: 9pt;")
        form.addRow(nota_ticks)

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
        # LaTeX / mhchem
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
        # Aparência
        # ----------------------------------------------------

        box = QGroupBox("Aparência")
        self.dos_appearance_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.btn_cor_dos_nspin1 = QPushButton("Cor da DOS (nspin=1)")
        self.btn_cor_dos_nspin1.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_dos_nspin1.setMinimumWidth(0)
        self.btn_cor_dos_nspin1.clicked.connect(self.escolher_cor_dos)
        form.addRow(self.btn_cor_dos_nspin1)

        self.btn_cor_dos_up = QPushButton("Cor DOS UP")
        self.btn_cor_dos_up.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_dos_up.setMinimumWidth(0)
        self.btn_cor_dos_up.clicked.connect(lambda: self.escolher_cor_dos_spin("up"))
        form.addRow(self.btn_cor_dos_up)

        self.btn_cor_dos_down = QPushButton("Cor DOS DOWN")
        self.btn_cor_dos_down.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_dos_down.setMinimumWidth(0)
        self.btn_cor_dos_down.clicked.connect(lambda: self.escolher_cor_dos_spin("down"))
        form.addRow(self.btn_cor_dos_down)

        btn = QPushButton("Cor de EF")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_cor_fermi)
        form.addRow(btn)
        self._pdos_botoes_estilo_extra = [btn]

        self.linewidth = self.dspin(0.1, 10, 1.5, 0.1)
        self.fermi_width = self.dspin(0.1, 10, 0.8, 0.1)

        form.addRow("Espessura DOS:", self.linewidth)
        form.addRow("Espessura EF:", self.fermi_width)

        self.show_fermi = QCheckBox("Mostrar EF")
        self.show_fermi.setChecked(True)

        self.show_grid = QCheckBox("Mostrar grade")
        self.show_legend = QCheckBox("Mostrar legenda")
        self.show_legend.setChecked(False)
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

        self.form.addWidget(box)

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

        self.threshold = self.dspin(0, 1000, 0.01, 0.001)
        self.threshold.setDecimals(6)

        form.addRow("Limiar DOS:", self.threshold)

        btn = QPushButton("Eliminar ruído no gap")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.eliminar_ruido)
        form.addRow(btn)
        self.auto_gap_bandas = QCheckBox('Aplicar corte na lacuna (gap)')
        self.auto_gap_bandas.setChecked(False)
        self.auto_gap_bandas.toggled.connect(self.atualizar_plot)
        form.addRow(self.auto_gap_bandas)
        btn_bandas = QPushButton('Zerar DOS pelo gap das bandas')
        btn_bandas.clicked.connect(self.cortar_dos_bandas)
        form.addRow(btn_bandas)

        btn = QPushButton("Restaurar DOS original")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.restaurar_dos)
        form.addRow(btn)

        info = QLabel(
            "O filtro zera apenas a região contínua de baixa DOS "
            "que contém E=0, preservando a banda de condução real."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666666; font-size: 9pt;")
        form.addRow(info)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Figura
        # ----------------------------------------------------

        box = QGroupBox("Figura")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.fig_w = self.dspin(3, 30, 8, 0.5)
        self.fig_h = self.dspin(3, 30, 6, 0.5)
        self.dpi = self.ispin(72, 2400, 300)

        form.addRow("Largura exportação:", self.fig_w)
        form.addRow("Altura exportação:", self.fig_h)
        form.addRow("DPI:", self.dpi)

        self.form.addWidget(box)

        # ----------------------------------------------------
        # Ações
        # ----------------------------------------------------

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

        self.status = QLabel("Carregue um arquivo .dos.")
        self.status.setWordWrap(True)
        self.form.addWidget(self.status)

        self.form.addStretch()

    # --------------------------------------------------------
    # SPINBOXES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Arquivo / cores
    # --------------------------------------------------------

    def escolher_arquivo(self):

        nome, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo DOS"
        )

        if nome:
            self.file_edit.setText(nome)

        self.atualizar_modo_spin()

    def escolher_cor_dos(self):

        c = QColorDialog.getColor()

        if c.isValid():
            self.cor_dos = c.name()
            self.atualizar_plot()

    def escolher_cor_dos_spin(self, canal):
        atual = self.cor_dos_up if canal == "up" else self.cor_dos_down
        cor = QColorDialog.getColor(QColor(atual), self)
        if cor.isValid():
            if canal == "up":
                self.cor_dos_up = cor.name()
            else:
                self.cor_dos_down = cor.name()
            self.atualizar_plot()

    def escolher_cor_fermi(self):

        c = QColorDialog.getColor()

        if c.isValid():
            self.cor_fermi = c.name()
            self.atualizar_plot()

    # --------------------------------------------------------
    # Dados
    # --------------------------------------------------------

    def atualizar_modo_spin(self):
        """Mostra somente os controles pertinentes ao modo DOS selecionado."""
        spin2 = self.spin_checkbox.isChecked()
        espelhado = spin2 and self.mirror_down.isChecked()
        globais = not spin2 or espelhado
        separados = spin2 and not espelhado

        def visivel_no_form(layout, widget, visible):
            widget.setVisible(visible)
            label = layout.labelForField(widget)
            if label is not None:
                label.setVisible(visible)

        eixos_layout = self.dos_eixos_box.layout()

        # Controles globais de eixos são do nspin=1.
        for w in (
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.xmajor, self.ymajor, self.xminor, self.yminor,
        ):
            visivel_no_form(eixos_layout, w, globais)

        # Controles locais UP/DOWN são exclusivos do nspin=2.
        for w in (
            self.dos_up_xmin, self.dos_up_xmax,
            self.dos_up_ymin, self.dos_up_ymax,
            self.dos_dn_xmin, self.dos_dn_xmax,
            self.dos_dn_ymin, self.dos_dn_ymax,
            self.dos_up_xmajor, self.dos_up_ymajor,
            self.dos_up_xminor, self.dos_up_yminor,
            self.dos_dn_xmajor, self.dos_dn_ymajor,
            self.dos_dn_xminor, self.dos_dn_yminor,
        ):
            visivel_no_form(eixos_layout, w, separados)

        self.dos_spin_panels_box.setVisible(spin2)
        self.mirror_down.setVisible(spin2)

        # Todas as cores, larguras e estilos ficam no editor da pré-visualização.
        for widget in (self.btn_cor_dos_nspin1, self.btn_cor_dos_up,
                       self.btn_cor_dos_down, self.linewidth, self.fermi_width):
            PlotWidget.ocultar_controle_de_estilo(widget)
        for widget in getattr(self, '_dos_botoes_estilo_extra', []):
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
            arquivo = self.file_edit.text()
            self.fermi = extrair_fermi_dos(arquivo)
            dados = np.loadtxt(arquivo)

            if dados.ndim != 2:
                raise ValueError("Arquivo DOS inválido.")

            self.energia = dados[:, 0] - self.fermi

            if self.spin_checkbox.isChecked():
                if dados.shape[1] < 3:
                    raise ValueError(
                        "Para nspin=2, o arquivo DOS deve possuir pelo menos "
                        "três colunas: energia, DOS UP e DOS DOWN."
                    )
                self.dos_up_original = dados[:, 1].copy()
                self.dos_down_original = dados[:, 2].copy()
                self.dos_up_plot = self.dos_up_original.copy()
                self.dos_down_plot = self.dos_down_original.copy()
                self.dos_original = self.dos_plot = None
                self.status.setText(
                    f"nspin=2 | EFermi = {self.fermi:.6f} eV | "
                    f"{len(self.energia)} pontos."
                )
            else:
                if dados.shape[1] < 2:
                    raise ValueError("O arquivo DOS deve possuir ao menos duas colunas.")
                self.dos_original = dados[:, 1].copy()
                self.dos_plot = self.dos_original.copy()
                self.dos_up_original = self.dos_down_original = None
                self.dos_up_plot = self.dos_down_plot = None
                self.status.setText(
                    f"EFermi = {self.fermi:.6f} eV | "
                    f"{len(self.dos_plot)} pontos carregados."
                )

            # -------------------------------------------------
            # VBM / CBM / GAP estimados pela DOS + CSV
            # -------------------------------------------------
            sistema = nome_sistema_de_arquivo(arquivo)
            resultados_csv = []

            if self.spin_checkbox.isChecked():
                r_up = calcular_bordas_por_dos(
                    self.energia, self.dos_up_original, self.fermi
                )
                r_down = calcular_bordas_por_dos(
                    self.energia, self.dos_down_original, self.fermi
                )
                r_total = calcular_bordas_por_dos(
                    self.energia,
                    self.dos_up_original + self.dos_down_original,
                    self.fermi,
                )
                resultados_csv.extend([
                    ("UP", r_up), ("DOWN", r_down), ("TOTAL", r_total)
                ])
            else:
                r_total = calcular_bordas_por_dos(
                    self.energia, self.dos_original, self.fermi
                )
                resultados_csv.append(("TOTAL", r_total))

            caminho_csv = salvar_resultados_eletronicos_csv(
                arquivo,
                sistema,
                "DOS",
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

    # --------------------------------------------------------
    # Filtro de ruído
    # --------------------------------------------------------

    def cortar_dos_bandas(self):
        if self.energia is None:
            QMessageBox.warning(self, 'DOS', 'Carregue primeiro a DOS.')
            return
        try:
            spin = self.spin_checkbox.isChecked()
            limites = limites_bandas_gap(self.window(), self.fermi, spin)
            if spin:
                self.dos_up_plot = corte_gap_bandas(self.energia, self.dos_up_original, limites['UP'])
                self.dos_down_plot = corte_gap_bandas(self.energia, self.dos_down_original, limites['DOWN'])
            else:
                self.dos_plot = corte_gap_bandas(self.energia, self.dos_original, limites['TOTAL'])
            self.status.setText('Corte aplicado: ' + '; '.join(
                f'{k}: {v[0]:.4f} a {v[1]:.4f} eV' for k, v in limites.items()))
            self.atualizar_plot()
        except Exception as e:
            QMessageBox.warning(self, 'Corte pelo gap', str(e))

    def eliminar_ruido(self):

        if self.energia is None:
            return

        limpa, e1, e2 = remover_ruido_gap(
            self.energia,
            self.dos_original,
            self.threshold.value()
        )

        self.dos_plot = limpa

        if e1 is None:
            self.status.setText(
                "Nenhuma região de baixa DOS foi encontrada."
            )
        else:
            self.status.setText(
                f"Ruído eliminado entre {e1:.4f} e {e2:.4f} eV "
                f"(limiar = {self.threshold.value():g})."
            )

        self.atualizar_plot()

    def restaurar_dos(self):

        if self.dos_original is None and self.dos_up_original is None:
            return

        if self.spin_checkbox.isChecked():
            self.dos_up_plot = self.dos_up_original.copy()
            self.dos_down_plot = self.dos_down_original.copy()
        else:
            self.dos_plot = self.dos_original.copy()
        self.status.setText("DOS original restaurada.")
        self.atualizar_plot()

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    def atualizar_plot(self):
        if self.energia is None:
            return
        if not self.auto_gap_bandas.isChecked():
            # Retorna às curvas originais ao desativar o corte automático.
            if self.spin_checkbox.isChecked():
                if self.dos_up_original is not None:
                    self.dos_up_plot = self.dos_up_original.copy()
                if self.dos_down_original is not None:
                    self.dos_down_plot = self.dos_down_original.copy()
            elif self.dos_original is not None:
                self.dos_plot = self.dos_original.copy()
        if self.auto_gap_bandas.isChecked():
            try:
                limites = limites_bandas_gap(self.window(), self.fermi,
                                            self.spin_checkbox.isChecked())
                if self.spin_checkbox.isChecked():
                    self.dos_up_plot = corte_gap_bandas(self.energia, self.dos_up_original, limites['UP'])
                    self.dos_down_plot = corte_gap_bandas(self.energia, self.dos_down_original, limites['DOWN'])
                else:
                    self.dos_plot = corte_gap_bandas(self.energia, self.dos_original, limites['TOTAL'])
            except (ValueError, AttributeError, TypeError):
                pass  # Bandas ainda não carregadas: preserva a curva sem alteração.
        if self.spin_checkbox.isChecked():
            if self.dos_up_plot is None or self.dos_down_plot is None:
                return
        elif self.dos_plot is None:
            return

        try:
            mpl.rcParams["text.usetex"] = bool(self.latex_global.isChecked())

            if self.latex_global.isChecked():
                mpl.rcParams["text.latex.preamble"] = (
                    r"\usepackage[version=4]{mhchem}"
                    r"\usepackage{amsmath}"
                    r"\usepackage{bm}"
                )

            # ------------------------------------------------
            # nspin=2: DOS UP e DOS DOWN lado a lado
            # ------------------------------------------------
            if self.spin_checkbox.isChecked():
                espelhado = self.mirror_down.isChecked()
                if espelhado:
                    ax_up = ax_dn = self.plot.reset_dos_mirrored_axes()
                else:
                    axes = self.plot.reset_dos_spin_axes()
                    ax_up, ax_dn = axes[0], axes[1]

                down = (
                    -self.dos_down_plot
                    if self.mirror_down.isChecked()
                    else self.dos_down_plot
                )

                ax_up.plot(
                    self.energia, self.dos_up_plot,
                    color=self.cor_dos_up,
                    linewidth=self.linewidth.value(),
                    label=texto_latex_negrito(
                        "DOS UP", self.bold_legend.isChecked(),
                        self.latex_global.isChecked()
                    )
                )
                ax_dn.plot(
                    self.energia, down,
                    color=self.cor_dos_down,
                    linewidth=self.linewidth.value(),
                    label=texto_latex_negrito(
                        "DOS DOWN", self.bold_legend.isChecked(),
                        self.latex_global.isChecked()
                    )
                )

                limites = (
                    (
                        ax_up, "DOS UP",
                        self.dos_up_xmin.value(), self.dos_up_xmax.value(),
                        self.dos_up_ymin.value(), self.dos_up_ymax.value(),
                        self.dos_up_xmajor.value(), self.dos_up_ymajor.value(),
                        self.dos_up_xminor.value(), self.dos_up_yminor.value()
                    ),
                    (
                        ax_dn, "DOS DOWN",
                        self.dos_dn_xmin.value(), self.dos_dn_xmax.value(),
                        self.dos_dn_ymin.value(), self.dos_dn_ymax.value(),
                        self.dos_dn_xmajor.value(), self.dos_dn_ymajor.value(),
                        self.dos_dn_xminor.value(), self.dos_dn_yminor.value()
                    ),
                )

                if espelhado:
                    # Eixos globais controlam exclusivamente o painel combinado.
                    limites = ((
                        ax_up, "DOS UP + DOWN",
                        self.xmin.value(), self.xmax.value(),
                        self.ymin.value(), self.ymax.value(),
                        self.xmajor.value(), self.ymajor.value(),
                        self.xminor.value(), self.yminor.value(),
                    ),)

                xlabel = self.xlabel_edit.text()
                ylabel = self.ylabel_edit.text()

                if self.bold_axis.isChecked() and not self.latex_global.isChecked():
                    xlabel = negrito_mathtext(xlabel)
                    ylabel = negrito_mathtext(ylabel)

                xlabel = texto_latex_negrito(
                    xlabel, self.bold_axis.isChecked(),
                    self.latex_global.isChecked()
                )
                ylabel = texto_latex_negrito(
                    ylabel, self.bold_axis.isChecked(),
                    self.latex_global.isChecked()
                )

                def fmt_num(v, pos):
                    if abs(v) < 1e-12:
                        v = 0.0
                    s = (
                        str(int(round(v)))
                        if abs(v-round(v)) < 1e-10
                        else f"{v:g}"
                    )
                    return r"$\mathbf{" + s + r"}$"

                for (
                    ax, titulo, xmin, xmax, ymin, ymax,
                    xmajor, ymajor, xminor, yminor
                ) in limites:
                    if xmin >= xmax:
                        raise ValueError(f"{titulo}: X mínimo deve ser menor que X máximo.")
                    if ymin >= ymax:
                        raise ValueError(f"{titulo}: Y mínimo deve ser menor que Y máximo.")

                    if self.show_fermi.isChecked():
                        ax.axvline(
                            0.0,
                            color=self.cor_fermi,
                            linestyle="--",
                            linewidth=self.fermi_width.value()
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
                        ax.xaxis.set_major_formatter(FuncFormatter(fmt_num))
                        ax.yaxis.set_major_formatter(FuncFormatter(fmt_num))
                    else:
                        ax.xaxis.set_major_formatter(ScalarFormatter())
                        ax.yaxis.set_major_formatter(ScalarFormatter())

                    cfg = (
                        self.dos_up_visual if ax is ax_up
                        else self.dos_dn_visual
                    )
                    titulo_editavel = texto_latex_negrito(
                        cfg.titulo.text(),
                        self.bold_title.isChecked(),
                        self.latex_global.isChecked()
                    )
                    ax.set_title(
                        titulo_editavel if cfg.show_title.isChecked() else "",
                        fontsize=self.font_title.value(),
                        fontweight="bold" if self.bold_title.isChecked() else "normal"
                    )

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
                        axis="both", which="major",
                        labelsize=self.font_tick.value()
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
                                txt.set_fontweight(
                                    "bold" if self.bold_legend.isChecked() else "normal"
                                )

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

                self.plot.figure.subplots_adjust(
                    left=0.10, right=0.98, bottom=0.12,
                    top=0.86 if self.title_edit.text().strip() else 0.92,
                    wspace=self.dos_wspace.value()
                )
                self.plot.redraw(use_tight_layout=False)
                return

            # ------------------------------------------------
            # nspin=1: comportamento original
            # ------------------------------------------------
            self.plot.reset_axes()
            ax = self.plot.ax

            ax.plot(
                self.energia,
                self.dos_plot,
                color=self.cor_dos,
                linewidth=self.linewidth.value(),
                label=texto_latex_negrito(
                    "DOS", self.bold_legend.isChecked(),
                    self.latex_global.isChecked()
                )
            )

            if self.show_fermi.isChecked():
                label_fermi = r"$E_F$"
                if self.bold_legend.isChecked() and not self.latex_global.isChecked():
                    label_fermi = r"$\mathbf{E_F}$"

                ax.axvline(
                    0.0,
                    color=self.cor_fermi,
                    linestyle="--",
                    linewidth=self.fermi_width.value(),
                    label=label_fermi
                )

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

            if self.title_edit.text().strip():
                ax.set_title(
                    texto_latex_negrito(
                        self.title_edit.text(),
                        self.bold_title.isChecked(),
                        self.latex_global.isChecked()
                    ),
                    fontsize=self.font_title.value(),
                    fontweight="bold" if self.bold_title.isChecked() else "normal"
                )

            ax.tick_params(
                axis="both", which="major",
                labelsize=self.font_tick.value()
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
                        txt.set_fontweight(
                            "bold" if self.bold_legend.isChecked() else "normal"
                        )

            self.plot.redraw()

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))


    def salvar_figura(self):

        if self.energia is None:
            return

        nome, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar figura",
            "dos.pdf",
            "PDF (*.pdf);;PNG (*.png);;SVG (*.svg)"
        )

        if not nome:
            return

        tamanho_original = self.plot.figure.get_size_inches().copy()

        try:

            self.plot.figure.set_size_inches(
                self.fig_w.value(),
                self.fig_h.value(),
                forward=False
            )

            self.plot.figure.savefig(
                nome,
                dpi=self.dpi.value(),
                bbox_inches="tight"
            )

        finally:

            self.plot.figure.set_size_inches(
                tamanho_original[0],
                tamanho_original[1],
                forward=False
            )

            self.plot.canvas.draw()


