import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta
import urllib.request

# ==============================================================================
# CONFIGURAÇÕES E PARÂMETROS INSTITUCIONAIS (PROTOCOLO V1.0)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "trades_database.json")
BRT_OFFSET = timedelta(hours=-3)

RISK_BRL = 15.0
TARGET_BRL = 16.5
RR_RATIO = 1.1

# ==============================================================================
# FUNÇÕES DE BANCO DE DADOS E SINCRONIZAÇÃO GIT
# ==============================================================================
def load_db():
    if not os.path.exists(DB_PATH):
        return {
            "initial_capital_brl": 1000.0,
            "risk_per_trade_pct": 1.5,
            "risk_per_trade_brl": 15.0,
            "target_rr": 1.1,
            "target_profit_brl": 16.5,
            "currency": "BRL",
            "active_trade": None,
            "trades": []
        }
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    data["last_updated"] = datetime.now(timezone(BRT_OFFSET)).isoformat()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def git_sync(commit_msg):
    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        git_cmd = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "cmd", "git.exe")
        if not os.path.exists(git_cmd):
            git_cmd = "git"

        subprocess.run([git_cmd, "add", "trades_database.json"], cwd=BASE_DIR, check=False)
        subprocess.run([git_cmd, "commit", "-m", commit_msg], cwd=BASE_DIR, check=False)
        res = subprocess.run([git_cmd, "push", "origin", "main"], cwd=BASE_DIR, env=env, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(f"[GIT] Sincronização Cloud realizada: {commit_msg}", flush=True)
        else:
            print(f"[GIT] Aviso no push: {res.stderr.strip()[:80]}", flush=True)
    except Exception as e:
        print(f"[GIT] Erro na sincronização: {e}", flush=True)

def update_maestri_note(status_summary):
    try:
        note_content = (
            f"# PAINEL OPERACIONAL - PAPER TRADING EM TEMPO REAL\n\n"
            f"## Status Global: 🟢 LOOP ATIVO (Monitoramento Contínuo)\n"
            f"Horário: {datetime.now(timezone(BRT_OFFSET)).strftime('%d/%m/%Y %H:%M:%S BRT')}\n\n"
            f"{status_summary}\n\n"
            f"### 📱 Dashboard Local: http://192.168.2.176:8501"
        )
        maestri_cli = "maestri"
        subprocess.run([maestri_cli, "note", "write", "Painel_Operacional", note_content], cwd=BASE_DIR, check=False, capture_output=True)
    except Exception:
        pass

# ==============================================================================
# FEEDS DE DADOS DE MERCADO EM TEMPO REAL
# ==============================================================================
def fetch_binance_klines(symbol="BTCUSDT", interval="5m", limit=60):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    candles = []
    for k in data:
        candles.append({
            "timestamp": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles

def calc_ema(values, period):
    k = 2.0 / (period + 1)
    ema = values[0]
    res = [ema]
    for v in values[1:]:
        ema = (v * k) + (ema * (1 - k))
        res.append(ema)
    return res

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(0.0, diff))
        losses.append(max(0.0, -diff))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calc_vwap(candles):
    cum_vol = 0.0
    cum_vp = 0.0
    for c in candles:
        v = c["volume"] if c["volume"] > 0 else 1.0
        typ = (c["high"] + c["low"] + c["close"]) / 3.0
        cum_vol += v
        cum_vp += typ * v
    return (cum_vp / cum_vol) if cum_vol > 0 else candles[-1]["close"]

# ==============================================================================
# VERIFICAÇÃO DE JANELAS DE GOVERNANÇA TEMPORAL
# ==============================================================================
def check_market_windows():
    now_brt = datetime.now(timezone(BRT_OFFSET))
    now_utc = datetime.now(timezone.utc)
    
    # 1. B3 (WIN): Dias úteis, exceto feriados nacionais conhecidos (ex: 12/10)
    is_b3_holiday = (now_brt.month == 10 and now_brt.day == 12) # Feriado Nacional Nossa Senhora Aparecida
    is_weekday = now_brt.weekday() < 5
    b3_w1 = (10 <= now_brt.hour < 12) and not (now_brt.hour == 11 and now_brt.minute >= 55)
    b3_w2 = (13 <= now_brt.hour < 15) and not (now_brt.hour == 14 and now_brt.minute >= 55)
    b3_active = is_weekday and not is_b3_holiday and (b3_w1 or b3_w2)

    # 2. Cripto (BTC): 05:00 às 14:00 BRT (08:00 às 17:00 UTC)
    btc_active = (5 <= now_brt.hour < 14)

    # 3. Commodities (XAU): Sobreposição (12:00 às 12:30 BRT) e Ásia (21:00 às 04:00 BRT)
    xau_w1 = (now_brt.hour == 12 and now_brt.minute <= 30)
    xau_w2 = (now_brt.hour >= 21 or now_brt.hour < 4)
    xau_active = (xau_w1 or xau_w2)

    return {
        "B3": {"active": b3_active, "reason": "Feriado Nacional (12/10)" if is_b3_holiday else ("Janela Fechada" if not (b3_w1 or b3_w2) else "Ativo")},
        "BTC": {"active": btc_active, "reason": "Janela Institucional (05h-14h BRT)" if btc_active else "Fora da Janela (Bloqueio Asiático)"},
        "XAU": {"active": xau_active, "reason": "Janela Autorizada" if xau_active else "Aguardando Sessão Asiática (21h BRT)"}
    }

# ==============================================================================
# LOOP PRINCIPAL DE EXECUÇÃO EM TEMPO REAL
# ==============================================================================
def run_paper_trading_iteration():
    db = load_db()
    current_balance = db.get("trades", [])[-1]["balance_after_brl"] if db.get("trades") else db["initial_capital_brl"]
    active_trade = db.get("active_trade")
    windows = check_market_windows()
    now_str = datetime.now(timezone(BRT_OFFSET)).strftime("%H:%M:%S")

    # --------------------------------------------------------------------------
    # 1. Gerenciar Trade Ativo (se houver)
    # --------------------------------------------------------------------------
    if active_trade:
        squad = active_trade["squad"]
        current_price = 0.0
        
        if squad == "Cripto":
            candles_5m = fetch_binance_klines("BTCUSDT", "5m", 5)
            current_price = candles_5m[-1]["close"]
            high_price = candles_5m[-1]["high"]
            low_price = candles_5m[-1]["low"]

            # Verificar Take Profit ou Stop Loss
            hit_tp = False
            hit_sl = False

            if active_trade["type"] == "COMPRA":
                if high_price >= active_trade["target_price"]:
                    hit_tp = True
                elif low_price <= active_trade["stop_loss"]:
                    hit_sl = True
            else:
                if low_price <= active_trade["target_price"]:
                    hit_tp = True
                elif high_price >= active_trade["stop_loss"]:
                    hit_sl = True

            if hit_tp:
                pnl = TARGET_BRL
                new_bal = current_balance + pnl
                closed_trade = {
                    "trade_id": len(db.get("trades", [])) + 1,
                    "date": datetime.now(timezone(BRT_OFFSET)).strftime("%Y-%m-%d"),
                    "time": now_str,
                    "squad": squad,
                    "asset": active_trade["asset"],
                    "type": active_trade["type"],
                    "entry_price": active_trade["entry_price"],
                    "stop_loss": active_trade["stop_loss"],
                    "target_price": active_trade["target_price"],
                    "result": "WIN",
                    "profit_brl": pnl,
                    "balance_after_brl": round(new_bal, 2),
                    "notes": "Take Profit atingido no alvo 1.1:1"
                }
                db["trades"].append(closed_trade)
                db["active_trade"] = None
                save_db(db)
                git_sync(f"chore(data): close trade #{closed_trade['trade_id']} [WIN] +R$ 16,50")
                print(f"[{now_str}] 🟢 TAKE PROFIT ATINGIDO! Trade #{closed_trade['trade_id']} Fechado com +R$ 16,50. Novo Saldo: R$ {new_bal:,.2f}", flush=True)
                return

            elif hit_sl:
                pnl = -RISK_BRL
                new_bal = current_balance + pnl
                closed_trade = {
                    "trade_id": len(db.get("trades", [])) + 1,
                    "date": datetime.now(timezone(BRT_OFFSET)).strftime("%Y-%m-%d"),
                    "time": now_str,
                    "squad": squad,
                    "asset": active_trade["asset"],
                    "type": active_trade["type"],
                    "entry_price": active_trade["entry_price"],
                    "stop_loss": active_trade["stop_loss"],
                    "target_price": active_trade["target_price"],
                    "result": "LOSS",
                    "profit_brl": pnl,
                    "balance_after_brl": round(new_bal, 2),
                    "notes": "Stop Loss acionado na mínima/máxima do pivô"
                }
                db["trades"].append(closed_trade)
                db["active_trade"] = None
                save_db(db)
                git_sync(f"chore(data): close trade #{closed_trade['trade_id']} [LOSS] -R$ 15,00")
                print(f"[{now_str}] 🔴 STOP LOSS ACIONADO! Trade #{closed_trade['trade_id']} Fechado com -R$ 15,00. Novo Saldo: R$ {new_bal:,.2f}", flush=True)
                return
            else:
                print(f"[{now_str}] Trade Ativo: {active_trade['type']} {active_trade['asset']} @ {active_trade['entry_price']} | Atual: {current_price} | TP: {active_trade['target_price']} | SL: {active_trade['stop_loss']}", flush=True)
                return

    # --------------------------------------------------------------------------
    # 2. Varredura por Novas Oportunidades (se sem trade ativo)
    # --------------------------------------------------------------------------
    summary_lines = []

    # Status dos Esquadrões
    summary_lines.append(f"### 🌐 Estado dos Esquadrões:\n")
    summary_lines.append(f"- 🇧🇷 **[B3 WIN]**: ⏸️ {windows['B3']['reason']}")
    summary_lines.append(f"- 🏆 **[XAU Ouro]**: ⏸️ {windows['XAU']['reason']}")
    summary_lines.append(f"- 🪙 **[BTC Cripto]**: {'🟢 ' + windows['BTC']['reason'] if windows['BTC']['active'] else '⏸️ ' + windows['BTC']['reason']}")

    # Análise de Cripto (BTC/USDT) se ativo na janela
    if windows["BTC"]["active"]:
        try:
            candles_h1 = fetch_binance_klines("BTCUSDT", "1h", 55)
            candles_5m = fetch_binance_klines("BTCUSDT", "5m", 55)

            closes_h1 = [c["close"] for c in candles_h1]
            ema20_h1 = calc_ema(closes_h1, 20)[-1]
            ema50_h1 = calc_ema(closes_h1, 50)[-1]
            h1_bullish = ema20_h1 > ema50_h1
            h1_bearish = ema20_h1 < ema50_h1

            closes_5m = [c["close"] for c in candles_5m]
            ema8_5m = calc_ema(closes_5m, 8)[-1]
            ema21_5m = calc_ema(closes_5m, 21)[-1]
            vwap_5m = calc_vwap(candles_5m)
            rsi_5m = calc_rsi(closes_5m, 14)
            current_close = closes_5m[-1]

            summary_lines.append(
                f"\n### 📊 Leitura Atual BTC/USDT (5m):\n"
                f"- Preço: ${current_close:,.2f} | VWAP: ${vwap_5m:,.2f}\n"
                f"- H1 Macro: {'ALTA (EMA20 > EMA50)' if h1_bullish else 'BAIXA (EMA20 < EMA50)'}\n"
                f"- 5m Médias: EMA8=${ema8_5m:,.2f} | EMA21=${ema21_5m:,.2f}\n"
                f"- IFR(14): {rsi_5m:.1f} (Neutro)"
            )

            # Verificar Gatilho de COMPRA
            if h1_bullish and (ema8_5m > ema21_5m) and (current_close > vwap_5m) and (40.0 <= rsi_5m <= 65.0):
                min_recent = min([c["low"] for c in candles_5m[-4:]])
                stop_loss = round(min_recent - 30.0, 2)
                risk_pts = current_close - stop_loss
                if 40.0 <= risk_pts <= 350.0:
                    target_price = round(current_close + (risk_pts * RR_RATIO), 2)
                    new_trade = {
                        "squad": "Cripto",
                        "asset": "BTC/USDT",
                        "type": "COMPRA",
                        "entry_price": current_close,
                        "stop_loss": stop_loss,
                        "target_price": target_price,
                        "risk_pts": risk_pts,
                        "opened_at": now_str
                    }
                    db["active_trade"] = new_trade
                    save_db(db)
                    git_sync(f"chore(data): open trade COMPRA BTC/USDT @ {current_close}")
                    print(f"[{now_str}] 🚀 NOVA ORDEM DE COMPRA SIMULADA: BTC/USDT @ ${current_close} | SL: ${stop_loss} | TP: ${target_price}", flush=True)
                    return

            # Verificar Gatilho de VENDA
            elif h1_bearish and (ema8_5m < ema21_5m) and (current_close < vwap_5m) and (35.0 <= rsi_5m <= 60.0):
                max_recent = max([c["high"] for c in candles_5m[-4:]])
                stop_loss = round(max_recent + 30.0, 2)
                risk_pts = stop_loss - current_close
                if 40.0 <= risk_pts <= 350.0:
                    target_price = round(current_close - (risk_pts * RR_RATIO), 2)
                    new_trade = {
                        "squad": "Cripto",
                        "asset": "BTC/USDT",
                        "type": "VENDA",
                        "entry_price": current_close,
                        "stop_loss": stop_loss,
                        "target_price": target_price,
                        "risk_pts": risk_pts,
                        "opened_at": now_str
                    }
                    db["active_trade"] = new_trade
                    save_db(db)
                    git_sync(f"chore(data): open trade VENDA BTC/USDT @ {current_close}")
                    print(f"[{now_str}] 🚀 NOVA ORDEM DE VENDA SIMULADA: BTC/USDT @ ${current_close} | SL: ${stop_loss} | TP: ${target_price}", flush=True)
                    return
            else:
                summary_lines.append(f"- Veredito: `[AGUARDAR]` (Sem confluência plena de rompimento/pullback)")
        except Exception as e:
            summary_lines.append(f"- Erro no feed BTC: {e}")

    update_maestri_note("\n".join(summary_lines))
    print(f"[{now_str}] Ciclo concluído. Saldo Atual: R$ {current_balance:,.2f} | Status: Standby/Monitorando...", flush=True)

# ==============================================================================
# EXECUÇÃO CONTÍNUA EM LOOP
# ==============================================================================
if __name__ == "__main__":
    print(">>> Iniciando Motor Autônomo de Paper Trading em Tempo Real...", flush=True)
    print(">>> Pressione Ctrl+C para interromper.", flush=True)
    while True:
        try:
            run_paper_trading_iteration()
        except Exception as e:
            print(f"[ERRO NO LOOP]: {e}", flush=True)
        time.sleep(30) # Checagem a cada 30 segundos
