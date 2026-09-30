import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de GTs", layout="wide")

# --- BANCO DE DADOS ---
conn = sqlite3.connect("gestao_gts.db", check_same_thread=False)
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS atiradores 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, cr TEXT, sigma TEXT, telefone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS armas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, atirador_id INTEGER, tipo TEXT, calibre TEXT, numero_serie TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS guias 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, arma_id INTEGER, clube_destino TEXT, finalidade TEXT, data_validade DATE)''')
conn.commit()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("Navegação")
opcao = st.sidebar.radio("Ir para:", ["Painel Geral / Alertas", "Cadastrar Atirador e Armas"])

# --- TELA DE CADASTRO ---
if opcao == "Cadastrar Atirador e Armas":
    st.header("Registrar Novo Atirador e Armas")
    
    with st.form("form_cadastro"):
        st.subheader("👤 Dados do Atirador")
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo (ou Razão Social)")
        cpf = col2.text_input("CPF")
        
        col3, col4, col5 = st.columns(3)
        cr = col3.text_input("Número do CR")
        sigma = col4.text_input("Número do SIGMA")
        telefone = col5.text_input("Telefone")
        
        st.subheader("🔫 Dados da Arma (Repetir para cada arma)")
        col_a1, col_a2, col_a3 = st.columns(3)
        tipo = col_a1.selectbox("Tipo de Arma", ["Pistola", "Revólver", "Carabina", "Fuzil", "Espingarda", "Outro"])
        calibre = col_a2.text_input("Calibre")
        numero_serie = col_a3.text_input("Número de Série")
        
        st.subheader("🎯 Detalhes da Guia de Tráfego")
        col_g1, col_g2 = st.columns(2)
        finalidade = col_g1.selectbox("Finalidade", ["Caça", "Atirador Desportivo", "Colecionador", "Porte de Trânsito"])
        clube = col_g2.selectbox("Clube de Destino", ["Abelardo Luz", "Xanxerê", "São Domingos", "São Lourenço", "Clevelândia", "Outro"])
        
        validade = st.date_input("Data de Validade da Guia")
        
        btn_salvar = st.form_submit_button("Registrar Novo Atirador e Armas")
        
        if btn_salvar:
            if nome and cpf:
                c.execute("INSERT INTO atiradores (nome, cpf, cr, sigma, telefone) VALUES (?, ?, ?, ?, ?)",
                          (nome, cpf, cr, sigma, telefone))
                atirador_id = c.lastrowid
                
                c.execute("INSERT INTO armas (atirador_id, tipo, calibre, numero_serie) VALUES (?, ?, ?, ?)",
                          (atirador_id, tipo, calibre, numero_serie))
                arma_id = c.lastrowid
                
                c.execute("INSERT INTO guias (arma_id, clube_destino, finalidade, data_validade) VALUES (?, ?, ?, ?)",
                          (arma_id, clube, finalidade, validade))
                conn.commit()
                st.success(f"Atirador {nome} registrado com sucesso!")
            else:
                st.error("Por favor, preencha pelo menos Nome e CPF.")

# --- PAINEL GERAL ---
elif opcao == "Painel Geral / Alertas":
    st.header("Painel Geral de Guias de Tráfego")
    
    query = '''
        SELECT a.nome, a.cr, a.sigma, a.telefone, ar.tipo, ar.calibre, ar.numero_serie, g.clube_destino, g.data_validade
        FROM atiradores a
        JOIN armas ar ON a.id = ar.atirador_id
        JOIN guias g ON ar.id = g.arma_id
    '''
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        st.info("Nenhum atirador cadastrado ainda.")
    else:
        for nome, group in df.groupby("nome"):
            with st.expander(f"👤 {nome} | CR: {group['cr'].iloc[0]} | Tel: {group['telefone'].iloc[0]}"):
                st.write(f"**SIGMA:** {group['sigma'].iloc[0]}")
                st.dataframe(group[['tipo', 'calibre', 'numero_serie', 'clube_destino', 'data_validade']])