import json
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA (MOBILE-FIRST)
# ==============================================================================
st.set_page_config(
    page_title="Maestri Quant — Live Mobile Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS Moderna e Otimizada para Celular (Dark Glassmorphism)
st.markdown(
    """
<style>
    /* Otimização mobile e correção de corte superior */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    h1, h2, h3 {
        line-height: 1.3 !important;
        margin-bottom: 0.5rem !important;
        margin-top: 0 !important;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-title {
        font-size: 0.82rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 4px 0;
    }
    .metric-delta-pos {
        color: #10b981;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #ef4444;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .trade-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 6px;
    }
    .badge-win { background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-loss { background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-b3 { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-cripto { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-commodities { background-color: rgba(234, 179, 8, 0.2); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.4); }
    .badge-buy { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
    .badge-sell { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }
    .confluence-box {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 8px;
        border-left: 3px solid #3b82f6;
        font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# CARREGAMENTO DO BANCO DE DADOS LOCAL
# ==============================================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "trades_database.json")


def load_database():
    if not os.path.exists(DB_PATH):
        st.error(f"Arquivo de banco de dados não encontrado em: {DB_PATH}")
        st.stop()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


data = load_database()
initial_capital = data.get("initial_capital_brl", 1000.0)
trades_raw = data.get("trades", [])
df_trades = pd.DataFrame(trades_raw)

# ==============================================================================
# CABEÇALHO DO DASHBOARD
# ==============================================================================
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("### ⚡ Maestri Quant — Gestão de Capital & Confluência")
    st.caption("Banca Base: **R$ 1.000,00** • Risco Fixo: **1,5% (R$ 15,00)** • Alvo: **1,1 : 1 (R$ 16,50)**")
with col_btn:
    if st.button("🔄 Atualizar"):
        st.rerun()

# ==============================================================================
# CÁLCULO DE MÉTRICAS GLOBAIS
# ==============================================================================
if not df_trades.empty:
    total_trades = len(df_trades)
    wins = (df_trades["result"] == "WIN").sum()
    losses = (df_trades["result"] == "LOSS").sum()
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    current_balance = df_trades["balance_after_brl"].iloc[-1]
    net_profit = current_balance - initial_capital
    net_profit_pct = (net_profit / initial_capital) * 100

    gross_profit = df_trades[df_trades["profit_brl"] > 0]["profit_brl"].sum()
    gross_loss = abs(df_trades[df_trades["profit_brl"] < 0]["profit_brl"].sum())
    profit_factor = (
        round(gross_profit / gross_loss, 2)
        if gross_loss > 0
        else (round(gross_profit, 2) if gross_profit > 0 else 1.0)
    )
else:
    total_trades = 0
    wins = 0
    losses = 0
    win_rate = 0.0
    current_balance = initial_capital
    net_profit = 0.0
    net_profit_pct = 0.0
    profit_factor = 0.0

# ==============================================================================
# CARDS DE MÉTRICAS NO TOPO (RESPONSIVO EM 4 COLUNAS / MOBILE STACK)
# ==============================================================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    delta_class = "metric-delta-pos" if net_profit >= 0 else "metric-delta-neg"
    delta_sign = "+" if net_profit >= 0 else ""
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-title">Saldo da Conta</div>
        <div class="metric-value">R$ {current_balance:,.2f}</div>
        <div class="{delta_class}">{delta_sign}R$ {net_profit:,.2f} ({delta_sign}{net_profit_pct:.1f}%)</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-title">Lucro Líquido Acumulado</div>
        <div class="metric-value">R$ {net_profit:,.2f}</div>
        <div class="{delta_class}">{wins} Acertos / {losses} Stops</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-title">Taxa de Acerto (Win Rate)</div>
        <div class="metric-value">{win_rate:.1f}%</div>
        <div class="metric-delta-pos">Meta Institucional: ~70%</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-title">Fator de Lucro</div>
        <div class="metric-value">{profit_factor}</div>
        <div class="metric-delta-pos">R:R Calibrado: 1,1 : 1</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ==============================================================================
# GRÁFICO DA CURVA DE CAPITAL (EQUITY CURVE)
# ==============================================================================
st.subheader("📈 Curva de Evolução Patrimonial (R$)")

if not df_trades.empty:
    equity_x = ["Início"] + [
        f"#{r['trade_id']} ({r['squad']})" for _, r in df_trades.iterrows()
    ]
    equity_y = [initial_capital] + df_trades["balance_after_brl"].tolist()

    fig_equity = go.Figure()

    # Linha de capital com gradiente de preenchimento
    fig_equity.add_trace(
        go.Scatter(
            x=equity_x,
            y=equity_y,
            mode="lines+markers",
            name="Saldo da Conta (R$)",
            line=dict(color="#10b981", width=3, shape="spline"),
            marker=dict(size=7, color="#10b981", symbol="circle"),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.12)",
            hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>",
        )
    )

    # Linha base do capital inicial
    fig_equity.add_hline(
        y=initial_capital,
        line_dash="dot",
        line_color="rgba(255, 255, 255, 0.3)",
        annotation_text="Banca Inicial: R$ 1.000,00",
        annotation_position="bottom right",
    )

    fig_equity.update_layout(
        template="plotly_dark",
        height=320,
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.08)"),
    )

    st.plotly_chart(fig_equity, use_container_width=True)
else:
    st.info("Nenhuma operação registrada ainda na base.")

# ==============================================================================
# BREAKDOWN POR ESQUADRÃO DE MERCADO
# ==============================================================================
st.subheader("🌐 Desempenho por Esquadrão Operacional")

if not df_trades.empty:
    squad_stats = []
    for squad_name in ["B3", "Cripto", "Commodities"]:
        df_s = df_trades[df_trades["squad"] == squad_name]
        s_total = len(df_s)
        if s_total > 0:
            s_wins = (df_s["result"] == "WIN").sum()
            s_losses = (df_s["result"] == "LOSS").sum()
            s_wr = (s_wins / s_total) * 100
            s_net = df_s["profit_brl"].sum()
        else:
            s_wins = 0
            s_losses = 0
            s_wr = 0.0
            s_net = 0.0
        squad_stats.append(
            {
                "Esquadrão": squad_name,
                "Trades": s_total,
                "Acertos": s_wins,
                "Stops": s_losses,
                "Win Rate (%)": f"{s_wr:.1f}%",
                "Lucro Líquido (R$)": f"R$ {s_net:+,.2f}",
                "net_val": s_net,
            }
        )

    col_sq1, col_sq2 = st.columns([1, 1])

    with col_sq1:
        df_sq = pd.DataFrame(squad_stats)
        colors = ["#3b82f6", "#f59e0b", "#eab308"]
        fig_squad = px.bar(
            df_sq,
            x="Esquadrão",
            y="net_val",
            color="Esquadrão",
            color_discrete_sequence=colors,
            title="Contribuição Financeira (R$)",
            text="Lucro Líquido (R$)",
        )
        fig_squad.update_layout(
            template="plotly_dark",
            height=260,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            yaxis_title=None,
            xaxis_title=None,
        )
        st.plotly_chart(fig_squad, use_container_width=True)

    with col_sq2:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.dataframe(
            df_sq[
                [
                    "Esquadrão",
                    "Trades",
                    "Acertos",
                    "Stops",
                    "Win Rate (%)",
                    "Lucro Líquido (R$)",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")

# ==============================================================================
# SEÇÃO DETALHADA: HISTÓRICO DE OPERAÇÕES & CONFLUÊNCIAS INSTITUCIONAIS
# ==============================================================================
st.subheader("🎯 Detalhamento de Operações & Confluência Institucional")
st.caption("Visão individual e auditável com alinhamento MTF H1, VWAP, IFR (14), estruturas de pivô e gestão de risco.")

if not df_trades.empty:
    # Filtros interativos para exploração mobile/desktop
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        squad_filter = st.selectbox("Filtrar por Esquadrão:", ["Todos", "B3", "Cripto", "Commodities"])
    with col_f2:
        result_filter = st.selectbox("Filtrar por Resultado:", ["Todos", "WIN", "LOSS"])

    filtered_trades = df_trades.copy()
    if squad_filter != "Todos":
        filtered_trades = filtered_trades[filtered_trades["squad"] == squad_filter]
    if result_filter != "Todos":
        filtered_trades = filtered_trades[filtered_trades["result"] == result_filter]

    # Ordenar pelos mais recentes primeiro
    filtered_trades = filtered_trades.sort_values(by="trade_id", ascending=False)

    # 1. Tabela Resumo Expandida
    table_rows = []
    for _, t in filtered_trades.iterrows():
        conf = t.get("confluence", {}) if isinstance(t.get("confluence"), dict) else {}
        entry_t = t.get("entry_time", f"{t['date']} {t['time']}")
        exit_t = t.get("exit_time", f"{t['date']} -")
        
        table_rows.append({
            "#": t["trade_id"],
            "Ativo": t["asset"],
            "Direção": "🟢 COMPRA" if t["type"] == "COMPRA" else "🔴 VENDA",
            "Entrada": entry_t,
            "Saída": exit_t,
            "Preço Entrada": f"{t['entry_price']:,.2f}",
            "Stop Loss": f"{t['stop_loss']:,.2f}",
            "Take Profit": f"{t['target_price']:,.2f}",
            "R:R": t.get("risk_reward", "1,1 : 1"),
            "Resultado": "🟢 WIN" if t["result"] == "WIN" else "🔴 LOSS",
            "P&L (R$)": f"+R$ {t['profit_brl']:,.2f}" if t["profit_brl"] > 0 else f"-R$ {abs(t['profit_brl']):,.2f}",
            "Saldo (R$)": f"R$ {t['balance_after_brl']:,.2f}",
            "Macro H1": conf.get("macro_h1", "Alinhado"),
            "VWAP": conf.get("vwap_position", "Favorável"),
            "IFR(14)": conf.get("rsi_14", "-"),
            "Estrutura 5m": conf.get("structure_5m", t.get("notes", "-")),
        })

    df_display_summary = pd.DataFrame(table_rows)
    st.dataframe(df_display_summary, use_container_width=True, hide_index=True)

    # 2. Cartões Individuais Detalhados (Mobile Friendly Expanders)
    st.markdown("#### 🔍 Análise Profunda Individual por Trade")
    
    for _, t in filtered_trades.iterrows():
        conf = t.get("confluence", {}) if isinstance(t.get("confluence"), dict) else {}
        res_badge = "🟢 WIN (+R$ 16,50)" if t["result"] == "WIN" else "🔴 LOSS (-R$ 15,00)"
        dir_badge = "🟢 COMPRA" if t["type"] == "COMPRA" else "🔴 VENDA"
        entry_t = t.get("entry_time", f"{t['date']} {t['time']}")
        exit_t = t.get("exit_time", f"{t['date']} -")
        
        expander_title = f"Trade #{t['trade_id']} • {t['asset']} ({dir_badge}) • {res_badge} • Saldo: R$ {t['balance_after_brl']:,.2f}"
        
        with st.expander(expander_title, expanded=(t["trade_id"] == df_trades["trade_id"].max())):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Esquadrão:** `{t['squad']}`")
                st.markdown(f"**Direção:** `{t['type']}`")
                st.markdown(f"**Resultado:** **{res_badge}**")
            with c2:
                st.markdown(f"**Horário Entrada:** `{entry_t}`")
                st.markdown(f"**Horário Saída:** `{exit_t}`")
                st.markdown(f"**Risco : Retorno:** `{t.get('risk_reward', '1,1 : 1')}`")
            with c3:
                st.markdown(f"**Preço Entrada:** `{t['entry_price']:,.2f}`")
                st.markdown(f"**Stop Loss:** `{t['stop_loss']:,.2f}`")
                st.markdown(f"**Take Profit:** `{t['target_price']:,.2f}`")

            # Bloco de Confluência Institucional
            st.markdown(
                f"""
            <div class="confluence-box">
                <b>🧩 Critérios de Confluência Validados no Gatilho:</b><br>
                • <b>Tendência Macro (H1 MTF):</b> {conf.get('macro_h1', 'Alinhamento de EMA 20 e EMA 50')}<br>
                • <b>Ancoragem Institucional (VWAP):</b> {conf.get('vwap_position', 'Preço a favor da VWAP da sessão')}<br>
                • <b>Momentum IFR (14):</b> {conf.get('rsi_14', 'Neutro')} (Calibrado entre 40-65 na compra ou 35-60 na venda)<br>
                • <b>Estrutura Micro (5m):</b> {conf.get('structure_5m', t.get('notes', 'Pullback e rejeição em pivô'))}<br>
                • <b>Evolução da Conta:</b> Saldo resultante de <b>R$ {t['balance_after_brl']:,.2f}</b> (Variação de {t['profit_brl']:+,.2f} BRL)
            </div>
            """,
                unsafe_allow_html=True,
            )
else:
    st.info("Nenhuma operação cadastrada.")

# ==============================================================================
# RODAPÉ INFORMATIVO
# ==============================================================================
st.markdown(
    """
<div style="text-align: center; color: #64748b; font-size: 0.75rem; margin-top: 2rem;">
    Sistema Autônomo Multiagente de Trading Quantitativo • Sincronizado com Maestri CLI & Streamlit Cloud
</div>
""",
    unsafe_allow_html=True,
)
