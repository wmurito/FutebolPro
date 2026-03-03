import streamlit as st
import time

if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = "Dashboard"

pagina = st.radio("Navegar", ["Dashboard", "Sorteio", "Partida"], key="pagina_atual")

if pagina == "Dashboard":
    st.write("Dashboard")
elif pagina == "Sorteio":
    st.write("Sorteio")
    if st.button("Iniciar"):
        st.session_state.pagina_atual = "Partida"
        st.success("Iniciando!")
        time.sleep(1)
        st.rerun()
elif pagina == "Partida":
    st.write("Partida ao Vivo")
