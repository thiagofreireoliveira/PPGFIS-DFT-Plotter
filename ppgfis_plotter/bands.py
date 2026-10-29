# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *
from .analysis import *
from .readers import *
from .exports import *
from .plotting import *
from .ui_helpers import *

class BandsPage(QWidget):

    def __init__(self, back_callback, parent=None):
        super().__init__(parent)

        self.back_callback = back_callback
        self.bandas = None
        self.bandas_up = None
        self.bandas_down = None
        self.spin_data = None
        self.normal_pdos_data = None
        self.energia_ref = 0.0
        self.tipo_ref = ""

        self.cor_bandas = "#000000"
        self.cor_bandas_up = "#1f77b4"
        self.cor_bandas_down = "#d62728"
        self.cor_fermi = "#d62728"
        self.cor_simetria = "#666666"

        # Cores editáveis das curvas no modo nspin=2.
        self.cores_orbitais_spin = {
            "s": "#1f77b4", "p": "#2ca02c",
            "d": "#ff7f0e", "f": "#9467bd"
        }
        self.cores_elementos_spin = {}
        self.botoes_cores_elementos_spin = {}

        root = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # Painel esquerdo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(360)

        panel = QWidget()
        self.form = QVBoxLayout(panel)
        self.form.setContentsMargins(8, 8, 8, 8)
        self.form.setSpacing(8)

        scroll.setWidget(panel)
        splitter.addWidget(scroll)

        # Pré-visualização permanente à direita
        preview_box = QGroupBox("Pré-visualização dos gráficos")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(6, 6, 6, 6)

        self.plot = PlotWidget()
        self.plot.style_controls = self
        self.plot.setMinimumWidth(650)
        self.plot.setMinimumHeight(520)
        self.corte_gap_painel_combinado = QCheckBox('Aplicar corte na lacuna da DOS/PDOS no painel combinado')
        self.corte_gap_painel_combinado.setChecked(False)
        self.corte_gap_painel_combinado.toggled.connect(self.atualizar_plot)
        preview_layout.addWidget(self.corte_gap_painel_combinado)
        preview_layout.addWidget(self.plot)

        splitter.addWidget(preview_box)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([390, 900])
        splitter.setCollapsible(1, False)

        instalar_barra_de_ferramentas(self, root, splitter, scroll)
        self._build_controls()
        self.mostrar_preview_inicial()

    def _build_controls(self):

        # Navegação
        nav = QHBoxLayout()

        voltar = QPushButton("← Início")
        voltar.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        voltar.setMinimumWidth(0)
        voltar.clicked.connect(self.back_callback)

        nav.addWidget(voltar)
        nav.addStretch()

        self.form.addLayout(nav)

        # Arquivos
        box = QGroupBox("Arquivos")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.spin_checkbox = QCheckBox(
            "Cálculo com polarização de spin (nspin = 2)"
        )
        self.spin_checkbox.stateChanged.connect(self.atualizar_modo_spin)
        form.addRow(self.spin_checkbox)

        self.scf_edit = QLineEdit("hBN2D.scf.out")
        self.band_edit = QLineEdit("hBN2D.band.gnu")
        self.band_up_edit = QLineEdit()
        self.band_down_edit = QLineEdit()
        self.pdos_tot_normal_edit = QLineEdit()
        self.orbitals_normal_edit = QLineEdit()
        self.pdos_tot_spin_edit = QLineEdit()
        self.orbitals_spin_edit = QLineEdit()

        # SCF comum aos dois modos
        self.scf_row = QWidget()
        rr = QHBoxLayout(self.scf_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.scf_edit)
        bb = QPushButton("Abrir")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(self.escolher_scf)
        rr.addWidget(bb)
        form.addRow("SCF:", self.scf_row)

        # -------- Modo sem polarizacao --------
        self.normal_band_label = QLabel("Bandas:")
        self.normal_band_row = QWidget()
        rr = QHBoxLayout(self.normal_band_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.band_edit)
        bb = QPushButton("Abrir")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(self.escolher_band)
        rr.addWidget(bb)
        form.addRow(self.normal_band_label, self.normal_band_row)

        # PDOS para o modo sem polarização de spin.
        self.normal_pdos_label = QLabel("PDOS total:")
        self.normal_pdos_row = QWidget()
        rr = QHBoxLayout(self.normal_pdos_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.pdos_tot_normal_edit)
        bb = QPushButton("Abrir")
        bb.clicked.connect(lambda: self.escolher_arquivo_para(
            self.pdos_tot_normal_edit, "Selecionar PDOS total (nspin=1)"))
        rr.addWidget(bb)
        form.addRow(self.normal_pdos_label, self.normal_pdos_row)

        self.normal_orbitals_label = QLabel("Pasta PDOS:")
        self.normal_orbitals_row = QWidget()
        rr = QHBoxLayout(self.normal_orbitals_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.orbitals_normal_edit)
        bb = QPushButton("Abrir pasta")
        bb.clicked.connect(lambda: self.escolher_pasta_para_normal())
        rr.addWidget(bb)
        form.addRow(self.normal_orbitals_label, self.normal_orbitals_row)

        # -------- Modo nspin=2 --------
        # Cada canal de spin possui seu proprio arquivo de estrutura de bandas.
        self.spin_widgets = []

        self.band_up_label = QLabel("Bandas UP:")
        self.band_up_row = QWidget()
        rr = QHBoxLayout(self.band_up_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.band_up_edit)
        bb = QPushButton("Abrir UP")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(
            lambda: self.escolher_arquivo_para(
                self.band_up_edit, "Selecionar arquivo de bandas UP"
            )
        )
        rr.addWidget(bb)
        form.addRow(self.band_up_label, self.band_up_row)
        self.spin_widgets += [self.band_up_label, self.band_up_row]

        self.band_down_label = QLabel("Bandas DOWN:")
        self.band_down_row = QWidget()
        rr = QHBoxLayout(self.band_down_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.band_down_edit)
        bb = QPushButton("Abrir DOWN")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(
            lambda: self.escolher_arquivo_para(
                self.band_down_edit, "Selecionar arquivo de bandas DOWN"
            )
        )
        rr.addWidget(bb)
        form.addRow(self.band_down_label, self.band_down_row)
        self.spin_widgets += [self.band_down_label, self.band_down_row]

        self.pdos_tot_spin_label = QLabel("PDOS total:")
        self.pdos_tot_spin_row = QWidget()
        rr = QHBoxLayout(self.pdos_tot_spin_row)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.pdos_tot_spin_edit)
        bb = QPushButton("Abrir")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(
            lambda: self.escolher_arquivo_para(
                self.pdos_tot_spin_edit, "Selecionar PDOS total (UP/DOWN)"
            )
        )
        rr.addWidget(bb)
        form.addRow(self.pdos_tot_spin_label, self.pdos_tot_spin_row)
        self.spin_widgets += [self.pdos_tot_spin_label, self.pdos_tot_spin_row]

        self.spin_orb_label = QLabel("Pasta PDOS:")
        self.spin_orb_widget = QWidget()
        rr = QHBoxLayout(self.spin_orb_widget)
        rr.setContentsMargins(0, 0, 0, 0)
        rr.addWidget(self.orbitals_spin_edit)
        bb = QPushButton("Abrir pasta")
        bb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        bb.setMinimumWidth(0)
        bb.clicked.connect(self.escolher_pasta_spin)
        rr.addWidget(bb)
        form.addRow(self.spin_orb_label, self.spin_orb_widget)
        self.spin_widgets += [self.spin_orb_label, self.spin_orb_widget]

        btn_load = QPushButton("Carregar dados")
        btn_load.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn_load.setMinimumWidth(0)
        btn_load.clicked.connect(self.carregar_dados)
        form.addRow(btn_load)


        self.form.addWidget(box)

        # Alta simetria
        box = QGroupBox("Caminho de alta simetria")
        v = QVBoxLayout(box)

        self.rotulos_edit = QLineEdit("G,M,K,G")
        v.addWidget(QLabel("Rótulos (ex.: G,M,K,G)"))
        v.addWidget(self.rotulos_edit)

        link = QPushButton("Consultar pontos de alta simetria (Brillouin zone)")
        link.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        link.setMinimumWidth(0)
        link.setFlat(True)
        link.setCursor(Qt.PointingHandCursor)
        link.clicked.connect(lambda: abrir_link(BRILLOUIN_URL))
        v.addWidget(link)

        self.form.addWidget(box)

        # Eixos
        box = QGroupBox("Eixos e rótulos")
        self.bands_axes_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.title_edit = QLineEdit()
        self.xlabel_edit = QLineEdit()
        self.ylabel_edit = QLineEdit(r"$E-E_F$ (eV)")

        form.addRow("Título:", self.title_edit)
        form.addRow("Eixo X:", self.xlabel_edit)
        form.addRow("Eixo Y:", self.ylabel_edit)

        self.ymin = self.dspin(-50, 50, -8, 0.5)
        self.ymax = self.dspin(-50, 50, 8, 0.5)
        self.ymajor = self.dspin(0.1, 50, 2, 0.5)

        form.addRow("Y mínimo:", self.ymin)
        form.addRow("Y máximo:", self.ymax)
        form.addRow("Incremento Y:", self.ymajor)

        # Limites horizontais das densidades (colunas 2 e 3).
        # São independentes para PDOS por elemento e por orbital.
        self.elem_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.elem_xmax = self.dspin(-100000, 100000, 10, 0.5)
        self.elem_xmajor = self.dspin(0.01, 100000, 2, 0.5)

        self.orb_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.orb_xmax = self.dspin(-100000, 100000, 10, 0.5)
        self.orb_xmajor = self.dspin(0.01, 100000, 2, 0.5)

        # Limites Y independentes para cada tipo de PDOS.
        self.elem_ymin = self.dspin(-50, 50, -8, 0.5)
        self.elem_ymax = self.dspin(-50, 50, 8, 0.5)
        self.elem_ymajor = self.dspin(0.1, 50, 2, 0.5)

        self.orb_ymin = self.dspin(-50, 50, -8, 0.5)
        self.orb_ymax = self.dspin(-50, 50, 8, 0.5)
        self.orb_ymajor = self.dspin(0.1, 50, 2, 0.5)

        # Limites horizontais independentes para UP e DOWN.
        # Isso é necessário porque as intensidades físicas dos dois canais
        # podem ser muito diferentes (especialmente estados 4f).
        self.elem_up_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.elem_up_xmax = self.dspin(-100000, 100000, 40, 0.5)
        self.elem_dn_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.elem_dn_xmax = self.dspin(-100000, 100000, 40, 0.5)

        self.orb_up_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.orb_up_xmax = self.dspin(-100000, 100000, 40, 0.5)
        self.orb_dn_xmin = self.dspin(-100000, 100000, 0, 0.5)
        self.orb_dn_xmax = self.dspin(-100000, 100000, 40, 0.5)

        form.addRow("Elemento UP - X mínimo:", self.elem_up_xmin)
        form.addRow("Elemento UP - X máximo:", self.elem_up_xmax)
        form.addRow("Elemento DOWN - X mínimo:", self.elem_dn_xmin)
        form.addRow("Elemento DOWN - X máximo:", self.elem_dn_xmax)

        form.addRow("Orbital UP - X mínimo:", self.orb_up_xmin)
        form.addRow("Orbital UP - X máximo:", self.orb_up_xmax)
        form.addRow("Orbital DOWN - X mínimo:", self.orb_dn_xmin)
        form.addRow("Orbital DOWN - X máximo:", self.orb_dn_xmax)

        form.addRow("Elemento X mínimo:", self.elem_xmin)
        form.addRow("Elemento X máximo:", self.elem_xmax)
        form.addRow("Elemento incremento X:", self.elem_xmajor)
        form.addRow("Elemento Y mínimo:", self.elem_ymin)
        form.addRow("Elemento Y máximo:", self.elem_ymax)
        form.addRow("Elemento incremento Y:", self.elem_ymajor)

        form.addRow("Orbital X mínimo:", self.orb_xmin)
        form.addRow("Orbital X máximo:", self.orb_xmax)
        form.addRow("Orbital incremento X:", self.orb_xmajor)
        form.addRow("Orbital Y mínimo:", self.orb_ymin)
        form.addRow("Orbital Y máximo:", self.orb_ymax)
        form.addRow("Orbital incremento Y:", self.orb_ymajor)

        # Rótulos X independentes apenas para os gráficos PDOS no modo nspin=2.
        self.elem_xlabel_edit = QLineEdit("PDOS (states/eV)")
        self.orb_xlabel_edit = QLineEdit("PDOS (states/eV)")
        self.elem_xlabel_edit.editingFinished.connect(self.atualizar_plot)
        self.orb_xlabel_edit.editingFinished.connect(self.atualizar_plot)

        form.addRow("Rótulo X - PDOS elemento:", self.elem_xlabel_edit)
        form.addRow("Rótulo X - PDOS orbital:", self.orb_xlabel_edit)

        # Espaçamento entre os seis painéis da matriz nspin=2.
        self.spin_wspace = self.dspin(0.0, 2.0, 0.30, 0.05)
        self.spin_hspace = self.dspin(0.0, 2.0, 0.35, 0.05)
        form.addRow("Espaçamento horizontal:", self.spin_wspace)
        form.addRow("Espaçamento vertical:", self.spin_hspace)

        self.bands_spin_axis_widgets = [
            self.elem_up_xmin, self.elem_up_xmax,
            self.elem_dn_xmin, self.elem_dn_xmax,
            self.orb_up_xmin, self.orb_up_xmax,
            self.orb_dn_xmin, self.orb_dn_xmax,
            self.elem_xmin, self.elem_xmax, self.elem_xmajor,
            self.elem_ymin, self.elem_ymax, self.elem_ymajor,
            self.orb_xmin, self.orb_xmax, self.orb_xmajor,
            self.orb_ymin, self.orb_ymax, self.orb_ymajor,
            self.elem_xlabel_edit, self.orb_xlabel_edit,
            self.spin_wspace, self.spin_hspace,
        ]

        self.form.addWidget(box)

        # Fontes
        box = QGroupBox("Fontes")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.font_axis = self.ispin(6, 40, 14)
        self.font_tick = self.ispin(6, 40, 12)
        self.font_title = self.ispin(6, 40, 14)

        form.addRow("Fonte eixos:", self.font_axis)
        form.addRow("Tamanho números/ticks:", self.font_tick)
        form.addRow("Fonte título:", self.font_title)

        nota_ticks = QLabel(
            "Use 'Tamanho números/ticks' para aumentar ou diminuir "
            "os valores numéricos dos eixos e os rótulos Γ, M, K..."
        )
        nota_ticks.setWordWrap(True)
        nota_ticks.setStyleSheet("color: #666666; font-size: 9pt;")
        form.addRow(nota_ticks)

        self.bold_title = QCheckBox("Título em negrito")
        self.bold_axis = QCheckBox("Rótulos em negrito")
        self.bold_ticks = QCheckBox("Números/ticks em negrito")
        self.bold_legend = QCheckBox("Legenda em negrito")

        for w in (self.bold_title, self.bold_axis, self.bold_ticks, self.bold_legend):
            w.stateChanged.connect(self.atualizar_plot)
            form.addRow(w)

        self.form.addWidget(box)

        # LaTeX
        box = QGroupBox("LaTeX")
        v = QVBoxLayout(box)

        self.latex_global = QCheckBox("Usar LaTeX / mhchem em toda a figura")
        self.latex_global.stateChanged.connect(self.atualizar_plot)
        v.addWidget(self.latex_global)

        self.form.addWidget(box)

        # Aparência
        box = QGroupBox("Aparência")
        self.bands_appearance_box = box
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.btn_cor_bandas_normal = QPushButton("Cor das bandas (modo normal)")
        self.btn_cor_bandas_normal.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_bandas_normal.setMinimumWidth(0)
        self.btn_cor_bandas_normal.clicked.connect(self.escolher_cor_bandas)
        form.addRow(self.btn_cor_bandas_normal)

        self.btn_cor_band_up = QPushButton("Cor das bandas UP")
        self.btn_cor_band_up.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_band_up.setMinimumWidth(0)
        self.btn_cor_band_up.clicked.connect(self.escolher_cor_bandas_up)
        form.addRow(self.btn_cor_band_up)

        self.btn_cor_band_down = QPushButton("Cor das bandas DOWN")
        self.btn_cor_band_down.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.btn_cor_band_down.setMinimumWidth(0)
        self.btn_cor_band_down.clicked.connect(self.escolher_cor_bandas_down)
        form.addRow(self.btn_cor_band_down)

        self.orbital_color_buttons = {}
        for orbital in ("s", "p", "d", "f"):
            b_orb = QPushButton(f"Cor orbital {orbital}")
            b_orb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            b_orb.setMinimumWidth(0)
            b_orb.setProperty("orbital", orbital)
            b_orb.clicked.connect(self.escolher_cor_orbital_botao)
            form.addRow(b_orb)
            self.orbital_color_buttons[orbital] = b_orb

        self.element_colors_box = QGroupBox("Cores dos elementos (nspin=2)")
        self.element_colors_layout = QFormLayout(self.element_colors_box)
        self.element_colors_layout.addRow(
            QLabel("Disponível após carregar os arquivos PDOS.")
        )
        self.form.addWidget(self.element_colors_box)

        # Visibilidade independente dos seis painéis do modo nspin=2
        self.panel_visibility_box = QGroupBox(
            "Visibilidade por gráfico (nspin=2)"
        )
        pv = QVBoxLayout(self.panel_visibility_box)
        nota = QLabel(
            "Escolha, para cada painel, se deseja mostrar título, "
            "legenda, ticks, números dos ticks e rótulos dos eixos."
        )
        nota.setWordWrap(True)
        pv.addWidget(nota)

        self.panel_visibility = {}
        nomes_paineis = (
            ("band_up", "Bandas UP"),
            ("elem_up", "PDOS elemento UP"),
            ("orb_up", "PDOS orbital UP"),
            ("band_down", "Bandas DOWN"),
            ("elem_down", "PDOS elemento DOWN"),
            ("orb_down", "PDOS orbital DOWN"),
        )

        for chave, nome in nomes_paineis:
            gb = QGroupBox(nome)
            grid = QGridLayout(gb)

            controles = {}
            opcoes = (
                ("title", "Título"),
                ("legend", "Legenda"),
                ("xticks", "Ticks X"),
                ("yticks", "Ticks Y"),
                ("xticklabels", "Números/rótulos X"),
                ("yticklabels", "Números/rótulos Y"),
                ("xlabel", "Rótulo eixo X"),
                ("ylabel", "Rótulo eixo Y"),
            )
            for i, (opt, texto_opt) in enumerate(opcoes):
                cb = QCheckBox(texto_opt)
                cb.setChecked(True)
                # stateChanged envia um argumento inteiro. Usamos lambda para
                # chamar atualizar_plot() sem repassar esse argumento.
                cb.stateChanged.connect(
                    lambda _state, self=self: self.atualizar_plot()
                )
                grid.addWidget(cb, i // 2, i % 2)
                controles[opt] = cb

            self.panel_visibility[chave] = controles
            pv.addWidget(gb)

        self.form.addWidget(self.panel_visibility_box)

        btn = QPushButton("Cor de EF")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_cor_fermi)
        form.addRow(btn)
        self._dos_botoes_estilo_extra = [btn]

        btn = QPushButton("Cor das divisões")
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.clicked.connect(self.escolher_cor_simetria)
        form.addRow(btn)

        self.band_width = self.dspin(0.1, 10, 0.8, 0.1)
        self.fermi_width = self.dspin(0.1, 10, 1.0, 0.1)
        self.sym_width = self.dspin(0.1, 10, 0.7, 0.1)

        form.addRow("Espessura bandas:", self.band_width)
        form.addRow("Espessura EF:", self.fermi_width)
        form.addRow("Espessura divisões:", self.sym_width)

        self.show_fermi = QCheckBox("Mostrar EF")
        self.show_fermi.setChecked(True)
        self.show_sym = QCheckBox("Mostrar divisões")
        self.show_sym.setChecked(True)
        self.show_grid = QCheckBox("Mostrar grade")
        self.show_legend = QCheckBox("Mostrar legenda")
        self.show_legend.setChecked(True)
        self.legend_frame = QCheckBox("Exibir moldura da legenda")
        self.legend_frame.setChecked(True)

        for w in (
            self.show_fermi, self.show_sym, self.show_grid,
            self.show_legend, self.legend_frame
        ):
            w.stateChanged.connect(
                lambda _state, self=self: self.atualizar_plot()
            )
            form.addRow(w)

        self.form.addWidget(box)

        # Figura
        box = QGroupBox("Figura")
        form = QFormLayout(box)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.fig_w = self.dspin(3, 20, 7, 0.5)
        self.fig_h = self.dspin(3, 20, 6, 0.5)
        self.dpi = self.ispin(72, 1200, 300)

        form.addRow("Largura:", self.fig_w)
        form.addRow("Altura:", self.fig_h)
        form.addRow("DPI:", self.dpi)

        self.form.addWidget(box)

        # Ações
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

        self.status = QLabel("Carregue os arquivos.")
        self.status.setWordWrap(True)
        self.form.addWidget(self.status)

        # Reaplica o estado do checkbox agora que todos os controles existem.
        self.form.addStretch()

        # Inicializa a visibilidade somente após criar todos os controles.
        self.atualizar_modo_spin()

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

    def escolher_scf(self):
        nome, _ = QFileDialog.getOpenFileName(self, "Arquivo SCF")

        if nome:
            self.scf_edit.setText(nome)

    def escolher_band(self):
        nome, _ = QFileDialog.getOpenFileName(self, "Arquivo .band.gnu")

        if nome:
            self.band_edit.setText(nome)

    def mostrar_preview_inicial(self):
        """Prévia estrutural com eixos/ticks no mesmo padrão Matplotlib."""
        if self.spin_checkbox.isChecked():
            axes = self.plot.reset_spin_axes()
            titulos = (
                ("Bandas UP", "PDOS por elemento UP", "PDOS por orbital UP"),
                ("Bandas DOWN", "PDOS por elemento DOWN", "PDOS por orbital DOWN"),
            )
            for i in range(2):
                for j in range(3):
                    ax = axes[i, j]
                    ax.set_title(titulos[i][j], fontsize=10)
                    ax.set_ylim(-8, 8)
                    ax.yaxis.set_major_locator(MultipleLocator(2))
                    ax.tick_params(direction="in", bottom=True, left=True, top=False, right=False, labelsize=8)
                    for spine in ax.spines.values():
                        spine.set_visible(True)
                    if j == 0:
                        ax.set_ylabel(r"$E-E_F$ (eV)")
                        ax.set_xticks([0, 1, 2, 3])
                        ax.set_xticklabels([r"$\Gamma$", "M", "K", r"$\Gamma$"])
                        ax.set_xlim(0, 3)
                    else:
                        if j == 1 and hasattr(self, "elem_xlabel_edit"):
                            ax.set_xlabel(texto_latex_negrito(self.elem_xlabel_edit.text(), self.bold_axis.isChecked(), self.latex_global.isChecked()))
                        elif j == 2 and hasattr(self, "orb_xlabel_edit"):
                            ax.set_xlabel(texto_latex_negrito(self.orb_xlabel_edit.text(), self.bold_axis.isChecked(), self.latex_global.isChecked()))
                        else:
                            ax.set_xlabel("PDOS (states/eV)")
                        ax.set_xlim(0, 1)
                    if j == 0:
                        cor_preview = self.cor_bandas_up if i == 0 else self.cor_bandas_down
                        # Linha ilustrativa para que a cor selecionada seja visível
                        # mesmo antes de carregar os dados reais.
                        ax.plot([0, 1, 2, 3], [-2, -1, 1, 2],
                                color=cor_preview, linewidth=1.2)
                    ax.axhline(0, color=self.cor_fermi, linestyle="--", linewidth=0.8)
            self.plot.figure.subplots_adjust(
                left=0.09, right=0.98, bottom=0.10, top=0.96,
                wspace=self.spin_wspace.value() if hasattr(self, "spin_wspace") else 0.30,
                hspace=self.spin_hspace.value() if hasattr(self, "spin_hspace") else 0.35
            )
            self.plot.redraw(use_tight_layout=False)
        else:
            ax = self.plot.set_single_mode()
            ax.clear()
            ax.set_title("Estrutura de bandas")
            ax.set_ylabel(r"$E-E_F$ (eV)")
            ax.set_ylim(-8, 8)
            ax.yaxis.set_major_locator(MultipleLocator(2))
            ax.set_xlim(0, 3)
            ax.set_xticks([0, 1, 2, 3])
            ax.set_xticklabels([r"$\Gamma$", "M", "K", r"$\Gamma$"])
            ax.tick_params(direction="in", bottom=True, left=True, top=False, right=False)
            for spine in ax.spines.values():
                spine.set_visible(True)
            ax.plot([0, 1, 2, 3], [-2, -1, 1, 2],
                    color=self.cor_bandas, linewidth=1.2)
            ax.axhline(0, color=self.cor_fermi, linestyle="--", linewidth=0.8)
            self.plot.figure.tight_layout()
            self.plot.redraw()

    def escolher_arquivo_para(self, edit, titulo):
        nome, _ = QFileDialog.getOpenFileName(self, titulo)
        if nome:
            edit.setText(nome)

    def escolher_pasta_spin(self):
        pasta = QFileDialog.getExistingDirectory(
            self, "Pasta contendo os arquivos PDOS do projwfc.x"
        )
        if pasta:
            self.orbitals_spin_edit.setText(pasta)

    def escolher_pasta_para_normal(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar pasta dos arquivos PDOS")
        if pasta:
            self.orbitals_normal_edit.setText(pasta)

    def atualizar_modo_spin(self):
        spin = bool(self.spin_checkbox.isChecked())

        # Arquivos adequados ao modo selecionado.
        self.normal_band_label.setVisible(not spin)
        self.normal_band_row.setVisible(not spin)
        for w in (self.normal_pdos_label, self.normal_pdos_row,
                  self.normal_orbitals_label, self.normal_orbitals_row):
            w.setVisible(not spin)
        for w in self.spin_widgets:
            w.setVisible(spin)

        # Controles adicionais da matriz 2x3 são exclusivos de nspin=2.
        axes_form = self.bands_axes_box.layout()
        for widget in self.bands_spin_axis_widgets:
            widget.setVisible(spin)
            label = axes_form.labelForField(widget)
            if label is not None:
                label.setVisible(spin)

        # Aparência específica do modo.
        # Cores, espessuras e padrões são editados em um único local:
        # botão "Editor de curvas" na área de pré-visualização.
        # Evita controles duplicados ou UP/DOWN no modo nspin=1.
        for widget in (self.btn_cor_bandas_normal, self.btn_cor_band_up,
                       self.btn_cor_band_down, *self.orbital_color_buttons.values(),
                       self.band_width, self.fermi_width, self.sym_width):
            widget.setVisible(False)
            label = self.bands_appearance_box.layout().labelForField(widget)
            if label is not None:
                label.setVisible(False)

        self.panel_visibility_box.setVisible(spin)
        self.element_colors_box.setVisible(False)

        # Os estilos antigos não podem migrar entre modos cujos painéis
        # e índices de curvas são diferentes.
        if getattr(self, '_ultimo_modo_editor', None) != spin:
            self.plot._estilos_personalizados.clear()
            self._ultimo_modo_editor = spin

        self.mostrar_preview_inicial()

    def escolher_cor_bandas(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cor_bandas = c.name()
            self.atualizar_plot()

    def escolher_cor_bandas_up(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cor_bandas_up = c.name()
            self.atualizar_plot()

    def escolher_cor_bandas_down(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cor_bandas_down = c.name()
            self.atualizar_plot()

    def escolher_cor_fermi(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cor_fermi = c.name()
            self.atualizar_plot()

    def escolher_cor_simetria(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cor_simetria = c.name()
            self.atualizar_plot()

    def escolher_cor_orbital_botao(self):
        botao = self.sender()
        if botao is None:
            return
        orbital = botao.property("orbital")
        if orbital not in self.cores_orbitais_spin:
            return

        c = QColorDialog.getColor()
        if c.isValid():
            self.cores_orbitais_spin[orbital] = c.name()
            self.atualizar_plot()

    def escolher_cor_elemento_botao(self):
        botao = self.sender()
        if botao is None:
            return

        elemento = botao.property("elemento")
        if not elemento:
            return

        c = QColorDialog.getColor()
        if c.isValid():
            self.cores_elementos_spin[elemento] = c.name()
            self.atualizar_plot()

    def atualizar_controles_cores_elementos(self, elementos):
        # Limpa os controles antigos.
        while self.element_colors_layout.rowCount():
            self.element_colors_layout.removeRow(0)

        paleta = ["#17becf", "#8c564b", "#e377c2", "#7f7f7f",
                  "#bcbd22", "#aec7e8", "#ff9896", "#98df8a",
                  "#c5b0d5", "#c49c94"]
        self.botoes_cores_elementos_spin = {}
        for i, elemento in enumerate(sorted(elementos)):
            self.cores_elementos_spin.setdefault(elemento, paleta[i % len(paleta)])
            b = QPushButton(f"Cor de {elemento}")
            b.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            b.setMinimumWidth(0)
            b.setProperty("elemento", elemento)
            b.clicked.connect(self.escolher_cor_elemento_botao)
            self.element_colors_layout.addRow(elemento, b)
            self.botoes_cores_elementos_spin[elemento] = b

    def carregar_dados(self):
        try:
            self.energia_ref, self.tipo_ref = ler_energia_referencia_scf(
                self.scf_edit.text()
            )

            if not self.spin_checkbox.isChecked():
                self.bandas = ler_bandas(self.band_edit.text())
                self.bandas_up = self.bandas_down = None
                self.spin_data = None
                self.normal_pdos_data = None
                arquivo_total = self.pdos_tot_normal_edit.text().strip()
                pasta_pdos = self.orbitals_normal_edit.text().strip()
                if arquivo_total and pasta_pdos:
                    energia, pdos_total, orbitais, usados_orb = (
                        somar_pdos_por_orbital(arquivo_total, pasta_pdos, self.energia_ref)
                    )
                    elementos, usados_el = somar_pdos_por_elemento(energia, pasta_pdos)
                    self.normal_pdos_data = {
                        "energia": energia, "pdos_total": pdos_total,
                        "orbitais": orbitais, "elementos": elementos,
                        "usados_orb": usados_orb, "usados_el": usados_el,
                    }
                    self.atualizar_controles_cores_elementos(elementos.keys())
                elif arquivo_total or pasta_pdos:
                    raise ValueError("Para o gráfico conjunto nspin=1, informe tanto o PDOS total quanto a pasta PDOS.")
                self.status.setText(
                    f"{len(self.bandas)} bandas | "
                    f"{len(self.bandas[0])} pontos | "
                    f"{self.tipo_ref}: {self.energia_ref:.6f} eV"
                )
            else:
                try:
                    self.bandas_up = ler_bandas(self.band_up_edit.text())
                except Exception as e:
                    raise ValueError(f"Erro ao ler BANDAS UP:\n{e}") from e

                try:
                    self.bandas_down = ler_bandas(self.band_down_edit.text())
                except Exception as e:
                    raise ValueError(f"Erro ao ler BANDAS DOWN:\n{e}") from e

                try:
                    (
                        eabs,
                        dos_up, dos_dn,
                        pdos_total_up, pdos_total_dn
                    ) = ler_pdos_tot_spin(
                        self.pdos_tot_spin_edit.text()
                    )
                except Exception as e:
                    raise ValueError(f"Erro ao ler PDOS TOTAL:\n{e}") from e
                energia = eabs - self.energia_ref
                orb_up, orb_dn, el_up, el_dn, usados_orb, usados_el = (
                    somar_pdos_spin(self.orbitals_spin_edit.text(), eabs)
                )
                # Mesma validação usada na aba PDOS corrigida:
                # a soma dos WFCs deve reconstruir PDOSup/PDOSdown do pdos_tot.
                reconstruido_up = np.zeros_like(pdos_total_up)
                reconstruido_dn = np.zeros_like(pdos_total_dn)
                for orbital in ("s", "p", "d", "f"):
                    reconstruido_up += orb_up[orbital]
                    reconstruido_dn += orb_dn[orbital]

                erro_pdos_up = float(np.max(np.abs(reconstruido_up - pdos_total_up)))
                erro_pdos_dn = float(np.max(np.abs(reconstruido_dn - pdos_total_dn)))

                self.spin_data = {
                    "energia": energia,
                    "dos_up": dos_up, "dos_dn": dos_dn,
                    "pdos_total_up": pdos_total_up,
                    "pdos_total_dn": pdos_total_dn,
                    "orb_up": orb_up, "orb_dn": orb_dn,
                    "el_up": el_up, "el_dn": el_dn,
                    "usados_orb": usados_orb,
                    "usados_el": usados_el,
                }
                self.bandas = None
                self.atualizar_controles_cores_elementos(el_up.keys())
                self.status.setText(
                    f"nspin=2 | {len(self.bandas_up)} bandas UP | "
                    f"{len(self.bandas_down)} bandas DOWN | "
                    f"elementos: {', '.join(sorted(el_up)) or 'nenhum'} | "
                    f"erro soma WFC: UP={erro_pdos_up:.3g}, DOWN={erro_pdos_dn:.3g} | "
                    f"{self.tipo_ref}: {self.energia_ref:.6f} eV"
                )

            # -------------------------------------------------
            # VBM / CBM / GAP + CSV
            # -------------------------------------------------
            sistema = nome_sistema_de_arquivo(self.scf_edit.text())
            resultados_csv = []

            if self.spin_checkbox.isChecked():
                r_up = calcular_bordas_por_bandas(
                    self.bandas_up, self.energia_ref
                )
                r_down = calcular_bordas_por_bandas(
                    self.bandas_down, self.energia_ref
                )
                resultados_csv.extend([
                    ("UP", r_up),
                    ("DOWN", r_down),
                ])

                # Resultado global: considera os dois canais de spin juntos.
                r_total = calcular_bordas_por_bandas(
                    list(self.bandas_up) + list(self.bandas_down),
                    self.energia_ref
                )
                resultados_csv.append(("TOTAL", r_total))
            else:
                r_total = calcular_bordas_por_bandas(
                    self.bandas, self.energia_ref
                )
                resultados_csv.append(("TOTAL", r_total))

            caminho_csv = salvar_resultados_eletronicos_csv(
                self.scf_edit.text(),
                sistema,
                "BANDS",
                self.energia_ref,
                self.tipo_ref,
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

    def atualizar_plot(self):
        if self.spin_checkbox.isChecked():
            if self.bandas_up is None or self.bandas_down is None or self.spin_data is None:
                return
            try:
                self.atualizar_plot_spin()
            except Exception as erro:
                QMessageBox.critical(self, "Erro", str(erro))
            return

        if self.bandas is None:
            return
        if self.normal_pdos_data is not None:
            try:
                self.atualizar_plot_normal_com_pdos()
            except Exception as erro:
                QMessageBox.critical(self, "Erro", str(erro))
            return

        try:
            mpl.rcParams["text.usetex"] = bool(self.latex_global.isChecked())

            if self.latex_global.isChecked():
                mpl.rcParams["text.latex.preamble"] = (
                    r"\usepackage[version=4]{mhchem}"
                    r"\usepackage{amsmath}"
                    r"\usepackage{bm}"
                )

            rotulos = converter_rotulos(self.rotulos_edit.text())
            k = self.bandas[0][:, 0]

            indices = np.linspace(
                0,
                len(k) - 1,
                len(rotulos)
            ).round().astype(int)

            k_sym = [k[i] for i in indices]

            self.plot.reset_axes()
            ax = self.plot.ax

            for banda in self.bandas:
                ax.plot(
                    banda[:, 0],
                    banda[:, 1] - self.energia_ref,
                    color=self.cor_bandas,
                    linewidth=self.band_width.value()
                )

            if self.show_fermi.isChecked():
                ax.axhline(
                    0.0,
                    color=self.cor_fermi,
                    linestyle="--",
                    linewidth=self.fermi_width.value(),
                    label=r"$E_F$"
                )

            if self.show_sym.isChecked():
                for x in k_sym:
                    ax.axvline(
                        x,
                        color=self.cor_simetria,
                        linewidth=self.sym_width.value()
                    )

            ax.set_xlim(k_sym[0], k_sym[-1])
            ax.set_ylim(self.ymin.value(), self.ymax.value())

            ax.set_xticks(k_sym)

            rotulos_plot = rotulos

            if self.bold_ticks.isChecked() and not self.latex_global.isChecked():
                rotulos_plot = [negrito_mathtext(r) for r in rotulos]

            ax.set_xticklabels(
                rotulos_plot,
                fontsize=self.font_tick.value()
            )

            ax.yaxis.set_major_locator(
                MultipleLocator(self.ymajor.value())
            )

            if self.bold_ticks.isChecked() and self.latex_global.isChecked():
                def fmt(v, pos):
                    if abs(v) < 1e-12:
                        v = 0.0

                    s = str(int(round(v))) if abs(v-round(v)) < 1e-10 else f"{v:g}"
                    return r"$\mathbf{" + s + r"}$"

                ax.yaxis.set_major_formatter(FuncFormatter(fmt))
            else:
                ax.yaxis.set_major_formatter(ScalarFormatter())

            # ------------------------------------------------
            # TAMANHO DOS NÚMEROS / TICKS
            # ------------------------------------------------
            # Aplicamos diretamente aos objetos Text depois que
            # locators e formatters já criaram os ticks.
            tamanho_ticks = self.font_tick.value()

            ax.tick_params(
                axis="both",
                which="major",
                labelsize=tamanho_ticks
            )

            for label in ax.get_xticklabels():
                label.set_fontsize(tamanho_ticks)
                label.set_fontweight(
                    "bold" if self.bold_ticks.isChecked() else "normal"
                )

            for label in ax.get_yticklabels():
                label.set_fontsize(tamanho_ticks)
                label.set_fontweight(
                    "bold" if self.bold_ticks.isChecked() else "normal"
                )

            xlabel = self.xlabel_edit.text()
            ylabel = self.ylabel_edit.text()
            titulo = self.title_edit.text()

            if self.bold_axis.isChecked() and not self.latex_global.isChecked():
                xlabel = negrito_mathtext(xlabel)
                ylabel = negrito_mathtext(ylabel)

            if xlabel.strip():
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

            if titulo.strip():
                ax.set_title(
                    titulo,
                    fontsize=self.font_title.value(),
                    fontweight="bold" if self.bold_title.isChecked() else "normal"
                )

            if self.show_grid.isChecked():
                ax.grid(True, alpha=0.25)

            if self.show_legend.isChecked():
                handles, labels = ax.get_legend_handles_labels()

                if handles:
                    leg = ax.legend(
                        fontsize=self.font_tick.value(),
                        frameon=self.legend_frame.isChecked()
                    )

                    for txt in leg.get_texts():
                        txt.set_fontweight(
                            "bold" if self.bold_legend.isChecked() else "normal"
                        )

            self.plot.redraw()

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def aplicar_visibilidade_painel(self, ax, chave):
        """Aplica, de forma efetiva, a visibilidade escolhida para um painel."""
        cfg = self.panel_visibility[chave]

        # Título: esvaziar o texto evita que reapareça por efeitos de redraw/layout.
        if cfg["title"].isChecked():
            ax.title.set_visible(True)
        else:
            ax.title.set_visible(False)

        # Rótulos dos eixos.
        ax.xaxis.label.set_visible(cfg["xlabel"].isChecked())
        ax.yaxis.label.set_visible(cfg["ylabel"].isChecked())

        # Marcas dos ticks e textos dos ticks são tratados separadamente.
        mostrar_xticks = cfg["xticks"].isChecked()
        mostrar_yticks = cfg["yticks"].isChecked()
        mostrar_xlabels = cfg["xticklabels"].isChecked()
        mostrar_ylabels = cfg["yticklabels"].isChecked()

        ax.tick_params(
            axis="x", which="both",
            bottom=mostrar_xticks,
            top=False,
            labelbottom=mostrar_xlabels,
            labeltop=False,
        )
        ax.tick_params(
            axis="y", which="both",
            left=mostrar_yticks,
            right=False,
            labelleft=mostrar_ylabels,
            labelright=False,
        )

        # Reforço direto nos artistas Matplotlib já criados.
        for tick in ax.xaxis.get_major_ticks() + ax.xaxis.get_minor_ticks():
            tick.tick1line.set_visible(mostrar_xticks)
            tick.tick2line.set_visible(False)
            tick.label1.set_visible(mostrar_xlabels)
            tick.label2.set_visible(False)

        for tick in ax.yaxis.get_major_ticks() + ax.yaxis.get_minor_ticks():
            tick.tick1line.set_visible(mostrar_yticks)
            tick.tick2line.set_visible(False)
            tick.label1.set_visible(mostrar_ylabels)
            tick.label2.set_visible(False)

        # Legenda independente.
        leg = ax.get_legend()
        if leg is not None:
            leg.get_frame().set_visible(self.legend_frame.isChecked())
            if cfg["legend"].isChecked():
                leg.set_visible(True)
            else:
                leg.remove()

    def atualizar_plot_spin(self):
        """Matriz 2x3 com aparência Matplotlib completa e editável."""
        mpl.rcParams["text.usetex"] = bool(self.latex_global.isChecked())
        if self.latex_global.isChecked():
            mpl.rcParams["text.latex.preamble"] = (
                r"\usepackage[version=4]{mhchem}\usepackage{amsmath}"
            )

        # Igual ao módulo DOS: limpa os MESMOS Axes e redesenha.
        normal = not self.spin_checkbox.isChecked()
        axes = (self.plot.reset_bands_three_axes() if normal
                else self.plot.reset_spin_axes())

        # IMPORTANTE:
        # Não alterar figure.set_size_inches() durante a pré-visualização.
        # A aba DOS também não redimensiona a Figure a cada atualização.
        # O tamanho físico (largura/altura) será usado apenas na exportação.
        rotulos = converter_rotulos(self.rotulos_edit.text())
        dados = self.normal_pdos_data if normal else self.spin_data
        energia = dados["energia"]
        # O corte do painel combinado é opcional e nunca altera os dados originais.
        def _filtrar_dicionario(dicionario, intervalo):
            return {chave: corte_gap_bandas(energia, curva, intervalo)
                    for chave, curva in dicionario.items()}
        if normal and self.corte_gap_painel_combinado.isChecked():
            bordas = calcular_bordas_por_bandas(self.bandas, self.energia_ref)
            if bordas['tipo'] == 'com gap':
                lim = (bordas['vbm_rel'], bordas['cbm_rel'])
                dados = dict(dados)
                dados['pdos_total'] = corte_gap_bandas(energia, dados['pdos_total'], lim)
                dados['elementos'] = _filtrar_dicionario(dados['elementos'], lim)
                dados['orbitais'] = _filtrar_dicionario(dados['orbitais'], lim)
        elif self.corte_gap_painel_combinado.isChecked():
            dados = dict(dados)
            for sufixo, bandas in (('up', self.bandas_up), ('dn', self.bandas_down)):
                bordas = calcular_bordas_por_bandas(bandas, self.energia_ref)
                if bordas['tipo'] != 'com gap':
                    continue
                lim = (bordas['vbm_rel'], bordas['cbm_rel'])
                for chave in ('dos_' + sufixo, 'pdos_total_' + sufixo):
                    dados[chave] = corte_gap_bandas(energia, dados[chave], lim)
                dados['orb_' + sufixo] = _filtrar_dicionario(dados['orb_' + sufixo], lim)
                dados['el_' + sufixo] = _filtrar_dicionario(dados['el_' + sufixo], lim)

        canais = ((
            "TOTAL", self.bandas, dados["elementos"], dados["orbitais"],
            self.cor_bandas, ("band_up", "elem_up", "orb_up")
        ),) if normal else (
            ("UP", self.bandas_up, dados["el_up"],
             dados["orb_up"], self.cor_bandas_up,
             ("band_up", "elem_up", "orb_up")),
            ("DOWN", self.bandas_down, dados["el_dn"],
             dados["orb_dn"], self.cor_bandas_down,
             ("band_down", "elem_down", "orb_down")),
        )
        for linha, (spin, bandas, el, orb, cor_banda, chaves) in enumerate(canais):
            axb, axe, axo = (axes if normal else axes[linha, :])

            if spin == "UP":
                elem_xmin_spin = self.elem_up_xmin.value()
                elem_xmax_spin = self.elem_up_xmax.value()
                orb_xmin_spin = self.orb_up_xmin.value()
                orb_xmax_spin = self.orb_up_xmax.value()
            else:
                elem_xmin_spin = self.elem_dn_xmin.value()
                elem_xmax_spin = self.elem_dn_xmax.value()
                orb_xmin_spin = self.orb_dn_xmin.value()
                orb_xmax_spin = self.orb_dn_xmax.value()

            # -------- Bandas --------
            k = bandas[0][:, 0]
            idx = np.linspace(0, len(k)-1, len(rotulos)).round().astype(int)
            ksym = [k[i] for i in idx]
            for banda in bandas:
                axb.plot(
                    banda[:, 0], banda[:, 1] - self.energia_ref,
                    color=cor_banda, linewidth=self.band_width.value()
                )

            if self.show_fermi.isChecked():
                axb.axhline(
                    0, color=self.cor_fermi, linestyle="--",
                    linewidth=self.fermi_width.value()
                )
            if self.show_sym.isChecked():
                for x in ksym:
                    axb.axvline(
                        x, color=self.cor_simetria,
                        linewidth=self.sym_width.value()
                    )

            axb.set_xlim(ksym[0], ksym[-1])
            axb.set_xticks(ksym)
            axb.set_xticklabels(rotulos)
            axb.set_ylabel(self.ylabel_edit.text())
            axb.set_title(f"Bandas {spin}")

            # -------- PDOS por elemento --------
            pdos_total_spin = (dados["pdos_total"] if normal else
                (dados["pdos_total_up"] if spin == "UP" else dados["pdos_total_dn"]))
            axe.plot(
                pdos_total_spin, energia,
                label="PDOS total", color="#000000",
                linewidth=self.band_width.value()
            )
            for elemento in sorted(el):
                axe.plot(
                    el[elemento], energia, label=elemento,
                    color=self.cores_elementos_spin.get(elemento),
                    linewidth=self.band_width.value()
                )
            if self.show_fermi.isChecked():
                axe.axhline(
                    0, color=self.cor_fermi, linestyle="--",
                    linewidth=self.fermi_width.value()
                )
            axe.set_xlabel(texto_latex_negrito(self.elem_xlabel_edit.text(), self.bold_axis.isChecked(), self.latex_global.isChecked()))
            axe.set_title(f"PDOS por elemento {spin}")
            if elem_xmin_spin >= elem_xmax_spin:
                raise ValueError(
                    f"Em PDOS por elemento {spin}, X mínimo deve ser menor que X máximo."
                )
            axe.set_xlim(elem_xmin_spin, elem_xmax_spin)
            axe.xaxis.set_major_locator(MultipleLocator(self.elem_xmajor.value()))

            # -------- PDOS por orbital --------
            axo.plot(
                pdos_total_spin, energia,
                label="PDOS total", color="#000000",
                linewidth=self.band_width.value()
            )
            for orbital in ("s", "p", "d", "f"):
                if dados["usados_orb"].get(orbital, 0) > 0:
                    axo.plot(
                        orb[orbital], energia, label=orbital,
                        color=self.cores_orbitais_spin[orbital],
                        linewidth=self.band_width.value()
                    )
            if self.show_fermi.isChecked():
                axo.axhline(
                    0, color=self.cor_fermi, linestyle="--",
                    linewidth=self.fermi_width.value()
                )
            axo.set_xlabel(texto_latex_negrito(self.orb_xlabel_edit.text(), self.bold_axis.isChecked(), self.latex_global.isChecked()))
            axo.set_title(f"PDOS por orbital {spin}")
            if orb_xmin_spin >= orb_xmax_spin:
                raise ValueError(
                    f"Em PDOS por orbital {spin}, X mínimo deve ser menor que X máximo."
                )
            axo.set_xlim(orb_xmin_spin, orb_xmax_spin)
            axo.xaxis.set_major_locator(MultipleLocator(self.orb_xmajor.value()))

            # -------- Limites Y independentes --------
            if self.elem_ymin.value() >= self.elem_ymax.value():
                raise ValueError(
                    "Em PDOS por elemento, Y mínimo deve ser menor que Y máximo."
                )
            if self.orb_ymin.value() >= self.orb_ymax.value():
                raise ValueError(
                    "Em PDOS por orbital, Y mínimo deve ser menor que Y máximo."
                )

            # Bandas usam os limites Y gerais.
            axb.set_ylim(self.ymin.value(), self.ymax.value())
            axb.yaxis.set_major_locator(MultipleLocator(self.ymajor.value()))

            # PDOS por elemento usa seus próprios limites Y.
            axe.set_ylim(self.elem_ymin.value(), self.elem_ymax.value())
            axe.yaxis.set_major_locator(MultipleLocator(self.elem_ymajor.value()))

            # PDOS por orbital usa seus próprios limites Y.
            axo.set_ylim(self.orb_ymin.value(), self.orb_ymax.value())
            axo.yaxis.set_major_locator(MultipleLocator(self.orb_ymajor.value()))

            # -------- Aparência comum: ticks/spines/grid --------
            for ax in (axb, axe, axo):
                ax.tick_params(
                    axis="both", which="major",
                    direction="in", bottom=True, left=True, top=False, right=False,
                    labelsize=self.font_tick.value()
                )
                for label in ax.get_xticklabels() + ax.get_yticklabels():
                    label.set_fontweight(
                        "bold" if self.bold_ticks.isChecked() else "normal"
                    )
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_linewidth(1.0)
                if self.show_grid.isChecked():
                    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)
                else:
                    ax.grid(False)

                ax.xaxis.label.set_fontsize(self.font_axis.value())
                ax.yaxis.label.set_fontsize(self.font_axis.value())
                ax.xaxis.label.set_fontweight(
                    "bold" if self.bold_axis.isChecked() else "normal"
                )
                ax.yaxis.label.set_fontweight(
                    "bold" if self.bold_axis.isChecked() else "normal"
                )
                ax.title.set_fontsize(self.font_title.value())
                ax.title.set_fontweight(
                    "bold" if self.bold_title.isChecked() else "normal"
                )

            if self.show_legend.isChecked():
                if el:
                    leg = axe.legend(
                        fontsize=max(6, self.font_tick.value()-2),
                        frameon=self.legend_frame.isChecked()
                    )
                    if self.bold_legend.isChecked():
                        for t in leg.get_texts():
                            t.set_fontweight("bold")
                if any(dados["usados_orb"].values()):
                    leg = axo.legend(
                        fontsize=max(6, self.font_tick.value()-2),
                        frameon=self.legend_frame.isChecked()
                    )
                    if self.bold_legend.isChecked():
                        for t in leg.get_texts():
                            t.set_fontweight("bold")

            # Controle independente para cada um dos três gráficos desta linha.
            self.aplicar_visibilidade_painel(axb, chaves[0])
            self.aplicar_visibilidade_painel(axe, chaves[1])
            self.aplicar_visibilidade_painel(axo, chaves[2])

        titulo = texto_latex_negrito(self.title_edit.text().strip(), self.bold_title.isChecked(), self.latex_global.isChecked())
        if titulo:
            self.plot.figure.suptitle(
                titulo,
                fontsize=self.font_title.value(),
                fontweight="bold" if self.bold_title.isChecked() else "normal"
            )

        # Não usar tight_layout aqui: ele recalcula automaticamente as
        # distâncias e pode anular o espaçamento escolhido pelo usuário.
        top = 0.92 if titulo else 0.96
        self.plot.figure.subplots_adjust(
            left=0.09,
            right=0.98,
            bottom=0.10,
            top=top,
            wspace=self.spin_wspace.value(),
            hspace=self.spin_hspace.value()
        )
        self.plot.redraw(use_tight_layout=False)

    def atualizar_plot_normal_com_pdos(self):
        """Aplica os mesmos controles do modo spin à matriz 1x3."""
        self.atualizar_plot_spin()

    def salvar_figura(self):
        if self.spin_checkbox.isChecked():
            if self.bandas_up is None or self.bandas_down is None:
                return
        elif self.bandas is None:
            return

        nome, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar figura",
            "band_structure.pdf",
            "PDF (*.pdf);;PNG (*.png);;SVG (*.svg)"
        )

        if nome:
            tamanho_original = self.plot.figure.get_size_inches().copy()

            try:
                # Largura/altura escolhidas pelo usuário são usadas
                # apenas no arquivo exportado.
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
                # Restaura o tamanho da prévia sem alterar o widget Qt.
                self.plot.figure.set_size_inches(
                    tamanho_original[0],
                    tamanho_original[1],
                    forward=False
                )
                self.plot.canvas.draw()


