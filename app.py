import streamlit as st
import plotly.graph_objects as go

import trading_strategy as strategy


st.set_page_config(
    page_title="MSFT Trading Strategy",
    page_icon="MS",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f4f7fb; }
        [data-testid="stSidebar"] { background: #102a43; }
        [data-testid="stSidebar"] * { color: #f4f7fb; }
        .hero {
            background: linear-gradient(120deg, #102a43, #1f7a8c);
            border-radius: 14px;
            padding: 28px 32px;
            color: white;
            margin-bottom: 24px;
        }
        .hero h1 { margin: 0; font-size: 2.2rem; }
        .hero p { margin: 8px 0 0; color: #d9f0f2; }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #d9e2ec;
            border-radius: 10px;
            padding: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_strategy_data():
    data = strategy.get_stock_data("MSFT")
    data = strategy.calculate_moving_averages(data)
    data = strategy.identify_golden_cross(data)
    positions = strategy.implement_strategy(data)
    return data, positions


data, positions = load_strategy_data()

st.sidebar.title("MSFT Strategy")
st.sidebar.caption("Golden-cross backtest dashboard")
page = st.sidebar.radio(
    "Dashboard",
    ["Price chart", "Trade statistics", "Detailed trades"],
)

st.markdown(
    """
    <div class="hero">
        <h1>Microsoft trading strategy</h1>
        <p>Five-year view of price momentum, moving averages, and simulated trades.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Price chart":
    st.subheader("Price and moving averages")
    st.caption("Buy markers show golden-cross entries. Sell markers show simulated exits.")

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            name="MSFT close",
            mode="lines",
            line={"color": "#102a43", "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA50"],
            name="50-day MA",
            mode="lines",
            line={"color": "#1f7a8c", "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA200"],
            name="200-day MA",
            mode="lines",
            line={"color": "#f4a261", "width": 2},
        )
    )

    buy_points = data[data["GoldenCross"]]
    figure.add_trace(
        go.Scatter(
            x=buy_points.index,
            y=buy_points["Close"],
            name="Buy",
            mode="markers",
            marker={"color": "#2a9d8f", "size": 11, "symbol": "triangle-up"},
        )
    )

    if not positions.empty:
        sell_dates = positions["SellDate"].tolist()
        sell_points = data[data.index.isin(sell_dates)]
        figure.add_trace(
            go.Scatter(
                x=sell_points.index,
                y=sell_points["Close"],
                name="Sell",
                mode="markers",
                marker={"color": "#e76f51", "size": 11, "symbol": "triangle-down"},
            )
        )

    figure.update_layout(
        height=620,
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        legend={"orientation": "h", "y": 1.05, "x": 0},
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis={"title": "Date", "showgrid": False},
        yaxis={"title": "Price (USD)", "gridcolor": "#e9eef5"},
    )
    st.plotly_chart(figure, use_container_width=True)

elif page == "Trade statistics":
    st.subheader("Overall trade statistics")

    if positions.empty:
        st.info("No trading signals were detected for this period.")
    else:
        total_trades = len(positions)
        winning_trades = int((positions["ProfitPct"] > 0).sum())
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100
        average_profit = positions["ProfitPct"].mean()
        average_holding = positions["HoldingDays"].mean()
        target_trades = int((positions["SellReason"] == "Target reached").sum())
        max_period_trades = int((positions["SellReason"] == "Max holding period").sum())

        first_row = st.columns(4)
        first_row[0].metric("Total trades", total_trades)
        first_row[1].metric("Win rate", f"{win_rate:.2f}%")
        first_row[2].metric("Average profit", f"{average_profit:.2f}%")
        first_row[3].metric("Average holding", f"{average_holding:.1f} days")

        st.write("")
        second_row = st.columns(4)
        second_row[0].metric("Winning trades", winning_trades)
        second_row[1].metric("Losing trades", losing_trades)
        second_row[2].metric("Target reached", target_trades)
        second_row[3].metric("Max holding period", max_period_trades)

        st.subheader("Profit distribution")
        profit_figure = go.Figure(
            go.Bar(
                x=[f"Trade {index + 1}" for index in positions.index],
                y=positions["ProfitPct"],
                marker_color=[
                    "#2a9d8f" if profit > 0 else "#e76f51"
                    for profit in positions["ProfitPct"]
                ],
            )
        )
        profit_figure.update_layout(
            height=360,
            yaxis_title="Profit (%)",
            xaxis_title="Trade",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
        )
        st.plotly_chart(profit_figure, use_container_width=True)

else:
    st.subheader("Detailed trade records")
    if positions.empty:
        st.info("No trading signals were detected for this period.")
    else:
        display_positions = positions.copy()
        for column in ["BuyDate", "SellDate"]:
            display_positions[column] = display_positions[column].dt.strftime("%Y-%m-%d")
        display_positions["BuyPrice"] = display_positions["BuyPrice"].map("${:,.2f}".format)
        display_positions["SellPrice"] = display_positions["SellPrice"].map("${:,.2f}".format)
        display_positions["ProfitPct"] = display_positions["ProfitPct"].map("{:.2f}%".format)
        display_positions = display_positions.rename(
            columns={
                "BuyDate": "Buy date",
                "BuyPrice": "Buy price",
                "SellDate": "Sell date",
                "SellPrice": "Sell price",
                "HoldingDays": "Holding days",
                "ProfitPct": "Profit",
                "SellReason": "Sell reason",
            }
        )
        st.dataframe(display_positions, use_container_width=True, hide_index=True)