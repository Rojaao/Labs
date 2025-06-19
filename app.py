import streamlit as st
import asyncio
from logic import start_bot
import random

st.set_page_config(page_title="Deriv Bot - Estratégia", layout="wide")
st.title("🤖 Deriv Bot - Estratégia Personalizada")

token = st.text_input("🔑 Token da Deriv", type="password")
stake = st.number_input("💵 Valor Inicial da Entrada", min_value=0.35, value=1.00, step=0.01)
threshold = st.number_input("📉 Mínimo de dígitos < 4 para entrar", min_value=1, max_value=8, value=3)
take_profit = st.number_input("🎯 Meta de Lucro Total ($)", min_value=1.0, value=10.0, step=0.5)
stop_loss = st.number_input("🛑 Limite de Perda Total ($)", min_value=1.0, value=10.0, step=0.5)
multiplicador = st.number_input("🔁 Fator de Multiplicação após 2 perdas", min_value=1.0, value=1.68, step=0.01)

estrategia = st.selectbox("🧠 Estratégia Utilizada", [
    "Dígitos < 4 ≥ limite → Over 3",
    "Nenhum dígito < 4 → Over 3 ou 4 aleatório",
    "0Matador"
])

start_button = st.button("▶️ Iniciar Robô")
stop_button = st.button("⏹️ Parar Robô")

log_area = st.empty()
status_area = st.empty()

if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

async def run_bot_loop():
    logs = []
    while True:
        if not st.session_state.bot_running:
            await asyncio.sleep(1)
            continue

        try:
            async for status, log, finished in start_bot(token, stake, threshold, take_profit, stop_loss, multiplicador, estrategia):
                status_area.success(status)
                logs.append(log)
                log_area.code("\n".join(logs[-25:]), language='text')

                if finished:
                    await asyncio.sleep(2)  # como se clicasse em parar
                    st.session_state.bot_running = False
                    wait_time = random.randint(5, 120)
                    status_area.warning(f"Robô pausado. Reiniciando em {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
                    st.session_state.bot_running = True
                    break  # volta para while True e reinicia

        except Exception as e:
            status_area.error(f"Erro: {str(e)}")
            st.session_state.bot_running = False

if start_button and token:
    st.session_state.bot_running = True
    asyncio.run(run_bot_loop())

if stop_button:
    st.session_state.bot_running = False
    st.warning("Robô parado manualmente.")
