
# 🤖 Deriv Bot - Estratégia 0Matador

Este robô opera automaticamente na Deriv.com com base nas últimas estratégias personalizadas:

- Estratégia 0Matador: entra em Over 3 ou Over 4 se os últimos 8 dígitos forem todos ≥ 4.
- Pausa automática entre operações (5 a 120 segundos).
- Controle de Martingale e limite de ganho/perda.

## Como usar
1. Instale as dependências com `pip install -r requirements.txt`
2. Execute com `streamlit run app.py`
3. Insira seu token da Deriv e clique em Iniciar
