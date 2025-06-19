import asyncio
import websockets
import json
import random
import streamlit as st

async def aguardar_resultado(ws, contract_id):
    while True:
        result_msg = json.loads(await ws.recv())
        if result_msg.get("contract") and result_msg["contract"].get("contract_id") == contract_id:
            return result_msg["contract"]

async def start_bot(token, stake, threshold, take_profit, stop_loss, multiplicador, estrategia):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"authorize": token}))
        auth_response = json.loads(await ws.recv())

        if auth_response.get("error"):
            yield "❌ Erro de Autorização", "Token inválido ou sem permissão de negociação.", False
            return

        yield "✅ Conectado com sucesso", "Autenticado na conta Deriv.", False

        await ws.send(json.dumps({
            "ticks": "R_100",
            "subscribe": 1
        }))

        digits = []
        loss_streak = 0
        current_stake = stake
        total_profit = 0
        win_count = 0
        loss_count = 0

        while True:
            if total_profit >= take_profit:
                yield "🏁 Meta Atingida", f"Lucro total ${total_profit:.2f} ≥ Meta ${take_profit:.2f}", True
                return
            if abs(total_profit) >= stop_loss:
                yield "🛑 Stop Loss Atingido", f"Perda total ${total_profit:.2f} ≥ Limite ${stop_loss:.2f}", True
                return

            try:
                msg = json.loads(await ws.recv())
            except websockets.exceptions.ConnectionClosed:
                yield "🔌 Conexão fechada", "Tentando reconectar...", True
                return

            if "tick" in msg:
                quote = msg["tick"]["quote"]
                digit = int(str(quote)[-1])
                digits.append(digit)

                yield "📥 Tick recebido", f"Preço: {quote} | Último dígito: {digit}", False

                if len(digits) > 8:
                    digits.pop(0)

                if len(digits) == 8:
                    tipo = None
                    barrier = None

                    if estrategia == "Dígitos < 4 ≥ limite → Over 3":
                        count_under_4 = sum(1 for d in digits if d < 4)
                        yield "📊 Analisando", f"Dígitos: {digits} | < 4: {count_under_4}", False
                        if count_under_4 >= threshold:
                            tipo = "DIGITOVER"
                            barrier = "3"
                            yield "📈 Sinal Detectado", f"{count_under_4} dígitos < 4. Enviando OVER 3.", False

                    elif estrategia in ["Nenhum dígito < 4 → Over 3 ou 4 aleatório", "0Matador"]:
                        if all(d >= 4 for d in digits):
                            tipo = "DIGITOVER"
                            barrier = random.choice(["3", "4"])
                            yield "🔥 Estratégia 0Matador", f"Dígitos: {digits}. Enviando OVER {barrier}", False

                    if tipo and barrier:
                        await ws.send(json.dumps({
                            "buy": 1,
                            "price": current_stake,
                            "parameters": {
                                "amount": current_stake,
                                "basis": "stake",
                                "contract_type": tipo,
                                "barrier": barrier,
                                "currency": "USD",
                                "duration": 1,
                                "duration_unit": "t",
                                "symbol": "R_100"
                            }
                        }))

                        buy_response = json.loads(await ws.recv())
                        if "buy" in buy_response:
                            contract_id = buy_response["buy"]["contract_id"]
                            yield "✅ Compra enviada", f"Contrato #{contract_id} iniciado.", False

                            contract = await aguardar_resultado(ws, contract_id)
                            status = contract["status"]
                            profit = contract.get("profit", 0)
                            total_profit += profit

                            if status == "won":
                                win_count += 1
                                loss_streak = 0
                                current_stake = stake
                                yield "🏆 WIN", f"Lucro ${profit:.2f} | Total: ${total_profit:.2f}", False
                            elif status == "lost":
                                loss_count += 1
                                loss_streak += 1
                                yield "💥 LOSS", f"Prejuízo ${profit:.2f} | Total: ${total_profit:.2f}", False
                                if loss_streak >= 2:
                                    current_stake *= multiplicador
                                    yield "🔁 Multiplicador aplicado", f"Nova stake: R${current_stake:.2f}", False

                            digits.clear()

                            wait_time = random.randint(5, 120)
                            yield "⏳ Aguardando", f"Esperando {wait_time} segundos antes de reiniciar análise...", False
                            await asyncio.sleep(wait_time)
