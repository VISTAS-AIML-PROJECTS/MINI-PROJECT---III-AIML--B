# ============================================================
# DemandIQ - Retail Demand Forecasting & Inventory Intelligence
# ============================================================

import streamlit as st
import pandas as pd
import joblib


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="DemandIQ",
    page_icon="📦",
    layout="wide"
)


# ============================================================
# SIMPLE PROFESSIONAL STYLING
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #080c14;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
}

.hero {
    background: linear-gradient(135deg, #101c35, #172554);
    padding: 30px;
    border-radius: 22px;
    border: 1px solid #263b66;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    font-size: 42px;
    margin-bottom: 5px;
}

.hero p {
    color: #a8c7ff;
    font-size: 17px;
}

[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #263449;
    border-radius: 16px;
    padding: 15px;
}

[data-testid="stSidebar"] {
    background-color: #0b111d;
}

h2, h3 {
    color: #f8fafc;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA AND MODEL
# ============================================================

@st.cache_data
def load_data():

    data = pd.read_csv("demandiq_data.csv")

    data["date"] = pd.to_datetime(data["date"])

    return data


@st.cache_resource
def load_model():

    return joblib.load("demandiq_model.pkl")


@st.cache_resource
def load_features():

    return joblib.load("demandiq_features.pkl")


df = load_data()

model = load_model()

features = load_features()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🎛️ Control Center")

    st.caption(
        "Configure your retail inventory"
    )

    st.divider()

    store = st.selectbox(
        "🏪 Select Store",
        sorted(df["store"].unique())
    )

    item = st.selectbox(
        "📦 Select Product",
        sorted(df["item"].unique())
    )

    current_stock = st.number_input(
        "📦 Current Stock",
        min_value=0,
        value=50,
        step=1
    )

    lead_time = st.number_input(
        "🚚 Supplier Lead Time",
        min_value=1,
        value=7,
        step=1
    )

    max_lead_time = st.number_input(
        "⏱️ Maximum Lead Time",
        min_value=1,
        value=10,
        step=1
    )

    analyze = st.button(
        "⚡ Analyze Inventory",
        use_container_width=True
    )


# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div class="hero">

<h1>📦 DemandIQ</h1>

<p>
Smart Demand. Smarter Inventory.
</p>

<p>
AI-powered retail demand forecasting and inventory
intelligence for smarter restocking decisions.
</p>

</div>
""", unsafe_allow_html=True)


# ============================================================
# START SCREEN
# ============================================================

if not analyze:

    st.subheader("👋 Welcome to DemandIQ")

    st.info(
        "Select a store and product, enter the current stock "
        "and supplier lead time, then click **Analyze Inventory**."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "🤖 AI Engine",
        "READY"
    )

    col2.metric(
        "📦 Inventory Engine",
        "READY"
    )

    col3.metric(
        "📈 Forecasting",
        "READY"
    )


# ============================================================
# DEMAND AND INVENTORY ANALYSIS
# ============================================================

if analyze:

    # --------------------------------------------------------
    # GET PRODUCT HISTORY
    # --------------------------------------------------------

    product_data = df[
        (df["store"] == store) &
        (df["item"] == item)
    ].sort_values("date")


    latest = product_data.iloc[-1]

    next_date = (
        latest["date"]
        + pd.Timedelta(days=1)
    )


    # --------------------------------------------------------
    # CREATE MODEL INPUT
    # --------------------------------------------------------

    input_data = pd.DataFrame([{

        "store": store,

        "item": item,

        "day": next_date.day,

        "month": next_date.month,

        "year": next_date.year,

        "day_of_week":
            next_date.dayofweek,

        "is_weekend":
            int(next_date.dayofweek >= 5),

        "lag_1":
            latest["sales"],

        "lag_7":
            product_data.iloc[-7]["sales"],

        "rolling_mean_7":
            product_data["sales"]
            .tail(7)
            .mean()

    }])


    # --------------------------------------------------------
    # AI PREDICTION
    # --------------------------------------------------------

    predicted_demand = model.predict(
        input_data[features]
    )[0]


    # --------------------------------------------------------
    # SALES STATISTICS
    # --------------------------------------------------------

    avg_sales = product_data["sales"].mean()

    max_sales = product_data["sales"].max()


    # --------------------------------------------------------
    # INVENTORY CALCULATIONS
    # --------------------------------------------------------

    safety_stock = (
        (max_sales * max_lead_time)
        -
        (avg_sales * lead_time)
    )


    reorder_point = (
        (avg_sales * lead_time)
        +
        safety_stock
    )


    safety_stock = max(
        0,
        safety_stock
    )


    reorder_point = max(
        0,
        reorder_point
    )


    # --------------------------------------------------------
    # STOCK COVERAGE
    # --------------------------------------------------------

    if predicted_demand > 0:

        days_of_stock = (
            current_stock /
            predicted_demand
        )

    else:

        days_of_stock = 0


    # --------------------------------------------------------
    # RESTOCK QUANTITY
    # --------------------------------------------------------

    restock_quantity = max(
        0,
        int(
            round(
                reorder_point -
                current_stock
            )
        )
    )


    # ========================================================
    # INVENTORY HEALTH
    # ========================================================

    st.subheader("📊 Inventory Health")

    col1, col2, col3, col4 = st.columns(4)


    col1.metric(
        "🔮 Tomorrow's Demand",
        f"{predicted_demand:.1f}"
    )


    col2.metric(
        "📦 Current Stock",
        f"{current_stock}"
    )


    col3.metric(
        "⏳ Stock Coverage",
        f"{days_of_stock:.1f} days"
    )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if current_stock <= reorder_point:

        status = "🔴 CRITICAL"

        col4.metric(
            "Inventory Status",
            status
        )

    elif current_stock <= reorder_point * 1.20:

        status = "🟠 WATCH"

        col4.metric(
            "Inventory Status",
            status
        )

    else:

        status = "🟢 HEALTHY"

        col4.metric(
            "Inventory Status",
            status
        )


    # ========================================================
    # RESTOCK DECISION
    # ========================================================

    st.subheader("🚨 Inventory Decision")


    if current_stock <= reorder_point:

        st.error(
            f"RESTOCK RECOMMENDED — "
            f"Current stock is below the reorder point "
            f"of {reorder_point:.0f} units."
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Suggested Restock",
            f"{restock_quantity} units"
        )

        col2.metric(
            "Safety Stock",
            f"{safety_stock:.0f} units"
        )

        col3.metric(
            "Reorder Point",
            f"{reorder_point:.0f} units"
        )


    elif current_stock <= reorder_point * 1.20:

        st.warning(
            f"MONITOR STOCK — "
            f"Inventory is approaching the reorder point "
            f"of {reorder_point:.0f} units."
        )


    else:

        st.success(
            f"STOCK LEVEL OK — "
            f"Current inventory is above the reorder point "
            f"of {reorder_point:.0f} units."
        )


    # ========================================================
    # STOCK POSITION
    # ========================================================

    st.subheader("📦 Stock Position")

    if reorder_point > 0:

        stock_ratio = (
            current_stock /
            reorder_point
        )

    else:

        stock_ratio = 1


    st.progress(
        min(
            1.0,
            max(
                0.0,
                stock_ratio
            )
        )
    )


    # ========================================================
    # DEMAND CHART
    # ========================================================

    st.subheader("📈 Recent Sales Trend")

    chart_data = (
        product_data[
            ["date", "sales"]
        ]
        .tail(30)
        .set_index("date")
    )


    st.line_chart(
        chart_data,
        height=350
    )


    # ========================================================
    # BUSINESS INSIGHTS
    # ========================================================

    st.subheader("🧠 DemandIQ Insights")

    col1, col2 = st.columns(2)


    with col1:

        if predicted_demand > avg_sales:

            st.info(
                f"📈 Expected demand is above the historical "
                f"average. Forecast: **{predicted_demand:.1f}** "
                f"units vs average **{avg_sales:.1f}** units."
            )

        else:

            st.info(
                f"📉 Expected demand is below the historical "
                f"average. Forecast: **{predicted_demand:.1f}** "
                f"units vs average **{avg_sales:.1f}** units."
            )


    with col2:

        st.info(
            f"📦 The calculated reorder point is "
            f"**{reorder_point:.0f} units** with "
            f"**{safety_stock:.0f} units** of safety stock."
        )


    # ========================================================
    # SHOP OWNER REPORT
    # ========================================================

    st.subheader("📄 Shop Owner Report")


    report = pd.DataFrame([{

        "Store":
            store,

        "Product":
            item,

        "Predicted Demand":
            round(
                predicted_demand,
                2
            ),

        "Current Stock":
            current_stock,

        "Stock Coverage":
            round(
                days_of_stock,
                1
            ),

        "Average Daily Sales":
            round(
                avg_sales,
                2
            ),

        "Safety Stock":
            round(
                safety_stock,
                2
            ),

        "Reorder Point":
            round(
                reorder_point,
                2
            ),

        "Suggested Restock":
            restock_quantity,

        "Status":
            status

    }])


    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # DOWNLOAD REPORT
    # ========================================================

    st.download_button(
        "⬇️ Download Inventory Report",

        report.to_csv(
            index=False
        ),

        "demandiq_inventory_report.csv",

        "text/csv",

        use_container_width=True
    )


    # ========================================================
    # MODEL PERFORMANCE
    # ========================================================

    st.subheader("🤖 AI Model Performance")

    col1, col2, col3 = st.columns(3)


    col1.metric(
        "MAE",
        "6.5353"
    )


    col2.metric(
        "RMSE",
        "8.5242"
    )


    col3.metric(
        "R² Score",
        "0.9270"
    )


    st.caption(
        "Random Forest model evaluated using the "
        "time-based test dataset."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        DemandIQ • AI-Driven Retail Demand Forecasting
        & Inventory Intelligence
        <br><br>
        Built for practical retail decision support
    </div>
    """,
    unsafe_allow_html=True
)