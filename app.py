import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(page_title="株価分析アプリ", page_icon="📈", layout="wide")

# タイトル
st.title("📈 株価分析アプリ")
st.markdown("---")

# サイドバー
st.sidebar.header("設定")

# ティッカーシンボル入力
ticker = st.sidebar.text_input(
    "ティッカーシンボルを入力してください",
    value="AAPL",
    help="例: AAPL (Apple), GOOGL (Google), 7203.T (トヨタ), TSLA (Tesla)",
)

# 移動平均線の設定
st.sidebar.subheader("移動平均線設定")
ma1_period = st.sidebar.number_input(
    "移動平均線1の期間", min_value=1, max_value=200, value=20
)
ma2_period = st.sidebar.number_input(
    "移動平均線2の期間", min_value=1, max_value=200, value=50
)
show_ma = st.sidebar.checkbox("移動平均線を表示", value=True)

# 期間選択
period_options = {
    "1日": "1d",
    "5日": "5d",
    "1ヶ月": "1mo",
    "3ヶ月": "3mo",
    "6ヶ月": "6mo",
    "1年": "1y",
    "2年": "2y",
    "5年": "5y",
}

selected_period = st.sidebar.selectbox(
    "表示期間を選択してください",
    options=list(period_options.keys()),
    index=5,  # デフォルトは1年
)

# データ取得と表示
if ticker:
    try:
        # 株価データ取得
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period_options[selected_period])
        info = stock.info

        if not hist.empty:
            # 通貨判定
            currency = info.get("currency", "USD")
            currency_symbol = "¥" if currency == "JPY" else "$"

            # 会社情報表示
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="会社名", value=info.get("longName", ticker))

            with col2:
                current_price = hist["Close"].iloc[-1]
                prev_price = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
                price_change = current_price - prev_price
                st.metric(
                    label="現在価格",
                    value=f"{currency_symbol}{current_price:.2f}",
                    delta=f"{price_change:.2f}",
                )

            with col3:
                market_cap = info.get("marketCap", "N/A")
                if market_cap != "N/A":
                    if currency == "JPY":
                        market_cap_t = market_cap / 1e12  # 兆円
                        st.metric(label="時価総額", value=f"¥{market_cap_t:.1f}兆")
                    else:
                        market_cap_b = market_cap / 1e9  # 10億ドル
                        st.metric(label="時価総額", value=f"${market_cap_b:.1f}B")
                else:
                    st.metric(label="時価総額", value="N/A")

            st.markdown("---")

            # チャート作成（株価チャートを大きく、出来高を小さく）
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=("株価チャート", "出来高"),
                row_heights=[0.8, 0.2],  # 株価80%、出来高20%
            )

            # ローソク足チャート
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist["Open"],
                    high=hist["High"],
                    low=hist["Low"],
                    close=hist["Close"],
                    name="株価",
                ),
                row=1,
                col=1,
            )

            # 移動平均線追加
            if show_ma:
                if len(hist) >= ma1_period:
                    hist[f"MA{ma1_period}"] = (
                        hist["Close"].rolling(window=ma1_period).mean()
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=hist[f"MA{ma1_period}"],
                            mode="lines",
                            name=f"{ma1_period}日移動平均",
                            line=dict(color="orange", width=2),
                        ),
                        row=1,
                        col=1,
                    )

                if len(hist) >= ma2_period and ma2_period != ma1_period:
                    hist[f"MA{ma2_period}"] = (
                        hist["Close"].rolling(window=ma2_period).mean()
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=hist[f"MA{ma2_period}"],
                            mode="lines",
                            name=f"{ma2_period}日移動平均",
                            line=dict(color="red", width=2),
                        ),
                        row=1,
                        col=1,
                    )

            # 出来高チャート
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist["Volume"],
                    name="出来高",
                    marker_color="lightblue",
                ),
                row=2,
                col=1,
            )

            # レイアウト設定
            fig.update_layout(
                title=f"{ticker} - {info.get('longName', ticker)}",
                xaxis_rangeslider_visible=False,
                height=700,  # 高さを増加
                showlegend=True,
            )

            fig.update_xaxes(title_text="日付", row=2, col=1)
            fig.update_yaxes(title_text=f"価格 ({currency_symbol})", row=1, col=1)
            fig.update_yaxes(title_text="出来高", row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

            # 統計情報
            st.markdown("---")
            st.subheader("📊 統計情報")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("最高値", f"{currency_symbol}{hist['High'].max():.2f}")
                st.metric("最安値", f"{currency_symbol}{hist['Low'].min():.2f}")

            with col2:
                volatility = hist["Close"].pct_change().std() * np.sqrt(252) * 100
                st.metric("年間ボラティリティ", f"{volatility:.1f}%")
                avg_volume = hist["Volume"].mean()
                st.metric("平均出来高", f"{avg_volume:,.0f}")

            with col3:
                returns = ((hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1) * 100
                st.metric(f"{selected_period}リターン", f"{returns:.1f}%")
                pe_ratio = info.get("trailingPE", "N/A")
                if pe_ratio != "N/A":
                    st.metric("PER", f"{pe_ratio:.1f}")
                else:
                    st.metric("PER", "N/A")

            with col4:
                dividend_yield = info.get("dividendYield", 0)
                if dividend_yield:
                    st.metric("配当利回り", f"{dividend_yield*100:.2f}%")
                else:
                    st.metric("配当利回り", "N/A")

                beta = info.get("beta", "N/A")
                if beta != "N/A":
                    st.metric("ベータ値", f"{beta:.2f}")
                else:
                    st.metric("ベータ値", "N/A")

            # 生データ表示オプション
            if st.checkbox("生データを表示"):
                st.subheader("📋 株価データ")
                st.dataframe(hist.tail(20))

        else:
            st.error(
                "データが見つかりませんでした。ティッカーシンボルを確認してください。"
            )

    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.info(
            "ティッカーシンボルの例: AAPL, GOOGL, MSFT, 7203.T (日本株の場合は.Tを追加)"
        )

else:
    st.info("左側のサイドバーでティッカーシンボルを入力してください。")

# フッター
st.markdown("---")
st.markdown("💡 **使い方のヒント:**")
st.markdown("- 米国株: AAPL, GOOGL, TSLA など")
st.markdown("- 日本株: 7203.T (トヨタ), 6758.T (ソニー) など (.T を追加)")
st.markdown("- その他の市場: 地域コードを追加 (.L for London, .PA for Paris など)")
