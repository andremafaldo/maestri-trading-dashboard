# 🏛️ PROTOCOLO OPERACIONAL INSTITUCIONAL MTF V1.0
**Sistema Multiagente de Trading Quantitativo / Híbrido**  
**Versão:** 1.0 (Calibração Definitiva Pós-Backtesting 6M e 1Y)  
**Status:** HOMOLOGADO / VIGENTE  

---

## 🎯 1. Filosofia de Operação e Governança
Este protocolo traduz as conclusões estatísticas obtidas em mais de **2.500 horas de pregão auditadas** nos mercados de **B3**, **Cripto** e **Commodities (Ouro)**.  
O objetivo central é maximizar a assertividade (*Win Rate* alvo de **~65% a 70%**), priorizando a preservação irrestrita de capital através de filtros multi-timeframe e janelas restritas de liquidez institucional.

---

## ⚡ 2. Matriz de Confluência Obrigatória (Orquestrador & Gatekeeper)

Toda e qualquer intenção de entrada (Paper Trading ou Live) deve satisfazer **cumulativamente** os 4 pilares:

### I. Filtro Macro de Tendência — MTF H1 (Regra Absoluta)
- **Compra:** Proibida se o gráfico de 60 minutos (H1) não estiver com `EMA 20 > EMA 50` e inclinação ascendente.
- **Venda:** Proibida se o gráfico de 60 minutos (H1) não estiver com `EMA 20 < EMA 50` e inclinação descendente.
- *Nenhuma divergência ou antecipação em tempo gráfico menor (5m) anula o veto do H1.*

### II. Calibração de Gestão de Risco & Alvos (Banca de R$ 1.000,00)
- **Banca Inicial Base:** **R$ 1.000,00 BRL**.
- **Risco Fixo por Trade:** **1,5% do capital atual** (**R$ 15,00** por operação simulada).
- **Alvo Risco:Retorno:** Fixado em **$1,1 : 1$** (**R$ 16,50** de lucro teórico por acerto na primeira zona de liquidez).
- **Dimensionamento Dinâmico de Posição:**
  - **B3 (WIN):** 1 minicontrato com Stop técnico contido na faixa de 75 a 150 pontos (máximo 200 pts).
  - **Cripto (BTC) & Ouro (XAU):** Lote fracionado ajustado para que a distância do Stop técnico resulte exatamente no risco financeiro de **R$ 15,00**.
- **Stop Loss Estrutural:** Ancorado obrigatoriamente atrás da mínima (compra) ou máxima (venda) do pivô de pullback com buffer de segurança.
- **Travas de Risco Máximo (Veto do Gatekeeper Baluarte):**
  - **Mini-Índice B3 (WIN):** Stop técnico máximo de **200 pontos**.
  - **Cripto (BTC/USDT):** Stop técnico máximo de **$350,00 USD**.
  - **Commodities (XAU/USD):** Stop técnico máximo de **$6,00 USD**.

### III. Trava de Estrutura Maior (Lição do Backlog XAU)
- **Veto de Resistência/Suporte Maior:** É expressamente vetada qualquer compra se o alvo projetado de $1,1 : 1$ estiver localizado **além da máxima semanal anterior ou de resistência estática do gráfico diário**.
- De forma análoga, vetam-se vendas cujo alvo esteja aquém da mínima semanal ou suporte estático diário.

### IV. Ancoragem Institucional (VWAP & Bollinger)
- Compras exigem preço operando **acima da VWAP** da sessão e fora de sobrecompra extrema ($IFR < 65$).
- Vendas exigem preço operando **abaixo da VWAP** da sessão e fora de sobrevenda extrema ($IFR > 35$).
- Proibida entrada com Bandas de Bollinger em compressão severa (*Squeeze*) sem candle de expansão.

---

## ⏱️ 3. Governança Temporal por Esquadrão

A auditoria histórica comprovou que fora dos horários de liquidez institucional os modelos geram falso sinal e ruído estatístico. Aplica-se bloqueio compulsório:

| Esquadrão | Ativos de Foco | Janelas Autorizadas | Janelas Bloqueadas / Veto Compulsório |
| :--- | :--- | :--- | :--- |
| **🇧🇷 [ESQUADRÃO B3]** | `WIN` / `WDO` | **10:00 às 11:55 BRT** e **13:00 às 14:55 BRT** | ❌ 09:00–10:00 (Abertura ruído) \| 11:55–13:00 (Almoço, WR 13%) \| Após 15:00 (Fim de pregão) |
| **🪙 [ESQUADRÃO CRIPTO]** | `BTC/USDT` | **08:00 às 17:00 UTC** (05:00 às 14:00 BRT) | ❌ 17:00 às 08:00 UTC (Sessão Asiática / Madrugada, PF 0.75) |
| **🏆 [ESQUADRÃO COMMODITIES]**| `XAU/USD` | **00:00 às 07:00 UTC** (Ásia) e **12:00 às 15:00 UTC** (NY) | ❌ Após as 16:00 UTC (Tarde NY, PF 0.76) \| 13:00–13:30 UTC (Notícias macro) |

---

## 👥 4. Atribuições dos Subagentes no Canvas Maestri

1. **`PRINCIPAL` (Orquestrador Central):**
   - Centraliza o fluxo de deliberação.
   - Aplica a matriz de confluência e confere a autorização final das 3 saídas: `[COMPRA]`, `[VENDA]` ou `[AGUARDAR / NEUTRO]`.
2. **`Vetor` (Tendência & Momentum):**
   - Monitora EMA 20 e EMA 50 no H1 e EMA 8/21 nos 5m.
   - Exige alinhamento angular estrito antes de liberar sinal direcional.
3. **`Estrato` (Zonas de Retenção & Volatilidade):**
   - Mapeia suportes/resistências na VWAP, Pivots e retrações de Fibonacci.
   - Aplica a Trava de Estrutura Maior (máximas/mínimas semanais e diárias).
4. **`Sentinela` (Contexto & Governança Temporal):**
   - Controla o relógio de liquidez institucional de cada esquadrão.
   - Aciona a flag `[ALERTA VERMELHO / BLOQUEIO]` em divulgações macroeconômicas (CPI, NFP, FOMC, Copom) e fora das janelas autorizadas.
5. **`Baluarte` (Risco & Execução - Gatekeeper):**
   - Valida o Risco:Retorno de $1,1 : 1$.
   - Fiscaliza as Travas de Risco Máximo (450 pts WIN / $350 BTC / $6,00 XAU).
   - Possui autoridade soberana de veto em qualquer violação de parâmetro.

---

## 🔒 5. Estado Operacional
O sistema permanece em **MODO DE ESPERA PASSIVO (STANDBY)** com seus esquadrões e agentes em escuta no canvas do Maestri. Nenhuma ordem será despachada sem gatilho explícito e estrito cumprimento deste protocolo.
