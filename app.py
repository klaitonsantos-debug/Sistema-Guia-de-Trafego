import sqlite3
import datetime
import urllib.parse
import streamlit as st
from streamlit_option_menu import option_menu

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E BANCO DE DADOS
# ==========================================
st.set_page_config(
    page_title="Gestão de Guias de Tráfego",
    page_icon="🛡️",
    layout="wide"
)

def conectar_bd():
    conn = sqlite3.connect("gestao_gts.db")
    return conn

def criar_tabelas():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT DEFAULT 'operador'
        )
    """)
    
    # Tabela de Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            cr TEXT,
            telefone TEXT NOT NULL
        )
    """)
    
    # Tabela de Guias de Tráfego (GTs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            numero_gt TEXT NOT NULL,
            arma_descricao TEXT NOT NULL,
            calibre TEXT,
            data_vencimento DATE NOT NULL,
            status TEXT DEFAULT 'Ativa',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    """)
    
    # Usuário Padrão Master
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'Klaiton'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES ('Klaiton', '134679', 'master')")
        
    conn.commit()
    conn.close()

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
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, perfil FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    user = cursor.fetchone()
    conn.close()
    return user

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
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    alerta_15 = today + datetime.timedelta(days=15)
    
    cursor.execute("SELECT COUNT(*) FROM guias WHERE data_vencimento > ? AND status = 'Ativa'", (alerta_15,))
    guias_em_dia = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM guias WHERE data_vencimento >= ? AND data_vencimento <= ? AND status = 'Ativa'", (today, alerta_15))
    guias_a_vencer = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM guias WHERE data_vencimento < ? AND status = 'Ativa'", (today,))
    guias_vencidas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]
    
    conn.close()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Guias Em Dia", guias_em_dia)
    c2.metric("⚠ A Vencer (15 dias)", guias_a_vencer)
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
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO clientes (nome, cpf, cr, telefone) VALUES (?, ?, ?, ?)",
                        (nome, cpf, cr, telefone)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Cliente {nome} cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("CPF já cadastrado no sistema.")
            else:
                st.warning("Preencha todos os campos obrigatórios (Nome, CPF e Telefone).")

# ------------------------------------------
# ABA: GERENCIAR CLIENTES (VISUALIZAR E EDITAR)
# ------------------------------------------
elif opcao == "Gerenciar Clientes":
    st.title("👥 Gerenciamento de Clientes")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, cpf, cr, telefone FROM clientes ORDER BY nome ASC")
    clientes_lista = cursor.fetchall()
    conn.close()
    
    if not clientes_lista:
        st.info("Nenhum cliente cadastrado no sistema.")
    else:
        st.subheader("📋 Lista de Clientes Cadastrados")
        
        # Filtro de Busca
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
            st.markdown(f"### ✏️ Alterar Dados do Cliente: **{cliente_dados[1]}**")
            
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
                            conn = conectar_bd()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE clientes 
                                SET nome = ?, cpf = ?, cr = ?, telefone = ?
                                WHERE id = ?
                            """, (novo_nome, novo_cpf, novo_cr, novo_telefone, id_cli))
                            conn.commit()
                            conn.close()
                            st.success("Dados do cliente atualizados com sucesso!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("O CPF informado já pertence a outro cliente.")
                    else:
                        st.warning("Preencha todos os campos obrigatórios (Nome, CPF e Telefone).")
        else:
            st.warning("Nenhum cliente encontrado com a busca informada.")

# ------------------------------------------
# ABA: CADASTRAR GUIA (GT)
# ------------------------------------------
elif opcao == "Cadastrar Guia (GT)":
    st.title("📄 Emissão / Cadastro de Guia de Tráfego")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome")
    clientes = cursor.fetchall()
    conn.close()
    
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
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO guias (cliente_id, numero_gt, arma_descricao, calibre, data_vencimento) VALUES (?, ?, ?, ?, ?)",
                        (cliente_id, numero_gt, arma_descricao, calibre, data_vencimento)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Guia de Tráfego cadastrada com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

# ------------------------------------------
# ABA: CONSULTAR & ALERTAS
# ------------------------------------------
elif opcao == "Consultar & Alertas":
    st.title("🔍 Consulta de GTs e Alertas de Vencimento")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
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
        ORDER BY g.data_vencimento ASC
    """)
    registros = cursor.fetchall()
    conn.close()
    
    if registros:
        today = datetime.date.today()
        
        for r in registros:
            gt_id, nome, telefone, num_gt, arma, vencimento_str, status = r
            data_venc = datetime.datetime.strptime(vencimento_str, "%Y-%m-%d").date()
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
    
    # Formulário 1: Novo Usuário
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
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)", (novo_user, nova_senha, perfil))
                        conn.commit()
                        conn.close()
                        st.success(f"Usuário '{novo_user}' criado com sucesso!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Nome de usuário já existe.")
                else:
                    st.warning("Preencha usuário e senha.")
                    
    # Formulário 2: Alterar Senha de Usuários
    with col_alt:
        st.subheader("🔑 Alterar Senha de Operador")
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario FROM usuarios ORDER BY usuario")
        lista_users = cursor.fetchall()
        conn.close()
        
        if lista_users:
            dict_users = {u[1]: u[0] for u in lista_users}
            user_sel = st.selectbox("Selecione o Usuário", list(dict_users.keys()))
            
            with st.form("form_alterar_senha", clear_on_submit=True):
                senha_nova = st.text_input("Nova Senha", type="password")
                btn_alterar = st.form_submit_button("Atualizar Senha")
                
                if btn_alterar:
                    if senha_nova:
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET senha = ? WHERE usuario = ?", (senha_nova, user_sel))
                        conn.commit()
                        conn.close()
                        st.success(f"Senha do usuário '{user_sel}' alterada com sucesso!")
                    else:
                        st.warning("Digite a nova senha.")

    st.divider()
    st.subheader("📋 Usuários Cadastrados no Sistema")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, perfil FROM usuarios")
    usuarios_lista = cursor.fetchall()
    conn.close()
    
    st.table(usuarios_lista)
