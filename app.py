import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import math
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E TEMA (VERDE ZANCANARO & TEXTOS EM PRETO)
# ==========================================
st.set_page_config(
    page_title="Clube de Tiro Zancanaro - Gestão & Despachante",
    page_icon="🎯",
    layout="wide"
)

# Estilização CSS Customizada (Menu Lateral Estilizado como Botões)
st.markdown("""
<style>
    .stApp {
        background-color: #2e7d32;
        color: #000000;
    }
    h1, h2, h3, h4 {
        color: #0d3b11 !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
    }
    p, span, label, div {
        color: #000000 !important;
        font-weight: 500;
    }
    .stButton>button {
        background-color: #1b5e20;
        color: #ffffff !important;
        border: 1px solid #0d3b11;
        border-radius: 6px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0d3b11;
        color: #00FF66 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    /* Estilo para os botões do menu lateral */
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        text-align: left;
        background-color: #e8f5e9;
        color: #0d3b11 !important;
        border: 1px solid #c8e6c9;
        border-radius: 8px;
        margin-bottom: 6px;
        font-weight: bold;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #1b5e20;
        color: #ffffff !important;
    }
    .metric-card {
        background-color: #a5d6a7;
        border-left: 6px solid #1b5e20;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0d3b11 !important;
    }
    .metric-label {
        font-size: 13px;
        color: #1b5e20 !important;
        font-weight: bold;
    }
    .card-confirmacao {
        background-color: #a5d6a7;
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #1b5e20;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# Funções de Supabase para Clientes
def buscar_clientes_supabase():
    if supabase:
        try:
            res = supabase.table("clientes").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Erro ao buscar clientes: {e}")
    return pd.DataFrame(columns=["id", "nome", "cpf", "cr", "telefone", "cidade"])

def atualizar_cliente_supabase(cli_id, dados):
    if supabase:
        try:
            supabase.table("clientes").update(dados).eq("id", cli_id).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar cliente: {e}")

def excluir_cliente_supabase(cli_id):
    if supabase:
        try:
            supabase.table("clientes").delete().eq("id", cli_id).execute()
        except Exception as e:
            st.error(f"Erro ao excluir cliente: {e}")

# Funções de Supabase para Usuários
def buscar_usuarios_supabase():
    if supabase:
        try:
            res = supabase.table("usuarios").select("*").execute()
            if res.data:
                dic = {}
                for row in res.data:
                    dic[row["login"]] = {
                        "senha": row["senha"],
                        "nome": row["nome"],
                        "perfil": row["perfil"],
                        "gera_comissao": row["gera_comissao"]
                    }
                return dic
        except Exception as e:
            st.error(f"Erro ao buscar usuários: {e}")
    return {
        "Klaiton": {"senha": "134679", "nome": "Klaiton (Master)", "perfil": "Master", "gera_comissao": True}
    }

def atualizar_usuario_supabase(login_antigo, login_novo, dados):
    if supabase:
        try:
            if login_antigo != login_novo:
                supabase.table("usuarios").delete().eq("login", login_antigo).execute()
                supabase.table("usuarios").insert({"login": login_novo, **dados}).execute()
            else:
                supabase.table("usuarios").update(dados).eq("login", login_antigo).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar usuário: {e}")

def excluir_usuario_supabase(login):
    if supabase:
        try:
            supabase.table("usuarios").delete().eq("login", login).execute()
        except Exception as e:
            st.error(f"Erro ao excluir usuário: {e}")

# Funções de Supabase para Catálogo de Serviços
def buscar_servicos_supabase():
    if supabase:
        try:
            res = supabase.table("servicos_catalogo").select("*").execute()
            if res.data:
                return res.data
        except Exception as e:
            st.error(f"Erro ao buscar serviços: {e}")
    return [
        {"servico": "Concessão de CR", "comissao": 150.00},
        {"servico": "Renovação de CR", "comissao": 80.00},
        {"servico": "Apostilamento de PCE (Prensa/Dies)", "comissao": 100.00},
        {"servico": "Guia de Tráfego Eletrônica", "comissao": 40.00},
        {"servico": "Emissão / Renovação de GT (Fixo)", "comissao": 5.00},
        {"servico": "Transferência de Arma (SIGMA/SINARM)", "comissao": 120.00}
    ]

def salvar_servico_supabase(servico, comissao):
    if supabase:
        try:
            supabase.table("servicos_catalogo").insert({"servico": servico, "comissao": comissao}).execute()
        except Exception as e:
            st.error(f"Erro ao salvar serviço: {e}")

def atualizar_servico_supabase(servico_antigo, novo_servico, nova_comissao):
    if supabase:
        try:
            supabase.table("servicos_catalogo").update({"servico": novo_servico, "comissao": nova_comissao}).eq("servico", servico_antigo).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar serviço: {e}")

def excluir_servico_supabase(servico):
    if supabase:
        try:
            supabase.table("servicos_catalogo").delete().eq("servico", servico).execute()
        except Exception as e:
            st.error(f"Erro ao excluir serviço: {e}")

# Funções de Supabase para Guias de Tráfego
def buscar_guias_supabase():
    if supabase:
        try:
            res = supabase.table("guias_trafego").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                if "cidade" not in df.columns or df["cidade"].isnull().all():
                    df["cidade"] = "Abelardo Luz - SC"
                else:
                    df["cidade"] = df["cidade"].fillna("Abelardo Luz - SC")
                return df
        except Exception as e:
            st.error(f"Erro ao buscar guias: {e}")
    return pd.DataFrame(columns=["id", "cliente_nome", "cr", "equipamento", "validade", "telefone", "cidade"])

def salvar_guia_supabase(dados_guia):
    if supabase:
        try:
            supabase.table("guias_trafego").insert(dados_guia).execute()
        except Exception as e:
            st.error(f"Erro ao salvar guia: {e}")

def atualizar_guia_supabase(guia_id, dados):
    if supabase:
        try:
            supabase.table("guias_trafego").update(dados).eq("id", guia_id).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar guia: {e}")

def excluir_guia_supabase(guia_id):
    if supabase:
        try:
            supabase.table("guias_trafego").delete().eq("id", guia_id).execute()
        except Exception as e:
            st.error(f"Erro ao excluir guia: {e}")

# Funções de Supabase para Processos Lançados
def buscar_processos_supabase():
    if supabase:
        try:
            res = supabase.table("processos_lancados").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Erro ao buscar processos: {e}")
    return pd.DataFrame(columns=[
        "id", "colaborador", "cliente_nome", "cidade", "numero_processo", "servico", 
        "valor_comissao", "tipo_processo", "data_envio", "mes_referencia", "comissao_devida", "comprovante"
    ])

def salvar_processo_supabase(dados):
    if supabase:
        try:
            supabase.table("processos_lancados").insert(dados).execute()
        except Exception as e:
            st.error(f"Erro ao salvar processo: {e}")

# Funções de Supabase para Agenda
def buscar_agenda_supabase():
    if supabase:
        try:
            res = supabase.table("agenda_processos").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Erro ao buscar agenda: {e}")
    return pd.DataFrame(columns=[
        "id", "data_cadastro", "cliente_nome", "cidade", "despachante", "tipo_servico", "arma_equipamento", "status", "teste_psicologico", "teste_tiro"
    ])

def salvar_agenda_supabase(dados):
    if supabase:
        try:
            supabase.table("agenda_processos").insert(dados).execute()
        except Exception as e:
            st.error(f"Erro ao salvar agendamento: {e}")

def atualizar_status_agenda_supabase(ag_id, novo_status):
    if supabase:
        try:
            supabase.table("agenda_processos").update({"status": novo_status}).eq("id", ag_id).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar status da agenda: {e}")

def atualizar_agenda_supabase(ag_id, dados):
    if supabase:
        try:
            supabase.table("agenda_processos").update(dados).eq("id", ag_id).execute()
        except Exception as e:
            st.error(f"Erro ao atualizar agenda: {e}")

def excluir_agenda_supabase(ag_id):
    if supabase:
        try:
            supabase.table("agenda_processos").delete().eq("id", ag_id).execute()
        except Exception as e:
            st.error(f"Erro ao excluir agendamento: {e}")

# ==========================================
# CATÁLOGO DE SERVIÇOS & SESSÕES
# ==========================================
servicos_catalogo_atual = buscar_servicos_supabase()

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "menu_ativo" not in st.session_state:
    st.session_state.menu_ativo = "👤 Cadastro Único de Clientes"

# ==========================================
# TELA DE LOGIN
# ==========================================
usuarios_db_atual = buscar_usuarios_supabase()

if st.session_state.usuario_logado is None:
    st.markdown("<h1 style='text-align: center;'>🎯 CLUBE DE TIRO ZANCANARO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Abelardo Luz - SC | Sistema de Gestão & Despachante</h3>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário").strip()
            senha_input = st.text_input("Senha", type="password").strip()
            btn_entrar = st.form_submit_button("🔓 Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                if usuario_input in usuarios_db_atual and usuarios_db_atual[usuario_input]["senha"] == senha_input:
                    user_data = usuarios_db_atual[usuario_input].copy()
                    user_data["login_chave"] = usuario_input
                    st.session_state.usuario_logado = user_data
                    st.success(f"Bem-vindo, {user_data['nome']}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# PAINEL PRINCIPAL & MENU LATERAL
# ==========================================
user_info = st.session_state.usuario_logado
perfil = user_info["perfil"]
colaborador_atual = user_info["nome"]
login_atual = user_info["login_chave"]
gera_comissao_atual = user_info.get("gera_comissao", True)

with st.sidebar:
    st.markdown("### 🎯 ZANCANARO")
    tipo_comissao_txt = "Com Comissão" if gera_comissao_atual else "Sem Comissão"
    st.caption(f"Logado: **{user_info['nome']}**\nPerfil: **{perfil}** ({tipo_comissao_txt})\nAbelardo Luz - SC")
    st.divider()
    
    st.markdown("### 🗂️ Menu de Navegação")
    
    if st.button("👤 Cadastro de Clientes", use_container_width=True):
        st.session_state.menu_ativo = "👤 Cadastro Único de Clientes"
        st.rerun()
        
    if st.button("🏙️ Clientes por Cidade", use_container_width=True):
        st.session_state.menu_ativo = "🏙️ Clientes por Cidade"
        st.rerun()
        
    if st.button("💰 Comissões & Processos", use_container_width=True):
        st.session_state.menu_ativo = "💰 Gestão de Comissões & Processos"
        st.rerun()
        
    if st.button("📜 Guias de Tráfego", use_container_width=True):
        st.session_state.menu_ativo = "📜 Guias de Tráfego"
        st.rerun()
        
    if st.button("📅 Agenda & Processos", use_container_width=True):
        st.session_state.menu_ativo = "📅 Agenda & Processos a Fazer"
        st.rerun()
        
    if perfil in ["Master", "Gestor"]:
        if st.button("⚙️ Serviços & Equipe", use_container_width=True):
            st.session_state.menu_ativo = "⚙️ Serviços & Equipe"
            st.rerun()

        if st.button("📊 Relatórios Gerenciais", use_container_width=True):
            st.session_state.menu_ativo = "📊 Relatórios Gerenciais"
            st.rerun()
            
    st.divider()
    
    if st.button("🔑 Alterar Minha Senha", use_container_width=True):
        st.session_state.menu_ativo = "🔑 Alterar Minha Senha"
        st.rerun()

    if st.button("🚪 Sair / Logout", use_container_width=True):
        st.session_state.usuario_logado = None
        st.rerun()

menu_selecionado = st.session_state.menu_ativo

clientes_db_atual = buscar_clientes_supabase()
lista_nomes_clientes = sorted(clientes_db_atual["nome"].tolist()) if not clientes_db_atual.empty else []
lista_colaboradores = [u["nome"] for u in usuarios_db_atual.values() if u["perfil"] == "Colaborador"]
lista_todos_despachantes = [u["nome"] for u in usuarios_db_atual.values()]

# ------------------------------------------
# SEÇÃO 1: CADASTRO ÚNICO DE CLIENTES
# ------------------------------------------
if menu_selecionado == "👤 Cadastro Único de Clientes":
    st.header("👤 Cadastro Central de Clientes")
    
    with st.form("form_novo_cliente", clear_on_submit=True):
        c_nome = st.text_input("Nome Completo do Cliente")
        c_cpf = st.text_input("CPF")
        c_cr = st.text_input("Número do CR (se houver)")
        c_tel = st.text_input("WhatsApp / Telefone (ex: 5549999999999)")
        
        c_estado = st.selectbox("Estado (UF)", ["SC", "PR", "RS"])
        c_cidade_nome = st.text_input("Nome da Cidade")
        
        btn_salvar_cli = st.form_submit_button("💾 Salvar Cliente no Banco")
        
        if btn_salvar_cli:
            if c_nome and c_cidade_nome:
                dados_cliente = {
                    "nome": c_nome.strip(),
                    "cpf": c_cpf,
                    "cr": c_cr,
                    "telefone": c_tel,
                    "cidade": f"{c_cidade_nome.strip()} - {c_estado}"
                }
                if supabase:
                    try:
                        supabase.table("clientes").insert(dados_cliente).execute()
                        st.success(f"Cliente '{c_nome.strip()}' salvo com sucesso na nuvem!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar cliente: {e}")
            else:
                st.error("Preencha ao menos o Nome e a Cidade do cliente.")

# ------------------------------------------
# SEÇÃO 2: CLIENTES CADASTRADOS POR CIDADE
# ------------------------------------------
elif menu_selecionado == "🏙️ Clientes por Cidade":
    st.header("🏙️ Gestão de Clientes por Cidade")
    st.caption("Filtre por cidade ou busque por nome. Visualização limpa em linha única.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cidades_no_banco = sorted(clientes_db_atual["cidade"].unique().tolist()) if not clientes_db_atual.empty else []
        cidade_filtro = st.selectbox("🔍 Selecione a Cidade para Filtrar:", ["Todas as Cidades"] + cidades_no_banco)
    
    with col_f2:
        busca_nome = st.text_input("🔎 Buscar Cliente por Nome:").strip().lower()

    df_cidades = clientes_db_atual.copy() if not clientes_db_atual.empty else pd.DataFrame()
    
    if not df_cidades.empty:
        if cidade_filtro != "Todas as Cidades":
            df_cidades = df_cidades[df_cidades["cidade"] == cidade_filtro]
        
        if busca_nome:
            df_cidades = df_cidades[df_cidades["nome"].str.lower().str.contains(busca_nome)]
        
        df_cidades = df_cidades.sort_values(by="nome").reset_index(drop=True)
        
        total_registros = len(df_cidades)
        itens_por_pagina = 15
        num_paginas = math.ceil(total_registros / itens_por_pagina) if total_registros > 0 else 1

        c_info, c_pag = st.columns([3, 1])
        with c_info:
            st.markdown(f"##### Total de Clientes Encontrados: **{total_registros}**")
        with c_pag:
            pagina_atual = st.number_input("Página", min_value=1, max_value=max(1, num_paginas), value=1, step=1)
        
        idx_inicio = (pagina_atual - 1) * itens_por_pagina
        idx_fim = idx_inicio + itens_por_pagina
        df_pagina = df_cidades.iloc[idx_inicio:idx_fim]
        
        st.divider()
        
        if not df_pagina.empty:
            for _, cliente in df_pagina.iterrows():
                cli_id = cliente["id"]
                
                c_dados, c_ed, c_ex = st.columns([6, 1, 1])
                with c_dados:
                    st.markdown(f"""
                    <div style="background-color: #a5d6a7; padding: 8px 12px; border-radius: 6px; border-left: 5px solid #1b5e20; font-size: 13px;">
                        👤 <b>{cliente['nome']}</b> | CPF: {cliente['cpf'] if cliente['cpf'] else 'N/A'} | CR: {cliente['cr'] if cliente['cr'] else 'N/A'} | Tel: {cliente['telefone']} | 📍 <b>{cliente['cidade']}</b>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_ed:
                    if st.button("✏️ Editar", key=f"btn_edit_cli_{cli_id}", use_container_width=True):
                        st.session_state[f"editando_cli_{cli_id}"] = not st.session_state.get(f"editando_cli_{cli_id}", False)
                        st.rerun()
                        
                with c_ex:
                    if st.button("🗑️ Excluir", key=f"btn_excluir_cli_{cli_id}", use_container_width=True):
                        excluir_cliente_supabase(cli_id)
                        st.warning(f"Cliente '{cliente['nome']}' removido com sucesso!")
                        st.rerun()

                if st.session_state.get(f"editando_cli_{cli_id}", False):
                    with st.form(f"form_ed_cli_{cli_id}"):
                        st.markdown(f"##### ✏️ Editando Cliente: {cliente['nome']}")
                        
                        cidade_atual_partes = cliente["cidade"].split(" - ")
                        nome_cidade_antiga = cidade_atual_partes[0] if len(cidade_atual_partes) > 0 else cliente["cidade"]
                        estado_antigo = cidade_atual_partes[1] if len(cidade_atual_partes) > 1 else "SC"
                        idx_est = ["SC", "PR", "RS"].index(estado_antigo) if estado_antigo in ["SC", "PR", "RS"] else 0
                        
                        ed_nome = st.text_input("Nome", value=cliente["nome"], key=f"n_{cli_id}")
                        ed_cpf = st.text_input("CPF", value=cliente["cpf"], key=f"cpf_{cli_id}")
                        ed_cr = st.text_input("CR", value=cliente["cr"], key=f"cr_{cli_id}")
                        ed_tel = st.text_input("Telefone/WhatsApp", value=cliente["telefone"], key=f"tel_{cli_id}")
                        ed_estado = st.selectbox("Estado (UF)", ["SC", "PR", "RS"], index=idx_est, key=f"est_{cli_id}")
                        ed_cidade_nome = st.text_input("Nome da Cidade", value=nome_cidade_antiga, key=f"cid_{cli_id}")
                        
                        if st.form_submit_button("💾 Salvar Alterações"):
                            cidade_nova_completa = f"{ed_cidade_nome.strip()} - {ed_estado}"
                            atualizar_cliente_supabase(cli_id, {
                                "nome": ed_nome,
                                "cpf": ed_cpf,
                                "cr": ed_cr,
                                "telefone": ed_tel,
                                "cidade": cidade_nova_completa
                            })
                            st.session_state[f"editando_cli_{cli_id}"] = False
                            st.success("Dados atualizados com sucesso!")
                            st.rerun()
        else:
            st.info("Nenhum cliente encontrado.")
    else:
        st.info("Nenhum cliente cadastrado no sistema.")

# ------------------------------------------
# SEÇÃO 3: GESTÃO DE COMISSÕES E PROCESSOS
# ------------------------------------------
elif menu_selecionado == "💰 Gestão de Comissões & Processos":
    mes_atual = datetime.now().strftime("%Y-%m")
    df_proc = buscar_processos_supabase()
    
    # Formatar data_envio para dd/mm/aaaa na exibição se existir
    if not df_proc.empty and "data_envio" in df_proc.columns:
        df_proc["data_envio_fmt"] = pd.to_datetime(df_proc["data_envio"], errors='coerce').dt.strftime("%d/%m/%Y").fillna(df_proc["data_envio"])

    if perfil in ["Master", "Gestor"]:
        st.header(f"👑 Painel da Administração ({perfil}) - Controle de Comissões")
        st.subheader(f"1. Resumo da Equipe no Mês ({mes_atual})")
        
        df_mes = df_proc[df_proc["mes_referencia"] == mes_atual] if not df_proc.empty else df_proc
        
        colaboradores_com_comissao = [
            u["nome"] for u in usuarios_db_atual.values() 
            if u["perfil"] == "Colaborador" and u.get("gera_comissao", True)
        ]
        
        cols_colab = st.columns(len(colaboradores_com_comissao)) if len(colaboradores_com_comissao) > 0 else [st.container()]
        
        for idx, colab in enumerate(colaboradores_com_comissao):
            df_c = df_mes[df_mes["colaborador"] == colab] if not df_mes.empty else pd.DataFrame()
            total_proc = len(df_c)
            total_comissao = df_c["comissao_devida"].sum() if total_proc > 0 else 0.0
            
            with cols_colab[idx]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Colaborador</div>
                    <div style="font-size: 18px; font-weight: bold;">{colab}</div>
                    <hr style="border-color: #1b5e20; margin: 8px 0;">
                    <div class="metric-label">Processos no Mês: <b>{total_proc}</b></div>
                    <div class="metric-label">Comissão a Pagar:</div>
                    <div class="metric-value">R$ {total_comissao:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔍 Detalhar ({colab})", key=f"btn_{colab}"):
                    estado_atual = st.session_state.get(f"ver_{colab}", False)
                    for c_outro in colaboradores_com_comissao:
                        st.session_state[f"ver_{c_outro}"] = False
                    st.session_state[f"ver_{colab}"] = not estado_atual
                    st.rerun()
            
            if st.session_state.get(f"ver_{colab}", False):
                st.markdown(f"#### 📄 Processos do Mês de {colab}")
                if total_proc > 0:
                    df_exib_det = df_c.copy()
                    df_exib_det["Data Envio"] = df_exib_det["data_envio_fmt"]
                    st.dataframe(df_exib_det[["cliente_nome", "cidade", "numero_processo", "servico", "tipo_processo", "Data Envio", "comissao_devida"]], use_container_width=True)
                else:
                    st.info("Nenhum lançamento no mês para este colaborador.")

        st.divider()

    if perfil == "Colaborador":
        st.header(f"📌 Painel do Colaborador: {colaborador_atual}")
        df_meus_processos = df_proc[(df_proc["colaborador"] == colaborador_atual) & (df_proc["mes_referencia"] == mes_atual)] if not df_proc.empty else pd.DataFrame()
        
        if gera_comissao_atual:
            total_comissao_meu = df_meus_processos["comissao_devida"].sum() if not df_meus_processos.empty else 0.0
            c_mc1, c_mc2 = st.columns(2)
            with c_mc1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Sua Comissão Acumulada ({mes_atual})</div>
                    <div class="metric-value">R$ {total_comissao_meu:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with c_mc2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total de Processos Realizados</div>
                    <div class="metric-value">{len(df_meus_processos)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.subheader("📋 Seus Processos em Andamento / Concluídos no Mês")
            if not df_meus_processos.empty:
                df_meu_exib = df_meus_processos.copy()
                df_meu_exib["Data Envio"] = df_meu_exib["data_envio_fmt"]
                st.dataframe(df_meu_exib[["cliente_nome", "cidade", "numero_processo", "servico", "tipo_processo", "Data Envio", "comissao_devida"]], use_container_width=True)
            else:
                st.info("Nenhum processo registrado em seu nome neste mês.")
        else:
            c_mc1 = st.columns(1)[0]
            with c_mc1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total de Processos Realizados no Mês ({mes_atual})</div>
                    <div class="metric-value">{len(df_meus_processos)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.subheader("📋 Seus Processos Realizados no Mês")
            if not df_meus_processos.empty:
                df_meu_exib = df_meus_processos.copy()
                df_meu_exib["Data Envio"] = df_meu_exib["data_envio_fmt"]
                st.dataframe(df_meu_exib[["cliente_nome", "cidade", "numero_processo", "servico", "tipo_processo", "Data Envio"]], use_container_width=True)
            else:
                st.info("Nenhum processo registrado em seu nome neste mês.")
        st.divider()

    nome_painel_lancar = colaborador_atual if perfil == "Colaborador" else f"{colaborador_atual} (Atuação Master)"
    st.subheader(f"📝 Lançar Envio de Processo - {nome_painel_lancar}")
    
    if "temp_novo_processo" in st.session_state:
        tp = st.session_state.temp_novo_processo
        st.markdown(f"""
        <div class="card-confirmacao">
            <h3>⚠️ Confirmação de Lançamento de Processo</h3>
            <p>Cliente: <b>{tp['cliente_nome']}</b><br>
            Serviço: <b>{tp['servico']}</b><br>
            Nº Processo: <b>{tp['numero_processo']}</b><br>
            Data: <b>{tp['data_envio_exib']}</b><br>
            Colaborador: <b>{tp['colaborador']}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        col_mp1, col_mp2 = st.columns(2)
        with col_mp1:
            if st.button("✅ OK, Confirmar Lançamento", key="btn_conf_proc_ok", use_container_width=True):
                novo_p = {
                    "colaborador": tp["colaborador"],
                    "cliente_nome": tp["cliente_nome"],
                    "cidade": tp["cidade"],
                    "numero_processo": tp["numero_processo"],
                    "servico": tp["servico"],
                    "valor_comissao": tp["valor_comissao"],
                    "tipo_processo": tp["tipo_processo"],
                    "data_envio": tp["data_envio"],
                    "mes_referencia": tp["mes_referencia"],
                    "comissao_devida": tp["comissao_devida"],
                    "comprovante": tp["comprovante"]
                }
                salvar_processo_supabase(novo_p)
                
                if tp["id_agendamento"]:
                    atualizar_status_agenda_supabase(tp["id_agendamento"], "Concluído")
                
                del st.session_state.temp_novo_processo
                st.success("Processo registrado com sucesso na nuvem!")
                st.rerun()
        with col_mp2:
            if st.button("❌ Cancelar", key="btn_canc_proc_ok", use_container_width=True):
                del st.session_state.temp_novo_processo
                st.rerun()
        st.divider()

    df_ag = buscar_agenda_supabase()
    
    if not df_ag.empty:
        df_ag_sem_gt = df_ag[~df_ag["tipo_servico"].str.contains("Guia de Tráfego", case=False)]
    else:
        df_ag_sem_gt = pd.DataFrame()

    if perfil in ["Master", "Gestor"]:
        ag_pendentes = df_ag_sem_gt[df_ag_sem_gt["status"] == "A Fazer"] if not df_ag_sem_gt.empty else pd.DataFrame()
    else:
        ag_pendentes = df_ag_sem_gt[(df_ag_sem_gt["status"] == "A Fazer") & (df_ag_sem_gt["despachante"] == colaborador_atual)] if not df_ag_sem_gt.empty else pd.DataFrame()
    
    opcoes_agenda = ["--- Lançar Novo Processo sem Agendamento ---"]
    if not ag_pendentes.empty:
        for _, r in ag_pendentes.iterrows():
            opcoes_agenda.append(f"ID #{r['id']} - {r['cliente_nome']} ({r['tipo_servico']}) [Resp: {r['despachante']}]")
    
    ag_selecionada = st.selectbox("📌 Capturar Processo Pendente da Agenda:", opcoes_agenda)
    
    id_agendado_capturado = None
    cliente_pre = lista_nomes_clientes[0] if lista_nomes_clientes else ""
    servico_pre = ""
    travar_cliente = False
    
    if ag_selecionada != "--- Lançar Novo Processo sem Agendamento ---":
        id_agendado_capturado = int(ag_selecionada.split("ID #")[1].split(" -")[0])
        obj_ag = ag_pendentes[ag_pendentes["id"] == id_agendado_capturado].iloc[0]
        cliente_pre = obj_ag["cliente_nome"]
        servico_pre = obj_ag["tipo_servico"]
        travar_cliente = True
        st.warning(f"🔒 Processo agendado selecionado! O cliente ({cliente_pre}) está travado.")

    with st.form("form_lancar_proc", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            if perfil == "Master":
                opcoes_atribuicao = [colaborador_atual] + lista_colaboradores
                colaborador_responsavel = st.selectbox("Atribuir Processo para:", opcoes_atribuicao)
            else:
                colaborador_responsavel = colaborador_atual

            idx_cli = lista_nomes_clientes.index(cliente_pre) if cliente_pre in lista_nomes_clientes else 0
            cliente_sel_nome = st.selectbox(
                "Cliente", 
                lista_nomes_clientes if lista_nomes_clientes else ["Nenhum"], 
                index=idx_cli,
                disabled=travar_cliente
            )
            
            cliente_obj = clientes_db_atual[clientes_db_atual["nome"] == cliente_sel_nome]
            cidade_auto = cliente_obj["cidade"].values[0] if not cliente_obj.empty else "Abelardo Luz - SC"
            st.info(f"📍 Cidade: **{cidade_auto}**")
            numero_proc = st.text_input("Número do Processo (SISGCORP / PF)")
            
        with f2:
            nomes_servicos = [s["servico"] for s in servicos_catalogo_atual if "Guia de Tráfego" not in s["servico"]]
            idx_serv = nomes_servicos.index(servico_pre) if servico_pre in nomes_servicos else 0
            servico_sel = st.selectbox("Serviço Executado", nomes_servicos if nomes_servicos else ["Nenhum"], index=idx_serv)
            data_envio = st.date_input("Data do Envio", value=datetime.now())
            tipo_proc = st.radio("Tipo:", ["Novo Processo", "Correção de Problema Antigo"])
        
        print_comprovante = st.file_uploader("Cole/Anexe o Print da Tela do Processo Enviado", type=["png", "jpg", "jpeg"])
        
        btn_sub_proc = st.form_submit_button("🚀 Salvar e Marcar Agendamento como Feito")
        
        if btn_sub_proc:
            if cliente_sel_nome and numero_proc:
                info_resp = usuarios_db_atual.get(next((k for k, v in usuarios_db_atual.items() if v["nome"] == colaborador_responsavel), ""), {})
                colab_gera_comissao = info_resp.get("gera_comissao", True)
                
                valor_base = next((s["comissao"] for s in servicos_catalogo_atual if s["servico"] == servico_sel), 50.0)
                
                if colab_gera_comissao:
                    comissao_calc = valor_base if tipo_proc == "Novo Processo" else 0.0
                else:
                    valor_base = 0.0
                    comissao_calc = 0.0
                
                st.session_state.temp_novo_processo = {
                    "colaborador": colaborador_responsavel,
                    "cliente_nome": cliente_sel_nome,
                    "cidade": cidade_auto,
                    "numero_processo": numero_proc,
                    "servico": servico_sel,
                    "valor_comissao": valor_base,
                    "tipo_processo": tipo_proc,
                    "data_envio": data_envio.strftime("%d/%m/%Y"), # Salva no formato dd/mm/aaaa
                    "data_envio_exib": data_envio.strftime("%d/%m/%Y"),
                    "mes_referencia": data_envio.strftime("%Y-%m"),
                    "comissao_devida": comissao_calc,
                    "comprovante": "Anexado" if print_comprovante else "Não informado",
                    "id_agendamento": id_agendado_capturado
                }
                st.rerun()

# ------------------------------------------
# SEÇÃO 4: GUIAS DE TRÁFEGO (SEPARADAS POR CIDADES & COM EDIÇÃO/EXCLUSÃO)
# ------------------------------------------
elif menu_selecionado == "📜 Guias de Tráfego":
    st.header("📜 Emissão e Gestão de Guias de Tráfego")
    
    col_gt1, col_gt2 = st.columns([1.3, 2.7])
    
    with col_gt1:
        st.subheader("Emitir Nova Guia de Tráfego")
        
        if "temp_nova_gt" in st.session_state:
            tg = st.session_state.temp_nova_gt
            st.markdown(f"""
            <div class="card-confirmacao">
                <h3>⚠️ Confirmação de Emissão de Guia de Tráfego</h3>
                <p>Atirador: <b>{tg['cliente_nome']}</b><br>
                Arma: <b>{tg['equipamento']}</b><br>
                Validade: <b>{tg['validade_exib']}</b><br>
                Cidade: <b>{tg['cidade']}</b><br>
                Colaborador: <b>{tg['colaborador']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            col_mg1, col_mg2 = st.columns(2)
            with col_mg1:
                if st.button("✅ OK, Confirmar Emissão", key="btn_conf_gt_ok", use_container_width=True):
                    data_hoje_str = datetime.now().strftime("%d/%m/%Y")
                    mes_hoje_str = datetime.now().strftime("%Y-%m")
                    
                    dados_nova_gt_db = {
                        "cliente_nome": tg["cliente_nome"],
                        "cr": tg["cr"],
                        "equipamento": tg["equipamento"],
                        "validade": tg["validade"], # formato dd/mm/aaaa
                        "telefone": tg["telefone"],
                        "cidade": tg["cidade"]
                    }
                    salvar_guia_supabase(dados_nova_gt_db)
                    
                    info_resp_gt = usuarios_db_atual.get(next((k for k, v in usuarios_db_atual.items() if v["nome"] == tg["colaborador"]), ""), {})
                    colab_gt_com = info_resp_gt.get("gera_comissao", True)
                    val_gt_com = 5.00 if colab_gt_com else 0.00
                    
                    novo_proc_gt = {
                        "colaborador": tg["colaborador"],
                        "cliente_nome": tg["cliente_nome"],
                        "cidade": tg["cidade"],
                        "numero_processo": f"GT-{tg['equipamento'].split()[0] if tg['equipamento'] else 'GERADA'}",
                        "servico": "Emissão de Guia de Tráfego",
                        "valor_comissao": val_gt_com,
                        "tipo_processo": "Novo Processo",
                        "data_envio": data_hoje_str,
                        "mes_referencia": mes_hoje_str,
                        "comissao_devida": val_gt_com,
                        "comprovante": "Sistema (Fixo GT)"
                    }
                    salvar_processo_supabase(novo_proc_gt)

                    if tg["id_agendamento"]:
                        atualizar_status_agenda_supabase(tg["id_agendamento"], "Concluído")
                    
                    del st.session_state.temp_nova_gt
                    st.success("Guia de Tráfego salva com sucesso no banco online!")
                    st.rerun()
            with col_mg2:
                if st.button("❌ Cancelar", key="btn_canc_gt_ok", use_container_width=True):
                    del st.session_state.temp_nova_gt
                    st.rerun()
            st.divider()

        df_ag = buscar_agenda_supabase()
        if perfil in ["Master", "Gestor"]:
            ag_gts = df_ag[(df_ag["status"] == "A Fazer") & (df_ag["tipo_servico"].str.contains("Guia de Tráfego", case=False))] if not df_ag.empty else pd.DataFrame()
        else:
            ag_gts = df_ag[(df_ag["status"] == "A Fazer") & (df_ag["tipo_servico"].str.contains("Guia de Tráfego", case=False)) & (df_ag["despachante"] == colaborador_atual)] if not df_ag.empty else pd.DataFrame()
        
        opcoes_gt_ag = ["--- Emitir sem Capturar da Agenda ---"]
        if not ag_gts.empty:
            for _, r in ag_gts.iterrows():
                opcoes_gt_ag.append(f"ID #{r['id']} - {r['cliente_nome']} ({r['arma_equipamento']}) [Resp: {r['despachante']}]")
                
        gt_ag_sel = st.selectbox("🎯 Capturar Agendamento de Guia de Tráfego:", opcoes_gt_ag)
        
        id_gt_ag_capturado = None
        cliente_gt_pre = lista_nomes_clientes[0] if lista_nomes_clientes else ""
        arma_gt_pre = ""
        travar_cli_gt = False
        
        if gt_ag_sel != "--- Emitir sem Capturar da Agenda ---":
            id_gt_ag_capturado = int(gt_ag_sel.split("ID #")[1].split(" -")[0])
            obj_gt_ag = ag_gts[ag_gts["id"] == id_gt_ag_capturado].iloc[0]
            cliente_gt_pre = obj_gt_ag["cliente_nome"]
            arma_gt_pre = obj_gt_ag["arma_equipamento"]
            travar_cli_gt = True
            st.warning(f"🔒 Atirador {cliente_gt_pre} travado por ser agendamento da Agenda.")

        with st.form("form_emitir_gt", clear_on_submit=True):
            if perfil == "Master":
                colab_gt_ganhador = st.selectbox("Atribuir Responsável por GT a:", lista_todos_despachantes)
            else:
                colab_gt_ganhador = colaborador_atual

            idx_cli_gt = lista_nomes_clientes.index(cliente_gt_pre) if cliente_gt_pre in lista_nomes_clientes else 0
            gt_cliente = st.selectbox("Atirador / Cliente", lista_nomes_clientes if lista_nomes_clientes else ["Nenhum"], index=idx_cli_gt, disabled=travar_cli_gt)
            
            cr_obj = clientes_db_atual[clientes_db_atual["nome"] == gt_cliente]
            cr_auto = cr_obj["cr"].values[0] if not cr_obj.empty else ""
            tel_auto = cr_obj["telefone"].values[0] if not cr_obj.empty else "5549999999999"
            cidade_gt_auto = cr_obj["cidade"].values[0] if not cr_obj.empty else "Abelardo Luz - SC"
            
            st.text_input("CR do Atirador", value=cr_auto, disabled=True)
            st.info(f"📍 Cidade do Atirador: **{cidade_gt_auto}**")
            gt_arma = st.text_input("Equipamento / Calibre / Nº Série", value=arma_gt_pre)
            gt_validade = st.date_input("Validade da Guia", value=datetime.now() + timedelta(days=365))
            
            btn_sub_gt = st.form_submit_button("🚀 Emitir Guia de Tráfego")
            
            if btn_sub_gt:
                if gt_cliente:
                    st.session_state.temp_nova_gt = {
                        "cliente_nome": gt_cliente,
                        "cr": cr_auto,
                        "equipamento": gt_arma,
                        "validade": gt_validade.strftime("%d/%m/%Y"), # dd/mm/aaaa
                        "validade_exib": gt_validade.strftime("%d/%m/%Y"),
                        "telefone": tel_auto,
                        "cidade": cidade_gt_auto,
                        "colaborador": colab_gt_ganhador,
                        "id_agendamento": id_gt_ag_capturado
                    }
                    st.rerun()

    with col_gt2:
        st.subheader("📊 Painel de Guias por Cidade")
        
        df_gts = buscar_guias_supabase()
        
        if not df_gts.empty:
            cidades_gts = sorted(df_gts["cidade"].unique().tolist())
            cidade_gt_selecionada = st.selectbox("🏙️ Selecione a Cidade para ver as Guias:", cidades_gts)
            
            df_gts_cidade = df_gts[df_gts["cidade"] == cidade_gt_selecionada].copy()
            hoje = datetime.now().date()
            
            # Converter coluna validade (aceita formato dd/mm/aaaa ou aaaa-mm-dd)
            df_gts_cidade["validade_dt"] = pd.to_datetime(df_gts_cidade["validade"], format="%d/%m/%Y", errors="coerce")
            mask_iso = df_gts_cidade["validade_dt"].isna()
            if mask_iso.any():
                df_gts_cidade.loc[mask_iso, "validade_dt"] = pd.to_datetime(df_gts_cidade.loc[mask_iso, "validade"], errors="coerce")
            df_gts_cidade["validade_dt"] = df_gts_cidade["validade_dt"].dt.date
            
            gts_em_dia = df_gts_cidade[df_gts_cidade["validade_dt"] > (hoje + timedelta(days=15))]
            gts_a_vencer = df_gts_cidade[(df_gts_cidade["validade_dt"] >= hoje) & (df_gts_cidade["validade_dt"] <= (hoje + timedelta(days=15)))]
            gts_vencidas = df_gts_cidade[df_gts_cidade["validade_dt"] < hoje]
            
            tab_em_dia, tab_a_vencer, tab_vencidas = st.tabs([
                f"🟢 Em Dia ({len(gts_em_dia)})",
                f"🟡 A Vencer ({len(gts_a_vencer)})",
                f"🔴 Vencidas ({len(gts_vencidas)})"
            ])
            
            with tab_em_dia:
                if not gts_em_dia.empty:
                    for _, r in gts_em_dia.iterrows():
                        r_id = r["id"]
                        st.markdown(f"""
                        <div style="background-color: #c8e6c9; padding: 10px; border-radius: 6px; margin-bottom: 6px; border-left: 6px solid #2e7d32; font-size: 13px;">
                            <b>Atirador:</b> {r['cliente_nome']} | <b>CR:</b> {r['cr']}<br>
                            <b>Arma:</b> {r['equipamento']} | 📅 <b>Validade:</b> <span style="color: #1b5e20; font-weight: bold;">{r['validade']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_ed_g1, col_ed_g2 = st.columns(2)
                        with col_ed_g1:
                            if st.button("✏️ Editar Guia", key=f"btn_edit_gt_{r_id}", use_container_width=True):
                                st.session_state[f"editando_gt_{r_id}"] = not st.session_state.get(f"editando_gt_{r_id}", False)
                                st.rerun()
                        with col_ed_g2:
                            if st.button("🗑️ Excluir Guia", key=f"btn_exc_gt_{r_id}", use_container_width=True):
                                excluir_guia_supabase(r_id)
                                st.warning("Guia excluída com sucesso!")
                                st.rerun()

                        if st.session_state.get(f"editando_gt_{r_id}", False):
                            with st.form(f"form_ed_gt_{r_id}"):
                                novo_eq = st.text_input("Equipamento / Calibre", value=r["equipamento"])
                                # Tentar carregar data atual para o date_input
                                try:
                                    dt_val_atual = datetime.strptime(r["validade"], "%d/%m/%Y")
                                except:
                                    try:
                                        dt_val_atual = pd.to_datetime(r["validade"])
                                    except:
                                        dt_val_atual = datetime.now()
                                nova_val = st.date_input("Nova Validade", value=dt_val_atual)
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    atualizar_guia_supabase(r_id, {
                                        "equipamento": novo_eq,
                                        "validade": nova_val.strftime("%d/%m/%Y")
                                    })
                                    st.session_state[f"editando_gt_{r_id}"] = False
                                    st.success("Guia atualizada com sucesso!")
                                    st.rerun()
                        st.markdown("---")
                else:
                    st.info(f"Nenhuma guia em dia em {cidade_gt_selecionada}.")

            with tab_a_vencer:
                if not gts_a_vencer.empty:
                    for _, r in gts_a_vencer.iterrows():
                        r_id = r["id"]
                        msg_wpp = f"Olá {r['cliente_nome']}, sua Guia de Tráfego ({r['equipamento']}) vence em {r['validade']}. Favor entrar em contato com o Clube de Tiro Zancanaro para renovação."
                        link_wpp = f"https://api.whatsapp.com/send?phone={r['telefone']}&text={urllib.parse.quote(msg_wpp)}"
                        
                        st.markdown(f"""
                        <div style="background-color: #fff9c4; padding: 10px; border-radius: 6px; margin-bottom: 6px; border-left: 6px solid #fbc02d; font-size: 13px;">
                            <b>Atirador:</b> {r['cliente_nome']} | <b>CR:</b> {r['cr']}<br>
                            <b>Arma:</b> {r['equipamento']} | ⚠️ <b>Vence em breve:</b> <span style="color: #b78103; font-weight: bold;">{r['validade']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c_av1, c_av2, c_av3, c_av4 = st.columns([1.2, 1.2, 1, 1])
                        with c_av1:
                            st.markdown(f"<a href='{link_wpp}' target='_blank'><button style='width:100%; height:38px; background-color:#25D366; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;'>📲 WhatsApp</button></a>", unsafe_allow_html=True)
                        with c_av2:
                            dt_ren_av = st.date_input("Validade", value=datetime.now() + timedelta(days=365), key=f"dt_av_{r_id}")
                        with c_av3:
                            colab_ren_av = st.selectbox("Atribuir:", lista_todos_despachantes, key=f"colab_av_{r_id}")
                        with c_av4:
                            st.write("")
                            if st.button("🔄 Renovar", key=f"btn_ren_av_{r_id}", use_container_width=True):
                                nova_val_str = dt_ren_av.strftime("%d/%m/%Y")
                                atualizar_guia_supabase(r_id, {"validade": nova_val_str})
                                
                                info_resp_ren = usuarios_db_atual.get(next((k for k, v in usuarios_db_atual.items() if v["nome"] == colab_ren_av), ""), {})
                                com_ren_val = 5.00 if info_resp_ren.get("gera_comissao", True) else 0.00
                                
                                proc_ren = {
                                    "colaborador": colab_ren_av,
                                    "cliente_nome": r['cliente_nome'],
                                    "cidade": r['cidade'],
                                    "numero_processo": f"REN-GT-#{r_id}",
                                    "servico": "Renovação de Guia de Tráfego",
                                    "valor_comissao": com_ren_val,
                                    "tipo_processo": "Novo Processo",
                                    "data_envio": datetime.now().strftime("%d/%m/%Y"),
                                    "mes_referencia": datetime.now().strftime("%Y-%m"),
                                    "comissao_devida": com_ren_val,
                                    "comprovante": "Sistema (Renovação GT)"
                                }
                                salvar_processo_supabase(proc_ren)
                                st.success(f"Guia renovada com sucesso para {colab_ren_av}!")
                                st.rerun()
                        
                        col_ed_g1, col_ed_g2 = st.columns(2)
                        with col_ed_g1:
                            if st.button("✏️ Editar", key=f"btn_edit_gta_{r_id}", use_container_width=True):
                                st.session_state[f"editando_gt_{r_id}"] = not st.session_state.get(f"editando_gt_{r_id}", False)
                                st.rerun()
                        with col_ed_g2:
                            if st.button("🗑️ Excluir", key=f"btn_exc_gta_{r_id}", use_container_width=True):
                                excluir_guia_supabase(r_id)
                                st.warning("Guia excluída com sucesso!")
                                st.rerun()

                        if st.session_state.get(f"editando_gt_{r_id}", False):
                            with st.form(f"form_ed_gta_{r_id}"):
                                novo_eq = st.text_input("Equipamento / Calibre", value=r["equipamento"])
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    atualizar_guia_supabase(r_id, {"equipamento": novo_eq})
                                    st.session_state[f"editando_gt_{r_id}"] = False
                                    st.success("Guia atualizada com sucesso!")
                                    st.rerun()
                        st.markdown("---")
                else:
                    st.info(f"Nenhuma guia a vencer em {cidade_gt_selecionada}.")

            with tab_vencidas:
                if not gts_vencidas.empty:
                    for _, r in gts_vencidas.iterrows():
                        r_id = r["id"]
                        msg_wpp = f"Olá {r['cliente_nome']}, sua Guia de Tráfego ({r['equipamento']}) VENCEU em {r['validade']}. Precisamos providenciar a renovação urgente no Clube de Tiro Zancanaro."
                        link_wpp = f"https://api.whatsapp.com/send?phone={r['telefone']}&text={urllib.parse.quote(msg_wpp)}"
                        
                        st.markdown(f"""
                        <div style="background-color: #ffcdd2; padding: 10px; border-radius: 6px; margin-bottom: 6px; border-left: 6px solid #c62828; font-size: 13px;">
                            <b>Atirador:</b> {r['cliente_nome']} | <b>CR:</b> {r['cr']}<br>
                            <b>Arma:</b> {r['equipamento']} | 🔴 <b>VENCIDA EM:</b> <span style="color: #b71c1c; font-weight: bold;">{r['validade']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c_v1, c_v2, c_v3, c_v4 = st.columns([1.2, 1.2, 1, 1])
                        with c_v1:
                            st.markdown(f"<a href='{link_wpp}' target='_blank'><button style='width:100%; height:38px; background-color:#25D366; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;'>📲 WhatsApp</button></a>", unsafe_allow_html=True)
                        with c_v2:
                            dt_ren_v = st.date_input("Validade", value=datetime.now() + timedelta(days=365), key=f"dt_v_{r_id}")
                        with c_v3:
                            colab_ren_v = st.selectbox("Atribuir:", lista_todos_despachantes, key=f"colab_v_{r_id}")
                        with c_v4:
                            st.write("")
                            if st.button("🔄 Renovar", key=f"btn_ren_v_{r_id}", use_container_width=True):
                                nova_val_v_str = dt_ren_v.strftime("%d/%m/%Y")
                                atualizar_guia_supabase(r_id, {"validade": nova_val_v_str})
                                
                                info_resp_ren_v = usuarios_db_atual.get(next((k for k, v in usuarios_db_atual.items() if v["nome"] == colab_ren_v), ""), {})
                                com_ren_val_v = 5.00 if info_resp_ren_v.get("gera_comissao", True) else 0.00
                                
                                proc_ren = {
                                    "colaborador": colab_ren_v,
                                    "cliente_nome": r['cliente_nome'],
                                    "cidade": r['cidade'],
                                    "numero_processo": f"REN-GT-#{r_id}",
                                    "servico": "Renovação de Guia de Tráfego",
                                    "valor_comissao": com_ren_val_v,
                                    "tipo_processo": "Novo Processo",
                                    "data_envio": datetime.now().strftime("%d/%m/%Y"),
                                    "mes_referencia": datetime.now().strftime("%Y-%m"),
                                    "comissao_devida": com_ren_val_v,
                                    "comprovante": "Sistema (Renovação GT)"
                                }
                                salvar_processo_supabase(proc_ren)
                                st.success(f"Guia renovada com sucesso para {colab_ren_v}!")
                                st.rerun()

                        col_ed_g1, col_ed_g2 = st.columns(2)
                        with col_ed_g1:
                            if st.button("✏️ Editar", key=f"btn_edit_gtv_{r_id}", use_container_width=True):
                                st.session_state[f"editando_gt_{r_id}"] = not st.session_state.get(f"editando_gt_{r_id}", False)
                                st.rerun()
                        with col_ed_g2:
                            if st.button("🗑️ Excluir", key=f"btn_exc_gtv_{r_id}", use_container_width=True):
                                excluir_guia_supabase(r_id)
                                st.warning("Guia excluída com sucesso!")
                                st.rerun()

                        if st.session_state.get(f"editando_gt_{r_id}", False):
                            with st.form(f"form_ed_gtv_{r_id}"):
                                novo_eq = st.text_input("Equipamento / Calibre", value=r["equipamento"])
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    atualizar_guia_supabase(r_id, {"equipamento": novo_eq})
                                    st.session_state[f"editando_gt_{r_id}"] = False
                                    st.success("Guia atualizada com sucesso!")
                                    st.rerun()
                        st.markdown("---")
                else:
                    st.info(f"Nenhuma guia vencida em {cidade_gt_selecionada}.")
        else:
            st.info("Nenhuma Guia de Tráfego no sistema.")

# ------------------------------------------
# SEÇÃO 5: AGENDA DE PROCESSOS
# ------------------------------------------
elif menu_selecionado == "📅 Agenda & Processos a Fazer":
    st.header("📅 Agenda de Processos & Agendamentos")
    
    col_ag_form, col_ag_lists = st.columns([1.2, 2.8])
    
    with col_ag_form:
        st.subheader("➕ Agendar Novo Serviço")
        
        if "temp_novo_agendamento" in st.session_state:
            ta = st.session_state.temp_novo_agendamento
            st.markdown(f"""
            <div class="card-confirmacao">
                <h3>⚠️ Confirmação de Agendamento</h3>
                <p>Cliente: <b>{ta['cliente_nome']}</b><br>
                Serviço: <b>{ta['tipo_servico']}</b><br>
                Despachante: <b>{ta['despachante']}</b><br>
                Psicológico: <b>{ta['teste_psicologico']}</b> | Tiro: <b>{ta['teste_tiro']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            c_ma_esp1, col_ma1, col_ma2, c_ma_esp2 = st.columns([1, 1.2, 1.2, 1])
            with col_ma1:
                if st.button("✅ OK, Confirmar", key="btn_conf_ag_ok", use_container_width=True):
                    data_cadastro_hoje = datetime.now().strftime("%d/%m/%Y")
                    novo_ag = {
                        "data_cadastro": data_cadastro_hoje,
                        "cliente_nome": ta["cliente_nome"],
                        "cidade": ta["cidade"],
                        "despachante": ta["despachante"],
                        "tipo_servico": ta["tipo_servico"],
                        "arma_equipamento": ta["arma_equipamento"],
                        "status": "A Fazer",
                        "teste_psicologico": ta["teste_psicologico"],
                        "teste_tiro": ta["teste_tiro"]
                    }
                    salvar_agenda_supabase(novo_ag)
                    del st.session_state.temp_novo_agendamento
                    st.success("Agendamento adicionado aos processos A Fazer na nuvem!")
                    st.rerun()
            with col_ma2:
                if st.button("❌ Cancelar", key="btn_canc_ag_ok", use_container_width=True):
                    del st.session_state.temp_novo_agendamento
                    st.rerun()
            st.divider()

        with st.form("form_agenda", clear_on_submit=True):
            ag_cliente = st.selectbox("Selecione o Cliente", lista_nomes_clientes if lista_nomes_clientes else ["Nenhum cliente"])
            ag_desp = st.selectbox("Despachante Responsável", lista_todos_despachantes if lista_todos_despachantes else [colaborador_atual])
            
            nomes_serv = [s["servico"] for s in servicos_catalogo_atual]
            ag_servico = st.selectbox("Tipo de Serviço a ser Feito", nomes_serv if nomes_serv else ["Nenhum serviço"])
            ag_arma = st.text_input("Arma / Equipamento Vinculado")
            
            st.markdown("---")
            st.markdown("##### 🎯 Controle de Testes Obrigatórios")
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                ag_psi = st.checkbox("Teste Psicológico Feito?", value=False)
            with c_t2:
                ag_tiro = st.checkbox("Teste de Tiro Feito?", value=False)
            
            btn_sub_agenda = st.form_submit_button("🗓️ Confirmar Agendamento")
            
            if btn_sub_agenda:
                cli_info = clientes_db_atual[clientes_db_atual["nome"] == ag_cliente]
                cidade_cad_auto = cli_info["cidade"].values[0] if not cli_info.empty else "Abelardo Luz - SC"
                
                st.session_state.temp_novo_agendamento = {
                    "cliente_nome": ag_cliente,
                    "cidade": cidade_cad_auto,
                    "despachante": ag_desp,
                    "tipo_servico": ag_servico,
                    "arma_equipamento": ag_arma,
                    "teste_psicologico": "Sim" if ag_psi else "Não",
                    "teste_tiro": "Sim" if ag_tiro else "Não"
                }
                st.rerun()

    with col_ag_lists:
        tab_pendentes, tab_feitos = st.tabs(["⏳ Processos A Fazer (Pendentes)", "✅ Processos Feitos (Concluídos)"])
        
        df_ag = buscar_agenda_supabase()
        if not df_ag.empty and "data_cadastro" in df_ag.columns:
            df_ag["data_cadastro_fmt"] = pd.to_datetime(df_ag["data_cadastro"], errors='coerce').dt.strftime("%d/%m/%Y").fillna(df_ag["data_cadastro"])
        
        with tab_pendentes:
            st.markdown(f"##### 🎯 Fila de Serviços A Fazer (Visão: **{perfil}**)")
            df_a_fazer = df_ag[df_ag["status"] == "A Fazer"] if not df_ag.empty else pd.DataFrame()
            
            if not df_a_fazer.empty:
                if "cidade" not in df_a_fazer.columns:
                    df_a_fazer["cidade"] = "Abelardo Luz - SC"
                if "teste_psicologico" not in df_a_fazer.columns:
                    df_a_fazer["teste_psicologico"] = "Não"
                if "teste_tiro" not in df_a_fazer.columns:
                    df_a_fazer["teste_tiro"] = "Não"
                
                cidades_com_agendamentos = sorted(df_a_fazer["cidade"].unique().tolist())
                cidade_agenda_selecionada = st.selectbox(
                    "🏙️ Selecione a Cidade para Visualizar os Agendamentos:", 
                    cidades_com_agendamentos
                )
                
                df_filtrado_cidade = df_a_fazer[df_a_fazer["cidade"] == cidade_agenda_selecionada]
                
                st.markdown(f"#### 📋 Agendamentos em: **{cidade_agenda_selecionada}** ({len(df_filtrado_cidade)} pendentes)")
                
                if not df_filtrado_cidade.empty:
                    for _, r in df_filtrado_cidade.iterrows():
                        ag_id = r['id']
                        psi_status = r.get('teste_psicologico', 'Não')
                        tiro_status = r.get('teste_tiro', 'Não')
                        data_cad_exib = r.get('data_cadastro_fmt', r.get('data_cadastro', ''))
                        
                        col_info, col_c, col_e, col_x = st.columns([5, 1, 1, 1])
                        
                        with col_info:
                            st.markdown(f"""
                            <div style="background-color: #a5d6a7; padding: 8px 12px; border-radius: 6px; border-left: 5px solid #1b5e20; font-size: 13px;">
                                📅 <b>{data_cad_exib}</b> | 👤 <b>{r['cliente_nome']}</b> | 🎯 {r['tipo_servico']} | 🔫 {r['arma_equipamento'] if r['arma_equipamento'] else 'N/A'}<br>
                                🧠 Psicológico: <b>{psi_status}</b> | 🎯 Teste de Tiro: <b>{tiro_status}</b> | 👨‍💼 <b>{r['despachante']}</b>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_c:
                            if st.button("✅ Concluir", key=f"btn_concluir_{ag_id}", use_container_width=True):
                                atualizar_status_agenda_supabase(ag_id, "Concluído")
                                st.success(f"Processo de {r['cliente_nome']} concluído!")
                                st.rerun()
                                    
                        with col_e:
                            if st.button("✏️ Editar", key=f"btn_edit_abrir_{ag_id}", use_container_width=True):
                                st.session_state[f"editando_agenda_{ag_id}"] = not st.session_state.get(f"editando_agenda_{ag_id}", False)
                                st.rerun()
                                
                        with col_x:
                            if st.button("🗑️ Excluir", key=f"btn_exc_{ag_id}", use_container_width=True):
                                excluir_agenda_supabase(ag_id)
                                st.warning(f"Agendamento de {r['cliente_nome']} excluído!")
                                st.rerun()

                        if st.session_state.get(f"editando_agenda_{ag_id}", False):
                            with st.form(f"form_editar_linha_{ag_id}"):
                                st.markdown(f"##### ✏️ Editando Agendamento ID #{ag_id} ({r['cliente_nome']})")
                                
                                idx_cli_ed = lista_nomes_clientes.index(r["cliente_nome"]) if r["cliente_nome"] in lista_nomes_clientes else 0
                                e_cli = st.selectbox("Cliente", lista_nomes_clientes if lista_nomes_clientes else ["Nenhum"], index=idx_cli_ed, key=f"e_cli_{ag_id}")
                                
                                idx_desp_ed = lista_todos_despachantes.index(r["despachante"]) if r["despachante"] in lista_todos_despachantes else 0
                                e_desp = st.selectbox("Despachante Responsável", lista_todos_despachantes if lista_todos_despachantes else [colaborador_atual], index=idx_desp_ed, key=f"e_desp_{ag_id}")
                                
                                nomes_s_ed = [s["servico"] for s in servicos_catalogo_atual]
                                idx_s_ed = nomes_s_ed.index(r["tipo_servico"]) if r["tipo_servico"] in nomes_s_ed else 0
                                e_serv = st.selectbox("Tipo de Serviço", nomes_s_ed, index=idx_s_ed, key=f"e_serv_{ag_id}")
                                
                                e_arma = st.text_input("Arma / Equipamento", value=r["arma_equipamento"], key=f"e_arma_{ag_id}")
                                
                                st.markdown("---")
                                st.markdown("##### 🎯 Controle de Testes Obrigatórios")
                                val_psi_bool = True if str(r.get("teste_psicologico", "Não")).strip().lower() == "sim" else False
                                val_tiro_bool = True if str(r.get("teste_tiro", "Não")).strip().lower() == "sim" else False
                                
                                c_ed_t1, c_ed_t2 = st.columns(2)
                                with c_ed_t1:
                                    e_psi = st.checkbox("🧠 Teste Psicológico Feito?", value=val_psi_bool, key=f"e_psi_{ag_id}")
                                with c_ed_t2:
                                    e_tiro = st.checkbox("🎯 Teste de Tiro Feito?", value=val_tiro_bool, key=f"e_tiro_{ag_id}")
                                
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    cli_inf_ed = clientes_db_atual[clientes_db_atual["nome"] == e_cli]
                                    nova_cid_ed = cli_inf_ed["cidade"].values[0] if not cli_inf_ed.empty else "Abelardo Luz - SC"
                                    
                                    atualizar_agenda_supabase(ag_id, {
                                        "cliente_nome": e_cli,
                                        "cidade": nova_cid_ed,
                                        "despachante": e_desp,
                                        "tipo_servico": e_serv,
                                        "arma_equipamento": e_arma,
                                        "teste_psicologico": "Sim" if e_psi else "Não",
                                        "teste_tiro": "Sim" if e_tiro else "Não"
                                    })
                                    st.session_state[f"editando_agenda_{ag_id}"] = False
                                    st.success("Agendamento atualizado com sucesso na nuvem!")
                                    st.rerun()
                else:
                    st.info(f"Nenhum agendamento pendente em {cidade_agenda_selecionada}.")
            else:
                st.info("Nenhum processo pendente na fila.")

        with tab_feitos:
            df_feitos = df_ag[df_ag["status"] == "Concluído"] if not df_ag.empty else pd.DataFrame()
            if "cidade" not in df_feitos.columns and not df_feitos.empty:
                df_feitos["cidade"] = "Abelardo Luz - SC"

            if not df_feitos.empty:
                df_feitos_exib = df_feitos.copy()
                df_feitos_exib["Data de Cadastro"] = df_feitos_exib["data_cadastro_fmt"]
                colunas_exibicao = ["Data de Cadastro", "cliente_nome", "cidade", "despachante", "tipo_servico", "arma_equipamento", "teste_psicologico", "teste_tiro"]
                renomear_colunas = {
                    "cliente_nome": "Nome do Cliente",
                    "cidade": "Cidade",
                    "despachante": "Despachante",
                    "tipo_servico": "Tipo de Serviço",
                    "arma_equipamento": "Arma",
                    "teste_psicologico": "Psicológico Feito",
                    "teste_tiro": "Teste de Tiro Feito"
                }
                df_exibir_f = df_feitos_exib[colunas_exibicao].rename(columns=renomear_colunas)
                st.dataframe(df_exibir_f, use_container_width=True)
            else:
                st.info("Nenhum processo concluído no histórico.")

# ------------------------------------------
# SEÇÃO 6: ALTERAR MINHA SENHA
# ------------------------------------------
elif menu_selecionado == "🔑 Alterar Minha Senha":
    st.header("🔑 Alterar Minha Senha de Acesso")
    st.caption(f"Usuário logado: **{user_info['nome']}** (`{login_atual}`)")
    
    col_ps1, col_ps2, col_ps3 = st.columns([1, 2, 1])
    with col_ps2:
        with st.form("form_mudar_propria_senha"):
            senha_atual_input = st.text_input("Digite sua Senha Atual", type="password")
            nova_senha_input = st.text_input("Digite a Nova Senha", type="password")
            confirma_nova_senha = st.text_input("Confirme a Nova Senha", type="password")
            
            btn_salvar_senha = st.form_submit_button("💾 Atualizar Minha Senha", use_container_width=True)
            
            if btn_salvar_senha:
                if login_atual in usuarios_db_atual:
                    if usuarios_db_atual[login_atual]["senha"] == senha_atual_input:
                        if nova_senha_input and nova_senha_input == confirma_nova_senha:
                            dados_atuais = usuarios_db_atual[login_atual]
                            dados_atuais["senha"] = nova_senha_input
                            atualizar_usuario_supabase(login_atual, login_atual, dados_atuais)
                            st.session_state.usuario_logado["senha"] = nova_senha_input
                            st.success("Sua senha foi alterada com sucesso na nuvem!")
                        else:
                            st.error("A nova senha e a confirmação não coincidem ou estão vazias.")
                    else:
                        st.error("A senha atual informada está incorreta.")
                else:
                    st.error("Erro de identificação do usuário.")

# ------------------------------------------
# SEÇÃO 7: SERVIÇOS & EQUIPE (ADMINISTRAÇÃO)
# ------------------------------------------
elif menu_selecionado == "⚙️ Serviços & Equipe" and perfil in ["Master", "Gestor"]:
    st.header("⚙️ Administração de Serviços e Equipe")
    st.caption("Gerencie o catálogo de serviços/comissões (compartilhado na nuvem) e a equipe.")
    
    sub_tab1, sub_tab2 = st.tabs(["⚙️ Catálogo de Serviços", "👥 Gestão de Equipe (Gestores e Colaboradores)"])
    
    with sub_tab1:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("##### ➕ Criar Novo Serviço")
            with st.form("form_add_servico", clear_on_submit=True):
                n_serv = st.text_input("Nome do Serviço")
                v_com = st.number_input("Valor da Comissão (R$)", min_value=0.0, value=50.0, step=10.0)
                if st.form_submit_button("Adicionar Serviço"):
                    if n_serv:
                        salvar_servico_supabase(n_serv.strip(), v_com)
                        st.success(f"Serviço '{n_serv}' cadastrado na nuvem!")
                        st.rerun()

        with col_s2:
            st.markdown("##### ✏️ Editar / ❌ Excluir Serviço")
            if servicos_catalogo_atual:
                lista_s_nomes = [s["servico"] for s in servicos_catalogo_atual]
                serv_selecionado = st.selectbox("Selecione o Serviço", lista_s_nomes)
                idx_s = next((i for i, item in enumerate(servicos_catalogo_atual) if item["servico"] == serv_selecionado), None)
                if idx_s is not None:
                    serv_obj = servicos_catalogo_atual[idx_s]
                    novo_nome_s = st.text_input("Editar Nome", value=serv_obj["servico"])
                    novo_val_s = st.number_input("Editar Comissão (R$)", value=float(serv_obj["comissao"]), min_value=0.0, step=10.0)
                    col_btn_ed, col_btn_ex = st.columns(2)
                    with col_btn_ed:
                        if st.button("💾 Salvar Alterações"):
                            atualizar_servico_supabase(serv_obj["servico"], novo_nome_s.strip(), novo_val_s)
                            st.success("Serviço e comissão atualizados na nuvem para todos!")
                            st.rerun()
                    with col_btn_ex:
                        if st.button("❌ Excluir Serviço"):
                            excluir_servico_supabase(serv_obj["servico"])
                            st.warning("Serviço removido!")
                            st.rerun()
        st.divider()
        st.dataframe(pd.DataFrame(servicos_catalogo_atual), use_container_width=True)

    with sub_tab2:
        st.markdown("##### 👥 Cadastro e Gerenciamento de Usuários (Nuvem)")
        
        with st.form("form_novo_usuario", clear_on_submit=True):
            st.markdown("###### Adicionar Novo Colaborador ou Gestor")
            nu_user = st.text_input("Login (Usuário)")
            nu_nome = st.text_input("Nome Completo")
            nu_senha = st.text_input("Senha", type="password")
            
            perfis_cadastro = ["Colaborador", "Gestor"]
            if perfil == "Master":
                perfis_cadastro.append("Master")
            nu_perfil = st.selectbox("Perfil de Acesso", perfis_cadastro)
            nu_gera_com = st.checkbox("Gera Comissões Financeiras?", value=True)
            
            btn_cad_usuario = st.form_submit_button("Cadastrar Usuário")
            
            if btn_cad_usuario:
                if nu_user and nu_nome and nu_senha:
                    if nu_user.strip() in usuarios_db_atual:
                        st.error("Este login já existe.")
                    else:
                        payload_usuario = {
                            "login": nu_user.strip(),
                            "senha": nu_senha,
                            "nome": nu_nome,
                            "perfil": nu_perfil,
                            "gera_comissao": nu_gera_com
                        }
                        if supabase:
                            try:
                                supabase.table("usuarios").insert(payload_usuario).execute()
                                st.success(f"Usuário {nu_nome} cadastrado com sucesso na nuvem!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar usuário: {e}")
                else:
                    st.error("Preencha todos os campos obrigatórios.")
        
        st.divider()
        st.markdown("###### 📋 Lista de Usuários Cadastrados (Editar Login/Senha / Excluir)")
        
        for login_k, u_val in list(usuarios_db_atual.items()):
            if perfil == "Gestor" and u_val["perfil"] == "Master":
                continue
                
            c_u1, c_u2, c_u3 = st.columns([4, 1, 1])
            with c_u1:
                comissao_status = "Com Comissão" if u_val.get("gera_comissao", True) else "Sem Comissão"
                st.markdown(f"👤 **{u_val['nome']}** | Login: `{login_k}` | Perfil: **{u_val['perfil']}** | {comissao_status}")
            with c_u2:
                if st.button("✏️ Editar", key=f"btn_edit_u_{login_k}"):
                    st.session_state[f"edit_u_{login_k}"] = not st.session_state.get(f"edit_u_{login_k}", False)
                    st.rerun()
            with c_u3:
                if login_k != login_atual:
                    if st.button("🗑️ Excluir", key=f"btn_exc_u_{login_k}"):
                        excluir_usuario_supabase(login_k)
                        st.warning(f"Usuário {u_val['nome']} removido!")
                        st.rerun()
                else:
                    st.caption("Você")

            if st.session_state.get(f"edit_u_{login_k}", False):
                with st.form(f"form_ed_u_{login_k}"):
                    st.markdown(f"**Editando Usuário: {u_val['nome']}**")
                    
                    ed_novo_login = st.text_input("Alterar Login (Usuário)", value=login_k, key=f"ed_login_{login_k}")
                    ed_u_nome = st.text_input("Nome Completo", value=u_val["nome"], key=f"ed_nome_{login_k}")
                    ed_u_senha = st.text_input("Senha", value=u_val["senha"], type="password", key=f"ed_senha_{login_k}")
                    
                    perfis_op = ["Colaborador", "Gestor"]
                    if perfil == "Master":
                        perfis_op.append("Master")
                    
                    idx_p = perfis_op.index(u_val["perfil"]) if u_val["perfil"] in perfis_op else 0
                    ed_u_perfil = st.selectbox("Perfil", perfis_op, index=idx_p, key=f"ed_perf_{login_k}")
                    ed_u_com = st.checkbox("Gera Comissões?", value=u_val.get("gera_comissao", True), key=f"ed_com_{login_k}")
                    
                    if st.form_submit_button("💾 Salvar Alterações"):
                        ed_novo_login_limpo = ed_novo_login.strip()
                        if not ed_novo_login_limpo:
                            st.error("O login não pode ficar vazio.")
                        elif ed_novo_login_limpo != login_k and ed_novo_login_limpo in usuarios_db_atual:
                            st.error("Este novo login já está sendo usado por outro usuário.")
                        else:
                            atualizar_usuario_supabase(login_k, ed_novo_login_limpo, {
                                "senha": ed_u_senha,
                                "nome": ed_u_nome,
                                "perfil": ed_u_perfil,
                                "gera_comissao": ed_u_com
                            })
                            st.session_state[f"edit_u_{login_k}"] = False
                            st.success("Dados do usuário atualizados com sucesso na nuvem!")
                            st.rerun()
            st.markdown("---")

# ------------------------------------------
# SEÇÃO 8: RELATÓRIOS GERENCIAIS
# ------------------------------------------
elif menu_selecionado == "📊 Relatórios Gerenciais" and perfil in ["Master", "Gestor"]:
    st.header("📊 Relatórios Gerenciais e de Comissões")
    st.caption("Visão consolidada para auditoria de pagamentos, desempenho de colaboradores e movimentação por cidade.")
    
    df_proc_rel = buscar_processos_supabase()
    
    if not df_proc_rel.empty:
        # Extrair ano da data de envio (lidando com dd/mm/aaaa ou aaaa-mm-dd)
        def extrair_ano(val):
            val_str = str(val)
            if "/" in val_str:
                partes = val_str.split("/")
                if len(partes) == 3:
                    return partes[2]
            elif "-" in val_str:
                return val_str.split("-")[0]
            return "2026"

        df_proc_rel["ano"] = df_proc_rel["data_envio"].apply(extrair_ano)
        if "data_envio" in df_proc_rel.columns:
            df_proc_rel["data_envio_fmt"] = pd.to_datetime(df_proc_rel["data_envio"], errors='coerce').dt.strftime("%d/%m/%Y").fillna(df_proc_rel["data_envio"])
        
        col_rf1, col_rf2, col_rf3, col_rf4 = st.columns(4)
        with col_rf1:
            anos_disponiveis = sorted(df_proc_rel["ano"].unique().tolist(), reverse=True)
            ano_escolhido = st.selectbox("📅 Filtrar por Ano:", ["Todos os Anos"] + anos_disponiveis)
        with col_rf2:
            meses_disponiveis = sorted(df_proc_rel["mes_referencia"].unique().tolist(), reverse=True)
            mes_escolhido = st.selectbox("📆 Filtrar por Mês:", ["Todos os Meses"] + meses_disponiveis)
        with col_rf3:
            cidades_disponiveis = sorted(df_proc_rel["cidade"].unique().tolist())
            cidade_escolhida = st.selectbox("🏙️ Filtrar por Cidade:", ["Todas as Cidades"] + cidades_disponiveis)
        with col_rf4:
            colaboradores_disponiveis = sorted(df_proc_rel["colaborador"].unique().tolist())
            colaborador_escolhido = st.selectbox("👤 Filtrar por Colaborador:", ["Todos os Colaboradores"] + colaboradores_disponiveis)
        
        df_filtrado = df_proc_rel
        if ano_escolhido != "Todos os Anos":
            df_filtrado = df_filtrado[df_filtrado["ano"] == ano_escolhido]
        if mes_escolhido != "Todos os Meses":
            df_filtrado = df_filtrado[df_filtrado["mes_referencia"] == mes_escolhido]
        if cidade_escolhida != "Todas as Cidades":
            df_filtrado = df_filtrado[df_filtrado["cidade"] == cidade_escolhida]
        if colaborador_escolhido != "Todos os Colaboradores":
            df_filtrado = df_filtrado[df_filtrado["colaborador"] == colaborador_escolhido]
        
        st.divider()
        
        total_processos_filtro = len(df_filtrado)
        total_comissao_filtro = df_filtrado["comissao_devida"].sum() if total_processos_filtro > 0 else 0.0
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total de Processos no Período</div>
                <div class="metric-value">{total_processos_filtro}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Pago em Comissões no Período</div>
                <div class="metric-value">R$ {total_comissao_filtro:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("👥 Relatório de Produção por Colaborador")
        if not df_filtrado.empty:
            resumo_colab = df_filtrado.groupby("colaborador").agg(
                Total_Processos=("id", "count"),
                Comissao_Total=("comissao_devida", "sum")
            ).reset_index()
            resumo_colab["Comissao_Total"] = resumo_colab["Comissao_Total"].apply(lambda x: f"R$ {x:.2f}")
            resumo_colab.columns = ["Colaborador", "Total de Processos", "Comissão Total Devida"]
            st.dataframe(resumo_colab, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
        
        st.subheader("🏙️ Relatório por Cidade")
        if not df_filtrado.empty:
            resumo_cidade = df_filtrado.groupby("cidade").agg(
                Total_Processos=("id", "count"),
                Comiss_Movimentada=("comissao_devida", "sum")
            ).reset_index()
            resumo_cidade["Comiss_Movimentada"] = resumo_cidade["Comiss_Movimentada"].apply(lambda x: f"R$ {x:.2f}")
            resumo_cidade.columns = ["Cidade", "Total de Processos", "Valor Total Movimentado"]
            st.dataframe(resumo_cidade, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
            
        st.subheader("📄 Listagem Detalhada dos Processos Filtrados")
        if not df_filtrado.empty:
            df_rel_exib = df_filtrado.copy()
            df_rel_exib["Data Envio"] = df_rel_exib["data_envio_fmt"]
            st.dataframe(df_rel_exib[["Data Envio", "colaborador", "cliente_nome", "cidade", "numero_processo", "servico", "tipo_processo", "comissao_devida"]], use_container_width=True)
        else:
            st.info("Nenhum processo na listagem detalhada.")
    else:
        st.info("Nenhum processo lançado no sistema para gerar relatórios.")
