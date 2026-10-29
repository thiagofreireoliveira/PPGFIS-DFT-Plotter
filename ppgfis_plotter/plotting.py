# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

def converter_rotulos(texto: str):
    resultado = []

    for item in texto.split(","):
        item = item.strip()

        if item.upper() in ("G", "GAMMA", "Γ"):
            resultado.append(r"$\Gamma$")
        else:
            resultado.append(item)

    return resultado


def negrito_mathtext(texto: str):
    def substituir(match):
        conteudo = match.group(1).strip()

        if conteudo.startswith((r"\mathbf{", r"\boldsymbol{")):
            return f"${conteudo}$"

        return r"$\mathbf{" + conteudo + "}$"

    return re.sub(r"\$(.*?)\$", substituir, texto)


def texto_latex_negrito(texto, negrito=False, usar_latex=False):
    """
    Mantém o texto original quando LaTeX está desligado.
    Com usetex=True, fontweight do Matplotlib nem sempre é obedecido;
    por isso o negrito é aplicado dentro do próprio texto TeX.
    """
    texto = str(texto)
    if usar_latex and negrito and texto:
        return r"{\bfseries\boldmath " + texto + "}"
    return texto


class PlotWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.set_facecolor(mpl.rcParams["figure.facecolor"])
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.axes_grid = None

        # Personalização universal: funciona para bandas, DOS, PDOS e spin.
        # A identificação (índice do painel, índice da curva) permanece estável
        # enquanto o tipo de gráfico e a ordem das curvas forem mantidos.
        self._estilos_personalizados = {}
        self._canvas_draw_original = self.canvas.draw

        def desenhar_com_estilos(*args, **kwargs):
            self._aplicar_estilos_personalizados()
            return self._canvas_draw_original(*args, **kwargs)

        self.canvas.draw = desenhar_com_estilos
        self.botao_estilos = QPushButton("Editor único de curvas — cores, espessuras e estilos")
        self.botao_estilos.setToolTip(
            "Personalizar cor, padrão e espessura de cada curva do gráfico atual"
        )
        self.botao_estilos.clicked.connect(self.abrir_editor_estilos)
        layout.insertWidget(1, self.botao_estilos)

    def _linhas_do_grafico(self):
        for ia, ax in enumerate(self.figure.axes):
            for il, linha in enumerate(ax.lines):
                yield (ia, il), ax, linha

    def _aplicar_estilos_personalizados(self):
        for chave, _ax, linha in self._linhas_do_grafico():
            estilo = self._estilos_personalizados.get(chave)
            if not estilo:
                continue
            if "color" in estilo:
                linha.set_color(estilo["color"])
            if "linestyle" in estilo:
                linha.set_linestyle(estilo["linestyle"])
            if "linewidth" in estilo:
                linha.set_linewidth(estilo["linewidth"])
            if "label" in estilo:
                linha.set_label(estilo["label"])
            if "visible" in estilo:
                linha.set_visible(estilo["visible"])
            if "alpha" in estilo:
                linha.set_alpha(estilo["alpha"])
            if "marker" in estilo:
                linha.set_marker(estilo["marker"])

        # As legendas guardam copias dos artistas: sincronizar com as curvas.
        for ax in self.figure.axes:
            legenda = ax.get_legend()
            if legenda is None:
                continue
            handles = getattr(legenda, "legend_handles", None)
            if handles is None:
                handles = getattr(legenda, "legendHandles", [])
            linhas_por_rotulo = {}
            for linha in ax.lines:
                rotulo = linha.get_label()
                if rotulo and not rotulo.startswith("_"):
                    linhas_por_rotulo.setdefault(rotulo, []).append(linha)
            for handle, texto in zip(handles, legenda.get_texts()):
                candidatas = linhas_por_rotulo.get(texto.get_text(), [])
                if not candidatas or not hasattr(handle, "set_linestyle"):
                    continue
                original = candidatas[0]
                handle.set_linestyle(original.get_linestyle())
                handle.set_linewidth(original.get_linewidth())
                handle.set_color(original.get_color())
                handle.set_alpha(original.get_alpha())
                handle.set_marker(original.get_marker())
                handle.set_visible(original.get_visible())

    @staticmethod
    def ocultar_controle_de_estilo(widget):
        """Esconde controles duplicados, inclusive o rótulo do QFormLayout."""
        widget.setVisible(False)
        pai = widget.parentWidget()
        if pai is not None and isinstance(pai.layout(), QFormLayout):
            rotulo = pai.layout().labelForField(widget)
            if rotulo is not None:
                rotulo.setVisible(False)

    def abrir_editor_estilos(self):
        """Editor contextual, agrupado por painel e com propriedades por curva.

        A seleção de nspin=2 permanece nos checkboxes originais das abas.
        As alterações só são confirmadas ao pressionar Aplicar ou OK.
        """
        linhas = list(self._linhas_do_grafico())
        # Não inferir spin pela presença de controles: usar apenas as
        # curvas efetivamente desenhadas para o modo selecionado.
        if not linhas:
            QMessageBox.information(
                self, "Editor de curvas",
                "Importe os dados e gere um gráfico antes de editar as curvas."
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Editor de curvas — propriedades individuais")
        dlg.resize(800, 540)
        raiz = QVBoxLayout(dlg)
        instrucao = QLabel(
            "Selecione um painel e uma curva à esquerda. "
            "Edite apenas as propriedades da curva selecionada à direita."
        )
        instrucao.setWordWrap(True)
        raiz.addWidget(instrucao)

        divisao = QSplitter(Qt.Orientation.Horizontal)
        raiz.addWidget(divisao, 1)

        arvore = QTreeWidget()
        arvore.setHeaderLabels(["Painéis e curvas"])
        arvore.setMinimumWidth(260)
        divisao.addWidget(arvore)

        direita = QWidget()
        direita_layout = QVBoxLayout(direita)
        divisao.addWidget(direita)
        divisao.setStretchFactor(0, 2)
        divisao.setStretchFactor(1, 3)

        titulo_curva = QLabel("Selecione uma curva")
        fonte = titulo_curva.font()
        fonte.setBold(True)
        titulo_curva.setFont(fonte)
        direita_layout.addWidget(titulo_curva)

        grupo = QGroupBox("Propriedades da curva")
        formulario = QFormLayout(grupo)
        nome = QLineEdit()
        formulario.addRow("Nome na legenda:", nome)
        visivel = QCheckBox("Exibir curva")
        formulario.addRow("Visibilidade:", visivel)
        estilo_combo = QComboBox()
        for rotulo, codigo in (
            ("Contínua", "-"), ("Tracejada", "--"),
            ("Pontilhada", ":"), ("Traço-ponto", "-."),
            ("Sem linha", "None")
        ):
            estilo_combo.addItem(rotulo, codigo)
        formulario.addRow("Estilo da linha:", estilo_combo)
        largura = QDoubleSpinBox()
        largura.setRange(0.1, 12.0)
        largura.setSingleStep(0.2)
        largura.setDecimals(2)
        largura.setSuffix(" pt")
        formulario.addRow("Espessura:", largura)
        opacidade = QSpinBox()
        opacidade.setRange(0, 100)
        opacidade.setSuffix(" %")
        formulario.addRow("Opacidade:", opacidade)
        marcador = QComboBox()
        for rotulo, codigo in (
            ("Nenhum", "None"), ("Círculo", "o"),
            ("Quadrado", "s"), ("Triângulo", "^"),
            ("Losango", "D"), ("Cruz", "x"), ("Ponto", ".")
        ):
            marcador.addItem(rotulo, codigo)
        formulario.addRow("Marcador:", marcador)
        cor_botao = QPushButton("Escolher cor…")
        formulario.addRow("Cor:", cor_botao)
        direita_layout.addWidget(grupo)
        direita_layout.addStretch(1)

        # Estado temporário: cancelar não altera os gráficos.
        ajustes = {chave: dict(valor)
                   for chave, valor in self._estilos_personalizados.items()}
        pais = {}
        for indice, ((ia, il), ax, linha) in enumerate(linhas):
            if ia not in pais:
                titulo = ax.get_title().strip() or f"Painel {ia + 1}"
                pai = QTreeWidgetItem([f"{ia + 1}. {titulo}"])
                pai.setFlags(pai.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                arvore.addTopLevelItem(pai)
                pais[ia] = pai
            rotulo = linha.get_label()
            if not rotulo or rotulo.startswith("_"):
                rotulo = f"Curva {il + 1}"
            item = QTreeWidgetItem([rotulo])
            pais[ia].addChild(item)
            item.setData(0, Qt.ItemDataRole.UserRole, indice)
        arvore.expandAll()

        carregando = [False]
        cor_atual = ["#000000"]

        def indice_atual():
            item = arvore.currentItem()
            return item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None

        def configuracao_atual():
            indice = indice_atual()
            if indice is None:
                return None, None, None
            chave, _, linha = linhas[indice]
            return chave, linha, ajustes.get(chave, {})

        def selecionar():
            indice = indice_atual()
            grupo.setEnabled(indice is not None)
            if indice is None:
                titulo_curva.setText("Selecione uma curva")
                return
            carregando[0] = True
            chave, linha, cfg = configuracao_atual()
            titulo_curva.setText(arvore.currentItem().text(0))
            nome.setText(str(cfg.get("label", linha.get_label())))
            visivel.setChecked(bool(cfg.get("visible", linha.get_visible())))
            estilo = cfg.get("linestyle", linha.get_linestyle())
            pos = estilo_combo.findData(estilo)
            estilo_combo.setCurrentIndex(max(0, pos))
            largura.setValue(float(cfg.get("linewidth", linha.get_linewidth())))
            alpha = cfg.get("alpha", linha.get_alpha())
            opacidade.setValue(round(100 * (1.0 if alpha is None else alpha)))
            marca = cfg.get("marker", linha.get_marker())
            pos = marcador.findData(marca)
            marcador.setCurrentIndex(max(0, pos))
            from matplotlib.colors import to_hex
            try:
                cor_atual[0] = to_hex(cfg.get("color", linha.get_color()))
            except (ValueError, TypeError):
                cor_atual[0] = "#000000"
            cor_botao.setStyleSheet(
                f"background-color: {cor_atual[0]};"
            )
            carregando[0] = False

        def salvar_controle(*_):
            if carregando[0]:
                return
            chave, linha, _ = configuracao_atual()
            if chave is None:
                return
            ajustes[chave] = {
                "label": nome.text(),
                "visible": visivel.isChecked(),
                "color": cor_atual[0],
                "linestyle": estilo_combo.currentData(),
                "linewidth": largura.value(),
                "alpha": opacidade.value() / 100.0,
                "marker": marcador.currentData(),
            }
            arvore.currentItem().setText(
                0, nome.text().strip() or f"Curva {chave[1] + 1}"
            )

        def escolher_cor():
            if indice_atual() is None:
                return
            from PySide6.QtGui import QColor
            cor = QColorDialog.getColor(QColor(cor_atual[0]), dlg, "Cor da curva")
            if cor.isValid():
                cor_atual[0] = cor.name()
                cor_botao.setStyleSheet(f"background-color: {cor_atual[0]};")
                salvar_controle()

        arvore.currentItemChanged.connect(lambda *_: selecionar())
        nome.textEdited.connect(salvar_controle)
        visivel.toggled.connect(salvar_controle)
        estilo_combo.currentIndexChanged.connect(salvar_controle)
        largura.valueChanged.connect(salvar_controle)
        opacidade.valueChanged.connect(salvar_controle)
        marcador.currentIndexChanged.connect(salvar_controle)
        cor_botao.clicked.connect(escolher_cor)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel
        )
        raiz.addWidget(botoes)

        def aplicar():
            salvar_controle()
            self._estilos_personalizados = {
                chave: dict(valor) for chave, valor in ajustes.items()
            }
            self._aplicar_estilos_personalizados()
            self.canvas.draw_idle()

        botoes.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(aplicar)

        def aceitar():
            aplicar()
            dlg.accept()

        botoes.accepted.connect(aceitar)
        botoes.rejected.connect(dlg.reject)
        if pais:
            primeira = pais[min(pais)].child(0)
            if primeira is not None:
                arvore.setCurrentItem(primeira)
        dlg.exec()

    def set_single_mode(self):
        if self.axes_grid is not None:
            self.figure.clear()
            self.axes_grid = None
            self.ax = self.figure.add_subplot(111)
        return self.ax

    def set_spin_grid(self):
        """
        Garante a matriz 2x3. Ela só é criada quando ainda não existe.
        Depois disso, as atualizações reutilizam os MESMOS Axes.
        """
        if self.axes_grid is None or getattr(self.axes_grid, "shape", None) != (2, 3):
            self.figure.clear()
            self.axes_grid = self.figure.subplots(
                2, 3,
                sharey=False,
                gridspec_kw={"width_ratios": [1.25, 1.0, 1.0]}
            )
            self.ax = self.axes_grid[0, 0]
        return self.axes_grid

    def reset_spin_axes(self):
        """
        Mesmo princípio usado pelo gráfico DOS:
        limpa os MESMOS Axes antes de redesenhar, sem recriar Figure/Axes.
        """
        axes = self.set_spin_grid()

        # Remove título global anterior sem destruir a Figure.
        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None

        for ax in axes.flat:
            ax.clear()
            ax.set_facecolor(mpl.rcParams["axes.facecolor"])

        self.ax = axes[0, 0]
        return axes

    def reset_bands_three_axes(self):
        """Três painéis lado a lado para bandas + PDOS em nspin=1."""
        if self.axes_grid is None or getattr(self.axes_grid, "shape", None) != (3,):
            self.figure.clear()
            self.axes_grid = self.figure.subplots(
                1, 3, sharey=False,
                gridspec_kw={"width_ratios": [1.25, 1.0, 1.0]}
            )
        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None
        for ax in self.axes_grid:
            ax.clear()
        self.ax = self.axes_grid[0]
        return self.axes_grid

    def set_dos_spin_grid(self):
        """
        Matriz 1x2 exclusiva da aba DOS em nspin=2:
        esquerda = DOS UP; direita = DOS DOWN.
        Os mesmos Axes são reutilizados para evitar ghosting no Qt.
        """
        if self.axes_grid is None or getattr(self.axes_grid, "shape", None) != (2,):
            self.figure.clear()
            self.axes_grid = self.figure.subplots(
                1, 2,
                sharex=False,
                sharey=False
            )
            self.ax = self.axes_grid[0]
        return self.axes_grid

    def reset_dos_spin_axes(self):
        axes = self.set_dos_spin_grid()

        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None

        for ax in axes.flat:
            ax.clear()
            ax.set_facecolor(mpl.rcParams["axes.facecolor"])

        self.ax = axes[0]
        return axes

    def set_pdos_spin_grid(self):
        """
        Matriz 2x2 exclusiva da aba PDOS em nspin=2:
        linha 1 = UP; linha 2 = DOWN;
        coluna 1 = por elemento; coluna 2 = por orbital.

        A matriz é criada uma única vez e os mesmos Axes são reutilizados,
        evitando ghosting na pré-visualização Qt.
        """
        if self.axes_grid is None or getattr(self.axes_grid, "shape", None) != (2, 2):
            self._mirrored_pdos = False
            self.figure.clear()
            self.axes_grid = self.figure.subplots(
                2, 2,
                sharex=False,
                sharey=False
            )
            self.ax = self.axes_grid[0, 0]
        return self.axes_grid

    def reset_pdos_spin_axes(self):
        axes = self.set_pdos_spin_grid()

        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None

        for ax in axes.flat:
            ax.clear()
            ax.set_facecolor(mpl.rcParams["axes.facecolor"])

        self.ax = axes[0, 0]
        return axes

    def reset_dos_mirrored_axes(self):
        """Um único painel para DOS UP e DOWN espelhado."""
        if self.axes_grid is not None or len(self.figure.axes) != 1:
            self.figure.clear()
            self.axes_grid = None
            self.ax = self.figure.add_subplot(111)
        self.ax.clear()
        self.ax.set_facecolor(mpl.rcParams["axes.facecolor"])
        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None
        return self.ax

    def reset_pdos_mirrored_axes(self):
        """Dois painéis: espécies (UP/DOWN) e orbitais (UP/DOWN)."""
        if self.axes_grid is None or getattr(self.axes_grid, "shape", None) != (2,) or getattr(self, "_mirrored_pdos", False) is False:
            self.figure.clear()
            self.axes_grid = self.figure.subplots(1, 2, sharex=False, sharey=False)
        self._mirrored_pdos = True
        if getattr(self.figure, "_suptitle", None) is not None:
            self.figure._suptitle.remove()
            self.figure._suptitle = None
        for ax in self.axes_grid:
            ax.clear()
            ax.set_facecolor(mpl.rcParams["axes.facecolor"])
        self.ax = self.axes_grid[0]
        return self.axes_grid

    def clear(self):
        """
        Limpa o eixo atual sem destruir a Figure/Canvas.
        Isso é mais estável com o backend Qt e evita imagens
        residuais ("ghosting") no widget embutido.
        """
        axes = (
            list(self.axes_grid.flat)
            if self.axes_grid is not None
            else [self.ax]
        )
        for ax in axes:
            ax.clear()
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
        self.canvas.draw()

    def reset_axes(self):
        """
        Remove todos os artistas do MESMO Axes antes de redesenhar.

        Importante:
        não usamos figure.clf() nem recriamos o Axes, pois a
        substituição contínua da Figure/Axes pode interagir mal
        com o backing store do Qt.
        """
        self.set_single_mode()
        self.ax.clear()

    def redraw(self, use_tight_layout=True):
        """Redesenha e aplica a tipografia uniformemente em todas as abas."""
        self.aplicar_tipografia()
        if use_tight_layout:
            self.figure.tight_layout()
        self.canvas.draw()

    def aplicar_tipografia(self):
        """Aplica os controles de fonte também aos painéis compostos e spin."""
        controles = getattr(self, "style_controls", None)
        if controles is None:
            return
        negrito_titulo = controles.bold_title.isChecked()
        negrito_eixos = controles.bold_axis.isChecked()
        negrito_ticks = controles.bold_ticks.isChecked()
        negrito_legenda = controles.bold_legend.isChecked()
        usar_tex = controles.latex_global.isChecked()

        # O backend TeX é definido antes da criação dos novos artistas.
        # Aplicar aqui também garante consistência entre os três módulos.
        mpl.rcParams["text.usetex"] = usar_tex
        if usar_tex:
            mpl.rcParams["text.latex.preamble"] = (
                r"\usepackage[version=4]{mhchem}"
                r"\usepackage{amsmath}"
                r"\usepackage{bm}"
            )

        def estilizar(texto, negrito):
            texto.set_fontweight("bold" if negrito else "normal")
            # No modo TeX, fontweight pode ser ignorado: forçar o peso no texto.
            if usar_tex and negrito and texto.get_text():
                original = texto.get_text()
                if not original.startswith(r"{\bfseries\boldmath "):
                    texto.set_text(texto_latex_negrito(original, True, True))

        for ax in self.figure.axes:
            estilizar(ax.title, negrito_titulo)
            estilizar(ax.xaxis.label, negrito_eixos)
            estilizar(ax.yaxis.label, negrito_eixos)
            for tick in ax.get_xticklabels() + ax.get_yticklabels():
                estilizar(tick, negrito_ticks)
            legenda = ax.get_legend()
            if legenda is not None:
                for texto in legenda.get_texts():
                    estilizar(texto, negrito_legenda)
                titulo_legenda = legenda.get_title()
                if titulo_legenda.get_text():
                    estilizar(titulo_legenda, negrito_legenda)
        for texto in self.figure.texts:
            estilizar(texto, negrito_titulo)


