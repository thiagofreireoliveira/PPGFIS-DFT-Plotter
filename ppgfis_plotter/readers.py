# -*- coding: utf-8 -*-
from __future__ import annotations
from .common import *

def nome_sistema_de_arquivo(caminho: str) -> str:
    """Obtém um nome de sistema legível a partir do arquivo principal."""
    nome = os.path.basename(str(caminho).strip())
    sufixos = (
        ".scf.out", ".scf.in", ".nscf.out", ".nscf.in",
        ".bands.dat.gnu", ".band.gnu", ".bands.gnu",
        ".pdos_tot", ".dos.dat", ".dos", ".out", ".in",
    )
    low = nome.lower()
    for suf in sufixos:
        if low.endswith(suf):
            nome = nome[:len(nome)-len(suf)]
            break
    return nome or "sistema"


def extrair_fermi_dos(arquivo: str) -> float:
    padrao = re.compile(
        r"EFermi\s*=\s*([+-]?\d+(?:\.\d+)?)\s*eV",
        re.IGNORECASE
    )

    with open(arquivo, "r", errors="ignore") as f:
        for _ in range(20):
            linha = f.readline()
            if not linha:
                break

            m = padrao.search(linha)

            if m:
                return float(m.group(1))

    raise ValueError("EFermi não encontrado no cabeçalho do arquivo DOS.")


def ler_energia_referencia_scf(arquivo: str):
    with open(arquivo, "r", errors="ignore") as f:
        texto = f.read()

    fermi = re.findall(
        r"the Fermi energy is\s+([-+]?\d*\.?\d+)\s+ev",
        texto,
        flags=re.IGNORECASE
    )

    if fermi:
        return float(fermi[-1]), "Fermi energy"

    ocupado = re.findall(
        r"highest occupied level\s*\(ev\)\s*:\s*([-+]?\d*\.?\d+)",
        texto,
        flags=re.IGNORECASE
    )

    if ocupado:
        return float(ocupado[-1]), "Highest occupied level"

    raise ValueError(
        "Não foi possível encontrar Fermi energy "
        "ou highest occupied level no arquivo SCF."
    )


def ler_bandas(arquivo: str):
    """
    Lê arquivo de bandas em formato de duas colunas (k, energia),
    com bandas separadas por linhas em branco. Linhas textuais de cabeçalho
    são ignoradas, mas um arquivo sem blocos numéricos válidos é rejeitado.
    """
    bandas = []
    bloco = []

    with open(arquivo, "r", errors="replace") as f:
        for linha in f:
            s = linha.strip()

            if not s:
                if bloco:
                    bandas.append(np.array(bloco, dtype=float))
                    bloco = []
                continue

            if s.startswith("#"):
                continue

            partes = s.replace("D", "E").replace("d", "e").split()
            if len(partes) < 2:
                continue

            try:
                k = float(partes[0])
                e = float(partes[1])
            except ValueError:
                # Ignora cabeçalhos/texto do Quantum ESPRESSO.
                continue

            bloco.append([k, e])

    if bloco:
        bandas.append(np.array(bloco, dtype=float))

    if not bandas:
        raise ValueError(
            f"Nenhum bloco numérico de bandas foi encontrado em:\n{arquivo}\n\n"
            "Para Bandas UP/DOWN selecione o arquivo de dados com duas colunas "
            "(k e energia), normalmente o arquivo .gnu produzido para plotagem, "
            "e não o arquivo .out do bands.x/pw.x."
        )

    n = len(bandas[0])
    for banda in bandas:
        if len(banda) != n:
            raise ValueError(
                f"As bandas em {arquivo} possuem números diferentes de pontos. "
                "Verifique se foi selecionado o arquivo de plotagem correto."
            )

    return bandas


def detectar_elemento_nome(nome_arquivo: str):
    """
    Detecta o símbolo químico a partir do nome padrão do projwfc.x.

    Exemplo:
        prefix.pdos_atm#1(B)_wfc#1(s)
                           ^
                           B

    Retorna, por exemplo: B, N, C, Eu, Mo, O...
    """
    m = re.search(
        r"_atm#\d+\(([A-Z][a-z]?)\)",
        nome_arquivo
    )

    if m:
        return m.group(1)

    return None


