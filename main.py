import streamlit as st
from docxtpl import DocxTemplate
import base64
import tempfile
import re
import shutil
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from subprocess import PIPE, run


@st.cache_resource(ttl=60*60*24)
def cleanup_tempdir() -> None:
    '''
    Cleanup temp dir for all user sessions.
    Filters the temp dir for uuid4 subdirs.
    Deletes them if they exist and are older than 1 day.
    '''
    deleteTime = datetime.now() - timedelta(days=1)
    # compile regex for uuid4
    uuid4_regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuid4_regex = re.compile(uuid4_regex)
    tempfiledir = Path(tempfile.gettempdir())
    if tempfiledir.exists():
        subdirs = [x for x in tempfiledir.iterdir() if x.is_dir()]
        subdirs_match = [x for x in subdirs if uuid4_regex.match(x.name)]
        for subdir in subdirs_match:
            itemTime = datetime.fromtimestamp(subdir.stat().st_mtime)
            if itemTime < deleteTime:
                shutil.rmtree(subdir)


# TODO: this function is unused yet
def cleanup_session_tempdir() -> None:
    '''
    Cleanup temp dir for user session.
    Deletes the whole session temp dir if it exists.
    '''
    if 'tempfiledir' in st.session_state:
        tempfiledir = st.session_state['tempfiledir']
        if tempfiledir.exists():
            shutil.rmtree(tempfiledir)

@st.cache_data(show_spinner=False)
def make_tempdir() -> Path:
    '''
    Make temp dir for each user session and return path to it.

    :return: Path to temp dir
    '''
    if 'tempfiledir' not in st.session_state:
        tempfiledir = Path(tempfile.gettempdir())
        tempfiledir = tempfiledir.joinpath(f"{uuid.uuid4()}")   # make unique subdir
        tempfiledir.mkdir(parents=True, exist_ok=True)  # make dir if not exists
        st.session_state['tempfiledir'] = tempfiledir
    return st.session_state['tempfiledir']

def check_if_file_with_same_name_and_hash_exists(tempfiledir: Path, file_name: str, hashval: int) -> bool:
    '''
    Check if file with same name and hash already exists in tempdir.

    :params tempfiledir: Path to file
    :params file_name: Name of file
    :params hashval: Hash of file
    :return bool: True if file with same name and hash already exists in tempdir
    '''
    file_path = tempfiledir.joinpath(file_name)
    if file_path.exists():
        file_hash = hash((file_path.name, file_path.stat().st_size))
        if file_hash == hashval:
            return True
    return False

