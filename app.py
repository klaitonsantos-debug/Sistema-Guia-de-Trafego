import datetime
import urllib.parse
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from streamlit_option_menu import option_menu

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E BANCO DE DADOS
# ==========================================
st.set_page_config(
    page_title="Gestão de Guias de Tráfego",
    page_icon="🛡️",
    layout="wide"
)

# Conexão automática com o Supabase usando as Secrets do Streamlit
@st.cache_resource
def obter_engine():
    try:
        db_url = st.secrets["postgres"]["url"]
        return create_engine(db_url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Erro ao ler as Secrets da base de dados: {e}")
        st.stop()

engine = obter_engine()

def criar_tabelas():
    try:
        with engine.begin() as conn:
            # Tabela de Usuários
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    usuario VARCHAR(100) UNIQUE NOT NULL,
                    senha VARCHAR(100) NOT NULL,
                    perfil VARCHAR(20) DEFAULT 'operador'
                );
            """))
            
            # Tabela de Clientes
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(150) NOT NULL,
                    cpf VARCHAR(20) UNIQUE NOT NULL,
                    cr VARCHAR(50),
                    telefone VARCHAR(30) NOT NULL
                );
            """))
            
            # Tabela de Guias de Tráfego (GTs)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS guias (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                    numero_gt VARCHAR(50) NOT NULL,
                    arma_descricao TEXT NOT NULL,
                    calibre VARCHAR(30),
                    data_vencimento DATE NOT NULL,
                    status VARCHAR(20) DEFAULT 'Ativa'
                );
            """))
            
            # Usuário Padrão Master
            res = conn.execute(text("SELECT * FROM usuarios WHERE usuario = 'Klaiton';")).fetchone()
            if not res:
                conn.execute(text("INSERT INTO usuarios (usuario, senha, perfil) VALUES ('Klaiton', '134679', 'master');"))
    except Exception as err:
        st.error(f"❌ Não foi possível conectar ao banco de dados Supabase. Verifique a URL e a Senha nas Secrets do Streamlit.\n\nDetalhes do erro: {err}")
        st.stop()

criar_tabelas()

# ==========================================
# 2. SISTEMA DE AUTENTICAÇÃO (LOGIN)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None
if "perfil_logado" not in st.session_state:
    st.session_state["perfil_logado"] = None

def realizar_login(usuario, senha):
    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT usuario, perfil FROM usuarios WHERE usuario = :u AND senha = :s;"),
            {"u": usuario, "s": senha}
        ).fetchone()
        return res

if not st.session_state["autenticado"]:
    st.title("🔒 Acesso ao Sistema de GTs")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar")
            
            if botao_login:
                dados_usuario = realizar_login(usuario_input, senha_input)
                if dados_usuario:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = dados_usuario[0]
                    st.session_state["perfil_logado"] = dados_usuario[1]
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# 3. INTERFACE PRINCIPAL & MENU NAVEGAÇÃO
# ==========================================
with st.sidebar:
    st.markdown("### 🛡️ **Painel de Controle**")
    st.caption(f"👤 Usuário: **{st.session_state['usuario_logado']}** | 🔰 **{st.session_state['perfil_logado'].upper()}**")
    st.divider()

    opcoes = ["Dashboard", "Cadastrar Cliente", "Gerenciar Clientes", "Cadastrar Guia (GT)", "Consultar & Alertas"]
    icones = ["speedometer2", "person-plus", "people", "file-earmark-plus", "search"]

    if st.session_state["perfil_logado"] == "master":
        opcoes.append("Gerenciar Usuários")
        icones.append("gear")

    opcao = option_menu(
        menu_title="Navegação",
        options=opcoes,
        icons=icones,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#fafafa"},
            "icon": {"color": "#1f77b4", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "2px",
                "--hover-color": "#e2e8f0",
            },
            "nav-link-selected": {"background-color": "#1f77b4", "color": "white"},
        },
    )

    st.divider()
    if st.button("🚪 Sair / Logout", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = None
        st.session_state["perfil_logado"] = None
        st.rerun()

# ------------------------------------------
# ABA: DASHBOARD
# ------------------------------------------
if opcao == "Dashboard":
    st.title("📊 Painel Geral de Guias de Tráfego")
    
    today = datetime.date.today()
    alerta_15 = today + datetime.timedelta(days=15)
    
    with engine.connect() as conn:
        guias_em_dia = conn.execute(text("SELECT COUNT(*) FROM guias WHERE data_vencimento > :a AND status = 'Ativa';"), {"a": alerta_15}).fetchone()[0]
        guias_a_vencer = conn.execute(text("SELECT COUNT(*) FROM guias WHERE data_vencimento >= :t AND data_vencimento <= :a AND status = 'Ativa';"), {"t": today, "a": alerta_15}).fetchone()[0]
        guias_vencidas = conn.execute(text("SELECT COUNT(*) FROM guias WHERE data_vencimento < :t AND status = 'Ativa';"), {"t": today}).fetchone()[0]
        total_clientes = conn.execute(text("SELECT COUNT(*) FROM clientes;")).fetchone()[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Guias Em Dia", guias_em_dia)
    c2.metric("⚠️ A Vencer (15 dias)", guias_a_vencer)
    c3.metric("🚨 GTs Vencidas", guias_vencidas)
    c4.metric("👥 Total de Clientes", total_clientes)

# ------------------------------------------
# ABA: CADASTRAR CLIENTE
# ------------------------------------------
elif opcao == "Cadastrar Cliente":
    st.title("👤 Cadastro de Atirador / Cliente")
    
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf = st.text_input("CPF (Somente números)")
        cr = st.text_input("Número do CR (Opcional)")
        telefone = st.text_input("Telefone/WhatsApp (Ex: 5549999999999)")
        
        salvar = st.form_submit_button("Salvar Cliente")
        
        if salvar:
            if nome and cpf and telefone:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO clientes (nome, cpf, cr, telefone) VALUES (:n, :c, :r, :t);"),
                            {"n": nome, "c": cpf, "r": cr, "t": telefone}
                        )
                    st.success(f"Cliente {nome} cadastrado com sucesso!")
                except Exception:
                    st.error("Erro ao salvar: CPF já cadastrado ou dados inválidos.")
            else:
                st.warning("Preencha todos os campos obrigatórios (Nome, CPF e Telefone).")

# ------------------------------------------
# ABA: GERENCIAR CLIENTES
# ------------------------------------------
elif opcao == "Gerenciar Clientes":
    st.title("👥 Gerenciamento de Clientes")
    
    with engine.connect() as conn:
        clientes_lista = conn.execute(text("SELECT id, nome, cpf, cr, telefone FROM clientes ORDER BY nome ASC;")).fetchall()
    
    if not clientes_lista:
        st.info("Nenhum cliente cadastrado no sistema.")
    else:
        st.subheader("📋 Lista de Clientes Cadastrados")
        busca = st.text_input("🔍 Buscar cliente por nome ou CPF:")
        
        clientes_filtrados = [
            c for c in clientes_lista 
            if busca.lower() in c[1].lower() or busca in c[2]
        ]
        
        if clientes_filtrados:
            dict_clientes = {f"{c[1]} (CPF: {c[2]})": c for c in clientes_filtrados}
            cliente_sel_nome = st.selectbox("Selecione um cliente para visualizar ou alterar:", list(dict_clientes.keys()))
            cliente_dados = dict_clientes[cliente_sel_nome]
            
            st.divider()
            st.markdown(f"### ✏ Alterar Dados do Cliente: **{cliente_dados[1]}**")
            
            with st.form("form_editar_cliente"):
                id_cli = cliente_dados[0]
                novo_nome = st.text_input("Nome Completo", value=cliente_dados[1])
                novo_cpf = st.text_input("CPF", value=cliente_dados[2])
                novo_cr = st.text_input("Número do CR", value=cliente_dados[3] if cliente_dados[3] else "")
                novo_telefone = st.text_input("Telefone / WhatsApp", value=cliente_dados[4])
                
                btn_atualizar = st.form_submit_button("💾 Salvar Alterações")
                
                if btn_atualizar:
                    if novo_nome and novo_cpf and novo_telefone:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("""
                                    UPDATE clientes 
                                    SET nome = :n, cpf = :c, cr = :r, telefone = :t
                                    WHERE id = :id;
                                """), {"n": novo_nome, "c": novo_cpf, "r": novo_cr, "t": novo_telefone, "id": id_cli})
                            st.success("Dados do cliente atualizados com sucesso!")
                            st.rerun()
                        except Exception:
                            st.error("O CPF informado já pertence a outro cliente.")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")
        else:
            st.warning("Nenhum cliente encontrado.")

# ------------------------------------------
# ABA: CADASTRAR GUIA (GT)
# ------------------------------------------
elif opcao == "Cadastrar Guia (GT)":
    st.title("📄 Emissão / Cadastro de Guia de Tráfego")
    
    with engine.connect() as conn:
        clientes = conn.execute(text("SELECT id, nome, cpf FROM clientes ORDER BY nome;")).fetchall()
    
    if not clientes:
        st.warning("Nenhum cliente cadastrado. Cadastre um cliente primeiro.")
    else:
        opcoes_clientes = {f"{c[1]} (CPF: {c[2]})": c[0] for c in clientes}
        cliente_selecionado = st.selectbox("Selecione o Cliente", list(opcoes_clientes.keys()))
        cliente_id = opcoes_clientes[cliente_selecionado]
        
        with st.form("form_gt", clear_on_submit=True):
            numero_gt = st.text_input("Número da Guia de Tráfego (GT)")
            arma_descricao = st.text_input("Descrição da Arma (Ex: Pistola Taurus TS9)")
            calibre = st.text_input("Calibre (Ex: 9mm)")
            data_vencimento = st.date_input("Data de Vencimento da GT")
            
            salvar_gt = st.form_submit_button("Cadastrar GT")
            
            if salvar_gt:
                if numero_gt and arma_descricao and data_vencimento:
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO guias (cliente_id, numero_gt, arma_descricao, calibre, data_vencimento) VALUES (:cid, :gt, :arma, :cal, :venc);"),
                            {"cid": cliente_id, "gt": numero_gt, "arma": arma_descricao, "cal": calibre, "venc": data_vencimento}
                        )
                    st.success("Guia de Tráfego cadastrada com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

# ------------------------------------------
# ABA: CONSULTAR & ALERTAS
# ------------------------------------------
elif opcao == "Consultar & Alertas":
    st.title("🔍 Consulta de GTs e Alertas de Vencimento")
    
    with engine.connect() as conn:
        registros = conn.execute(text("""
            SELECT 
                g.id,
                c.nome,
                c.telefone,
                g.numero_gt,
                g.arma_descricao,
                g.data_vencimento,
                g.status
            FROM guias g
            JOIN clientes c ON g.cliente_id = c.id
            ORDER BY g.data_vencimento ASC;
        """)).fetchall()
    
    if registros:
        today = datetime.date.today()
        
        for r in registros:
            gt_id, nome, telefone, num_gt, arma, data_venc, status = r
            dias_restantes = (data_venc - today).days
            
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.write(f"**{nome}** — {arma}")
                st.caption(f"GT: {num_gt}")
                
            with col2:
                st.write(f"Vencimento: {data_venc.strftime('%d/%m/%Y')}")
                if dias_restantes < 0:
                    st.error(f"Vencida há {abs(dias_restantes)} dias")
                elif dias_restantes <= 15:
                    st.warning(f"Vence em {dias_restantes} dias")
                else:
                    st.success(f"Válida ({dias_restantes} dias)")
                    
            with col3:
                mensagem = f"Olá {nome}, informamos que sua Guia de Tráfego nº {num_gt} referente à arma {arma} vence em {data_venc.strftime('%d/%m/%Y')}. Entre em contato para renovação."
                msg_encoded = urllib.parse.quote(mensagem)
                link_wa = f"https://wa.me/{telefone}?text={msg_encoded}"
                
                st.markdown(f"[📲 Notificar WhatsApp]({link_wa})", unsafe_allow_dict=True)
                
            st.divider()
    else:
        st.info("Nenhuma Guia de Tráfego registrada.")

# ------------------------------------------
# ABA MASTER: GERENCIAR USUÁRIOS
# ------------------------------------------
elif opcao == "Gerenciar Usuários" and st.session_state["perfil_logado"] == "master":
    st.title("⚙️ Gerenciamento de Usuários (Acesso Master)")
    
    col_cad, col_alt = st.columns(2)
    
    with col_cad:
        st.subheader("➕ Cadastrar Novo Operador")
        with st.form("form_novo_usuario", clear_on_submit=True):
            novo_user = st.text_input("Nome de Usuário")
            nova_senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil de Acesso", ["operador", "master"])
            
            btn_criar = st.form_submit_button("Criar Usuário")
            
            if btn_criar:
                if novo_user and nova_senha:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO usuarios (usuario, senha, perfil) VALUES (:u, :s, :p);"), {"u": novo_user, "s": nova_senha, "p": perfil})
                        st.success(f"Usuário '{novo_user}' criado com sucesso!")
                        st.rerun()
                    except Exception:
                        st.error("Nome de usuário já existe.")
                else:
                    st.warning("Preencha usuário e senha.")
                    
    with col_alt:
        st.subheader("🔑 Alterar Senha de Operador")
        with engine.connect() as conn:
            lista_users = conn.execute(text("SELECT id, usuario FROM usuarios ORDER BY usuario;")).fetchall()
        
        if lista_users:
            dict_users = {u[1]: u[0] for u in lista_users}
            user_sel = st.selectbox("Selecione o Usuário", list(dict_users.keys()))
            
            with st.form("form_alterar_senha", clear_on_submit=True):
                senha_nova = st.text_input("Nova Senha", type="password")
                btn_alterar = st.form_submit_button("Atualizar Senha")
                
                if btn_alterar:
                    if senha_nova:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE usuarios SET senha = :s WHERE usuario = :u;"), {"s": senha_nova, "u": user_sel})
                        st.success(f"Senha do usuário '{user_sel}' alterada com sucesso!")
                    else:
                        st.warning("Digite a nova senha.")

    st.divider()
    st.subheader("📋 Usuários Cadastrados no Sistema")
    
    with engine.connect() as conn:
        usuarios_lista = conn.execute(text("SELECT id, usuario, perfil FROM usuarios;")).fetchall()
    
    df_users = pd.DataFrame(usuarios_lista, columns=["ID", "Usuário", "Perfil"])
    st.dataframe(df_users, use_container_width=True)