def detectar_orbital_nome(nome_arquivo: str):
    """
    Detecta o orbital a partir de padrões do projwfc.x, por exemplo:
      _wfc#1(s)
      _wfc#2(p)
      _wfc#3(d)
      _wfc#4(f)

    Retorna: 's', 'p', 'd', 'f' ou None.
    """
    m = re.search(r"_wfc#\d+\(([spdf])\)", nome_arquivo, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    return None


def organizar_arquivos_pdos(diretorio_origem: str, diretorio_destino: str):
    """
    Copia/move arquivos de PDOS do diretório de origem para uma pasta
    organizada por orbitais.

    Estrutura criada:
        orbitals/
            s/
            p/
            d/
            f/

    Retorna um dicionário com as quantidades movidas.
    """
    origem = os.path.abspath(diretorio_origem)
    destino = os.path.abspath(diretorio_destino)

    os.makedirs(destino, exist_ok=True)

    contagem = {"s": 0, "p": 0, "d": 0, "f": 0}

    for nome in os.listdir(origem):
        caminho = os.path.join(origem, nome)

        if not os.path.isfile(caminho):
            continue

        orbital = detectar_orbital_nome(nome)

        if orbital is None:
            continue

        pasta_orbital = os.path.join(destino, orbital)
        os.makedirs(pasta_orbital, exist_ok=True)

        alvo = os.path.join(pasta_orbital, nome)

        # Evita erro se o arquivo já estiver organizado
        if os.path.abspath(caminho) == os.path.abspath(alvo):
            continue

        shutil.move(caminho, alvo)
        contagem[orbital] += 1

    return contagem


def listar_arquivos_pdos(diretorio_pdos: str):
    """
    Retorna {'s': [...], 'p': [...], 'd': [...], 'f': [...]}
    aceitando tanto:
      orbitals/arquivo_wfc#1(s)
    quanto:
      orbitals/s/arquivo_wfc#1(s)
    """
    grupos = {"s": [], "p": [], "d": [], "f": []}

    if not os.path.isdir(diretorio_pdos):
        return grupos

    for raiz, _, arquivos in os.walk(diretorio_pdos):
        for nome in arquivos:
            orbital = detectar_orbital_nome(nome)

            if orbital is not None:
                grupos[orbital].append(
                    os.path.join(raiz, nome)
                )

    return grupos


def ler_pdos_tot(arquivo):
    dados = np.loadtxt(arquivo, skiprows=1)

    if dados.ndim != 2 or dados.shape[1] < 2:
        raise ValueError(
            "O arquivo .pdos_tot deve possuir pelo menos duas colunas."
        )

    return dados[:, 0], dados[:, 1]


def ler_arquivo_pdos(arquivo):
    dados = np.loadtxt(arquivo, skiprows=1)

    if dados.ndim != 2 or dados.shape[1] < 2:
        raise ValueError(
            f"Arquivo PDOS inválido: {arquivo}"
        )

    return dados[:, 0], dados[:, 1]


def ler_pdos_tot_spin(arquivo):
    """
    Lê o arquivo *.pdos_tot do projwfc.x para nspin=2.

    Formato esperado do Quantum ESPRESSO:
        E(eV)  DOSup  DOSdown  PDOSup  PDOSdown

    Retorna:
        energia, dos_up, dos_down, pdos_up, pdos_down

    Esta função é usada tanto pela aba Estrutura de Bandas quanto pela aba
    PDOS, garantindo que ambas interpretem o mesmo arquivo da mesma forma.
    """
    linhas = []

    with open(arquivo, "r", errors="replace") as f:
        for linha in f:
            s = linha.strip()

            if not s or s.startswith("#"):
                continue

            partes = s.replace("D", "E").replace("d", "e").split()

            if len(partes) < 5:
                continue

            try:
                valores = [float(partes[i]) for i in range(5)]
            except ValueError:
                continue

            linhas.append(valores)

    if not linhas:
        raise ValueError(
            f"Nenhum conjunto válido de 5 colunas foi encontrado em:\n{arquivo}\n\n"
            "Para nspin=2, selecione o arquivo *.pdos_tot produzido pelo "
            "projwfc.x, com as colunas E, DOSup, DOSdown, PDOSup e PDOSdown."
        )

    dados = np.asarray(linhas, dtype=float)

    if dados.ndim != 2 or dados.shape[1] < 5:
        raise ValueError(
            f"Arquivo incompatível com *.pdos_tot nspin=2:\n{arquivo}\n"
            "São necessárias cinco colunas numéricas."
        )

    energia = dados[:, 0]
    dos_up = dados[:, 1]
    dos_down = dados[:, 2]
    pdos_up = dados[:, 3]
    pdos_down = dados[:, 4]

    return energia, dos_up, dos_down, pdos_up, pdos_down


def ler_pdos_spin(arquivo):
    """
    Lê um arquivo individual *.pdos_atm#... do projwfc.x em nspin=2.

    Para arquivos individuais do QE, as colunas são:
        0 = E(eV)
        1 = ldosup(E)   -> contribuição total UP daquele WFC
        2 = ldosdw(E)   -> contribuição total DOWN daquele WFC

    As colunas seguintes são as componentes m-resolvidas e NÃO devem ser
    somadas novamente quando queremos PDOS total por elemento/orbital,
    pois ldosup/ldosdw já contêm essa soma.
    """
    linhas = []

    with open(arquivo, "r", errors="replace") as f:
        for linha in f:
            s = linha.strip()
            if not s or s.startswith("#"):
                continue

            partes = s.replace("D", "E").replace("d", "e").split()
            if len(partes) < 3:
                continue

            try:
                linhas.append([
                    float(partes[0]),
                    float(partes[1]),
                    float(partes[2]),
                ])
            except ValueError:
                continue

    if not linhas:
        raise ValueError(
            f"Nenhum dado nspin=2 válido encontrado em:\n{arquivo}"
        )

    dados = np.asarray(linhas, dtype=float)
    return dados[:, 0], dados[:, 1], dados[:, 2]


def somar_pdos_spin(diretorio_pdos, energia_ref):
    """
    Soma os arquivos individuais do projwfc.x em nspin=2 por orbital
    e por elemento, preservando separadamente UP e DOWN.

    Validação:
      - usa ldosup/ldosdw (colunas 1/2);
      - exige a mesma malha de energia do *.pdos_tot;
      - não normaliza UP/DOWN;
      - não reescala um canal em função do outro.
    """
    grupos_orb = listar_arquivos_pdos(diretorio_pdos)
    grupos_el = agrupar_pdos_por_elemento(diretorio_pdos)

    energia_ref = np.asarray(energia_ref, dtype=float)

    orb_up = {o: np.zeros_like(energia_ref) for o in ("s", "p", "d", "f")}
    orb_dn = {o: np.zeros_like(energia_ref) for o in ("s", "p", "d", "f")}
    usados_orb = {o: 0 for o in ("s", "p", "d", "f")}

    def validar_grade(arquivo, energia):
        if len(energia) != len(energia_ref):
            raise ValueError(f"Número de pontos incompatível em {arquivo}.")
        if not np.allclose(energia, energia_ref, rtol=0.0, atol=1.0e-8):
            raise ValueError(
                f"Malha de energia incompatível com o pdos_tot em:\n{arquivo}"
            )

    for orbital, arquivos in grupos_orb.items():
        if orbital not in orb_up:
            continue
        for arquivo in arquivos:
            energia, up, dn = ler_pdos_spin(arquivo)
            validar_grade(arquivo, energia)
            orb_up[orbital] += up
            orb_dn[orbital] += dn
            usados_orb[orbital] += 1

    el_up, el_dn, usados_el = {}, {}, {}
    for elemento, arquivos in grupos_el.items():
        el_up[elemento] = np.zeros_like(energia_ref)
        el_dn[elemento] = np.zeros_like(energia_ref)
        usados_el[elemento] = 0

        for arquivo in arquivos:
            energia, up, dn = ler_pdos_spin(arquivo)
            validar_grade(arquivo, energia)
            el_up[elemento] += up
            el_dn[elemento] += dn
            usados_el[elemento] += 1

    return orb_up, orb_dn, el_up, el_dn, usados_orb, usados_el


def somar_pdos_por_orbital(arquivo_pdos_tot, diretorio_pdos, nivel_fermi):
    """
    Soma todos os arquivos PDOS por orbital s/p/d/f.
    """
    energia_abs, dos_total = ler_pdos_tot(arquivo_pdos_tot)
    energia = energia_abs - nivel_fermi

    grupos = listar_arquivos_pdos(diretorio_pdos)

    acumulado = {
        "s": np.zeros_like(energia),
        "p": np.zeros_like(energia),
        "d": np.zeros_like(energia),
        "f": np.zeros_like(energia),
    }

    usados = {k: 0 for k in acumulado}

    for orbital, arquivos in grupos.items():
        for arquivo in arquivos:
            e_pdos, d_pdos = ler_arquivo_pdos(arquivo)

            if len(d_pdos) != len(energia):
                raise ValueError(
                    f"Número de pontos incompatível em {arquivo}."
                )

            acumulado[orbital] += d_pdos
            usados[orbital] += 1

    return energia, dos_total, acumulado, usados


def agrupar_pdos_por_elemento(diretorio_pdos: str):
    """
    Agrupa os arquivos PDOS por símbolo químico.
    """
    grupos = {}

    if not os.path.isdir(diretorio_pdos):
        return grupos

    for raiz, _, arquivos in os.walk(diretorio_pdos):

        for nome in arquivos:

            elemento = detectar_elemento_nome(nome)

            if elemento is None:
                continue

            grupos.setdefault(elemento, []).append(
                os.path.join(raiz, nome)
            )

    return grupos


def somar_pdos_por_elemento(energia_ref, diretorio_pdos):
    """
    Soma a PDOS de todos os átomos do mesmo elemento.

    energia_ref:
        vetor de energia usado como referência de tamanho.

    Retorna:
        pdos_elementos = {'B': array, 'N': array, ...}
        usados_elementos = {'B': n_arquivos, ...}
    """
    grupos = agrupar_pdos_por_elemento(diretorio_pdos)

    acumulado = {}
    usados = {}

    for elemento, arquivos in grupos.items():

        acumulado[elemento] = np.zeros_like(energia_ref)
        usados[elemento] = 0

        for arquivo in arquivos:

            e_pdos, d_pdos = ler_arquivo_pdos(arquivo)

            if len(d_pdos) != len(energia_ref):
                raise ValueError(
                    f"Número de pontos incompatível em {arquivo}."
                )

            acumulado[elemento] += d_pdos
            usados[elemento] += 1

    return acumulado, usados