def store_file_in_tempdir(tmpdirname: Path, uploaded_file: BytesIO) -> Path:
    '''
    Store file in temp dir and return path to it

    :params tmpdirname: Path to temp dir
    :params uploaded_file: BytesIO object
    :return: Path to stored file
    '''
    # store file in temp dir
    tmpfile = tmpdirname.joinpath(uploaded_file.name)
    with open(tmpfile, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return tmpfile

def convert_doc_to_pdf_native(doc_file: Path, output_dir: Path=Path("."), timeout: int=300):
    '''
    Converts a doc file to pdf using libreoffice without msoffice2pdf.
    Calls libroeoffice (soffice) directly in headless mode.

    :param doc_file: Path to doc file
    :param output_dir: Path to output dir
    :param timeout: Timeout for subprocess in seconds

    :returns output: Path to converted file
    :returns exception: Exception if conversion failed
    '''
    exception = None
    output = None
    try:
        process = run(['soffice', '--headless', '--convert-to',
            'pdf:writer_pdf_Export', '--outdir', output_dir.resolve(), doc_file.resolve()],
            stdout=PIPE, stderr=PIPE,
            timeout=timeout, check=True)
        stdout = process.stdout.decode("utf-8")
        re_filename = re.search('-> (.*?) using filter', stdout)
        output = Path(re_filename[1]).resolve()
    except Exception as e:
        exception = e
    return (output, exception)

def get_bytes_from_file(file_path: Path) -> bytes:
    '''
    Write something here.
    '''
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return file_bytes

@st.cache_data(show_spinner=False)
def show_pdf_base64(base64_pdf):
    '''
    Show PDF in iframe already base64 encoded

    :param base64_pdf: The PDF converted to base64.
    '''
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_base64_encoded_bytes(file_bytes) -> str:
    '''
    Convert the PDF to base64.

    :return base64_encoded: The base64 encoded string.
    '''
    base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
    return base64_encoded


    
# ----------------------------------------------------------------------------------------------------
st.title("CV Template")

# ----------------------------------------------------------------------------------------------------
st.header("Vaga")
vaga = st.text_input("Vaga", key="Vaga")

# ----------------------------------------------------------------------------------------------------
st.header("Nome")
nome_candidato = st.text_input("Nome", key="NomeCandidato")

# ----------------------------------------------------------------------------------------------------
st.header("Apresentação")
apresentacao = st.text_area("Apresentação", key="Apresentacao")

# ----------------------------------------------------------------------------------------------------
# Inicializa a sessão com a chave de controle se ainda não existir
if "experiencias" not in st.session_state:
    st.session_state.experiencias = []

if "experiencia_counter" not in st.session_state:
    st.session_state.experiencia_counter = 0

with st.container(border=True):
    h0, h1 = st.columns([10,1])
    h0.header("Experiencia")

    # Botão para adicionar nova experiência
    if h1.button("", icon=":material/add:", key="Experiencia"):
        new_id = st.session_state.experiencia_counter
        st.session_state.experiencias.append(new_id)
        st.session_state.experiencia_counter += 1  # Garante unicidade dos próximos IDs

    # Lista auxiliar para experiências a serem removidas
    experiencia_remover_ids = []

    # Renderiza cada bloco de experiência já adicionado
    for i in st.session_state.experiencias:
        # Recupera o valor atual do campo "Empresa", se já existir
        key_empresa = f"ExperienciaEmpresa-{i}"
        key_cargo = f"ExperienciaCargo-{i}"
        empresa_nome = st.session_state.get(key_empresa)
        cargo_nome = st.session_state.get(key_cargo)
        exp = ""
        if empresa_nome and cargo_nome:
            exp = empresa_nome + " - " + cargo_nome

        with st.expander(label=exp or "Empresa - Cargo", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Início", key=f"ExperienciaInicio-{i}")

            with col2:
                st.text_input("Fim", key=f"ExperienciaFim-{i}")
            
            col3, col4 = st.columns(2)
            col3.text_input("Cargo", key=key_cargo)
            col4.text_input("Empresa", key=key_empresa)
            
            experiencia_descricao = st.text_area("Descrição", key=f"ExperienciaDescricao-{i}")

            # Botão de remover experiência
            b0, b1 = st.columns([10,1])
            if b1.button("", key=f"ExperienciaRemover-{i}", icon=":material/delete:"):
                experiencia_remover_ids.append(i)

# Remove as experiências marcadas
if experiencia_remover_ids:
    for rid in experiencia_remover_ids:
        st.session_state.experiencias.remove(rid)
        # Limpa os campos relacionados do session_state
        for campo in ["Inicio", "Fim", "Cargo", "Empresa", "Descricao"]:
            key = f"Experiencia{campo}-{rid}"
            if key in st.session_state:
                del st.session_state[key]
    st.rerun()

# ----------------------------------------------------------------------------------------------------
if "habilidades" not in st.session_state:
    st.session_state.habilidades = []
if "limpar_habilidade" not in st.session_state:
    st.session_state.limpar_habilidade = False

# Limpa o campo de entrada se a flag estiver ativada
if st.session_state.limpar_habilidade:
    st.session_state.limpar_habilidade = False
    nova_habilidade = ""
else:
    nova_habilidade = st.session_state.get("NovaHabilidade", "")

with st.container(border=True):
    st.header("Habilidades")

    h0, h1 = st.columns([7,1])
    nova_habilidade = h0.text_input("Digite o nome da certificação", value=nova_habilidade, key="NovaHabilidade", label_visibility='collapsed')

    with h1:
        # st.markdown("<br>", unsafe_allow_html=True)  # empurra o botão para baixo
        if st.button("", icon=":material/add:", key="habilidade"):
            if nova_habilidade.strip():
                st.session_state.habilidades.append(nova_habilidade.strip())
                st.session_state.limpar_habilidade = True
                st.rerun()  # força a interface a recarregar e limpar o campo
            # else:
            #     st.warning("Digite o nome da certificação antes de adicionar.")

    # Exibe lista de certificações com botão de remover
    with st.expander(label=f"Habilidades ({st.session_state.habilidades.__len__()})", expanded=True):
        if st.session_state.habilidades:
            for idx, habi in enumerate(st.session_state.habilidades):

                b0, b1 = st.columns([7,1])
                b0.write(f"- {habi}")
                
                # Botão Remover
                if b1.button("", key=f"RemoverHabi-{idx}", icon=":material/delete:"):
                    st.session_state.habilidades.pop(idx)
                    st.rerun()

# ----------------------------------------------------------------------------------------------------
if "educacao" not in st.session_state:
    st.session_state.educacao = []

if "educacao_counter" not in st.session_state:
    st.session_state.educacao_counter = 0

with st.container(border=True):
    h0, h1 = st.columns([10,1])
    h0.header("Educação")

    if h1.button("", icon=":material/add:", key="educ"):
        new_id = st.session_state.educacao_counter
        st.session_state.educacao.append(new_id)
        st.session_state.educacao_counter += 1

    educacao_remover_ids = []

    for i in st.session_state.educacao:
        # Recupera o valor atual do campo "Empresa", se já existir
        key_curso = f"EducacaoCurso-{i}"
        key_instituicao = f"EducacaoInstituicao-{i}"
        curso_nome = st.session_state.get(key_curso)
        instituicao_nome = st.session_state.get(key_instituicao)
        exp = ""
        if curso_nome and instituicao_nome:
            exp = curso_nome + " - " + instituicao_nome
        with st.expander(label=exp or "Curso - Instituição", expanded=True):
            col1, col2 = st.columns(2)
            educacaoInicio = col1.text_input("Inicio", key=f"EducacaoInicio-{i}")
            educacaoFim = col2.text_input("Fim", key=f"EducacaoFim-{i}")
            
            col3, col4 = st.columns(2)
            educacaoCargo = col3.text_input("Curso", key=f"EducacaoCurso-{i}")
            educacaoInstituicao = col4.text_input("Instituição", key=f"EducacaoInstituicao-{i}")

            b0, b1 = st.columns([10,1])
            if b1.button("", key=f"EducacaoRemover-{i}", icon=":material/delete:"):
                educacao_remover_ids.append(i)

if educacao_remover_ids:
    for rid in educacao_remover_ids:
        st.session_state.educacao.remove(rid)
        for campo in ["Inicio","Fim","Curso","Instituição"]:
            key = f"Educacao{campo}-{rid}"
            if key in st.session_state:
                del st.session_state[key]
    st.rerun()

# ----------------------------------------------------------------------------------------------------
if "certificacoes" not in st.session_state:
    st.session_state.certificacoes = []
if "limpar_certificacao" not in st.session_state:
    st.session_state.limpar_certificacao = False

# Limpa o campo de entrada se a flag estiver ativada
if st.session_state.limpar_certificacao:
    st.session_state.limpar_certificacao = False
    nova_certificacao = ""
else:
    nova_certificacao = st.session_state.get("NovaCertificacao", "")

with st.container(border=True):
    st.header("Certificações / Cursos")

    h0, h1 = st.columns([7,1])
    nova_certificacao = h0.text_input("Digite o nome da certificação", value=nova_certificacao, key="NovaCertificacao", label_visibility='collapsed')

    with h1:
        # st.markdown("<br>", unsafe_allow_html=True)  # empurra o botão para baixo
        if st.button("", icon=":material/add:", key="certificado"):
            if nova_certificacao.strip():
                st.session_state.certificacoes.append(nova_certificacao.strip())
                st.session_state.limpar_certificacao = True
                st.rerun()  # força a interface a recarregar e limpar o campo
            # else:
            #     st.warning("Digite o nome da certificação antes de adicionar.")

    # Exibe lista de certificações com botão de remover
    with st.expander(label=f"Certificações ({st.session_state.certificacoes.__len__()})", expanded=True):
        if st.session_state.certificacoes:
            for idx, cert in enumerate(st.session_state.certificacoes):
                
                b0, b1 = st.columns([7,1])
                b0.write(f"- {cert}")

                # Botão Remover
                if b1.button("", key=f"RemoverCert-{idx}", icon=":material/delete:"):
                    st.session_state.certificacoes.pop(idx)
                    st.rerun()

# ----------------------------------------------------------------------------------------------------
if "idiomas" not in st.session_state:
    st.session_state.idiomas = []
if "limpar_idioma" not in st.session_state:
    st.session_state.limpar_idioma = False

# Limpa o campo de entrada se a flag estiver ativada
if st.session_state.limpar_idioma:
    st.session_state.limpar_idioma = False
    idiomaLingua = ""
    idiomaNivel = ""
else:
    idiomaLingua = st.session_state.get("idiomaLingua", "")
    idiomaNivel = st.session_state.get("idiomaNivel", "")
    

with st.container(border=True):
    st.header("Idiomas")

    h0, h1, h2 = st.columns([4,3,1])
    idiomaLingua = h0.text_input("Lingua", value=idiomaLingua, key="idiomaLingua")
    idiomaNivel = h1.text_input("Nivel", value=idiomaNivel, key="idiomaNivel")

    with h2:
        st.markdown("<br>", unsafe_allow_html=True)  # empurra o botão para baixo
        if st.button("", icon=":material/add:", key="idioma"):
            if idiomaLingua.strip() and idiomaNivel.strip():
                st.session_state.idiomas.append(idiomaLingua.strip() + " - " + idiomaNivel.strip())
                st.session_state.limpar_idioma = True
                st.rerun()  # força a interface a recarregar e limpar o campo
            # else:
            #     st.warning("Digite o nome da certificação antes de adicionar.")

    # Exibe lista de certificações com botão de remover
    with st.expander(label=f"Idiomas ({st.session_state.idiomas.__len__()})", expanded=True):
        if st.session_state.idiomas:
            for idx, idi in enumerate(st.session_state.idiomas):
                
                b0, b1 = st.columns([7,1])
                b0.write(f"- {idi}")

                # Botão Remover
                if b1.button("", key=f"RemoverIdi-{idx}", icon=":material/delete:"):
                    st.session_state.idiomas.pop(idx)
                    st.rerun()
                
# ----------------------------------------------------------------------------------------------------

st.markdown("---")
experiencias = []
habilidades = []
educacao = []
treinamentos = []
certificados = []
idiomas = []

if st.button("Gerar PDF", icon=":material/picture_as_pdf:"):
    cleanup_tempdir()
    for i in st.session_state.experiencias:
        periodo = st.session_state.get(f"ExperienciaInicio-{i}") + " - " + st.session_state.get(f"ExperienciaFim-{i}")
        item = {
            "periodo": periodo,
            "cargo": st.session_state.get(f"ExperienciaCargo-{i}"),
            "empresa": st.session_state.get(f"ExperienciaEmpresa-{i}"),
            "descricao": st.session_state.get(f"ExperienciaDescricao-{i}"),
        }
        experiencias.append(item)

    for i in st.session_state.habilidades:
        item = {
            "habilidade": i,
        }
        habilidades.append(item)
    
    for i in st.session_state.educacao:
        item = {
            "inicio": st.session_state.get(f"EducacaoInicio-{i}"),
            "fim": st.session_state.get(f"EducacaoFim-{i}"),
            "curso": st.session_state.get(f"EducacaoCurso-{i}"),
            "instituicao": st.session_state.get(f"EducacaoInstituicao-{i}"),
        }
        educacao.append(item)
    
    for i in st.session_state.certificacoes:
        item = {
            "certificado": i
        }
        certificados.append(item)
    
    for i in st.session_state.idiomas:
        item = {
            "idioma": i,
        }
        idiomas.append(item)

    doc = DocxTemplate('template.docx')

    context = {
        'vaga': vaga,
        'nome_candidato': nome_candidato,
        'apresentacao': apresentacao,
        'experiencias': experiencias,
        'habilidades': habilidades,
        'cursos': educacao,
        'treinamentos': treinamentos,
        'certificados': certificados,
        'idiomas': idiomas
    }

    # st.markdown("---")
    # st.subheader("Dados preenchidos:")
    # st.write(context)
    # st.markdown("---")


    tmpdirname = make_tempdir()

    doc.render(context)
    doc.save(f"{tmpdirname}\{vaga}_{nome_candidato}.docx")
    # doc.save(f"{vaga}_{nome_candidato}.docx")

    
    with st.spinner('Converting file...'):
        pdf_file, exception = convert_doc_to_pdf_native(doc_file=Path(f"{tmpdirname}\{vaga}_{nome_candidato}.docx"), output_dir=tmpdirname)
    
    if exception is not None:
        st.exception('Exception occured during conversion.')
        st.exception(exception)
        st.stop()
    elif pdf_file is None:
        st.error('Conversion failed. No PDF file was created.')
        st.stop()
    elif pdf_file.exists():
        st.success(f"Conversion successful!")
        pdf_bytes = get_bytes_from_file(pdf_file)

    if pdf_bytes is not None:
        st.markdown('''---''')
        st.subheader(f'Preview of converted PDF file "{pdf_file.name}"')
        pdf_bytes_base64 = get_base64_encoded_bytes(pdf_bytes)
        show_pdf_base64(pdf_bytes_base64)