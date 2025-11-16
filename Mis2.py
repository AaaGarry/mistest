import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="CRM Dashboard", layout="wide")

# =========================================
# 1. 模拟数据（可替换为真实数据）
# =========================================

np.random.seed(42)

contacts = pd.DataFrame({
    "id": np.arange(1, 301),
    "stage": np.random.choice(
        ["Lead", "Prospect", "Negotiation", "Closed Won", "Closed Lost"],
        size=300, p=[0.35, 0.30, 0.20, 0.10, 0.05]
    ),
    "deal_value": np.random.uniform(2000, 20000, size=300),
    "created_date": pd.to_datetime(
        np.random.choice(
            pd.date_range("2024-01-01", "2025-01-01"),
            300
        )
    )
})

# 交易数据用于 RFM
tx = pd.DataFrame({
    "customer_id": np.random.randint(1, 501, size=3000),
    "amount": np.random.uniform(100, 5000, size=3000),
    "date": pd.to_datetime(
        np.random.choice(
            pd.date_range("2024-01-01", "2025-01-01"),
            3000
        )
    )
})

# =========================================
# 2. 全局筛选器
# =========================================

st.sidebar.header("全局筛选器")

start_date = st.sidebar.date_input("开始日期", contacts["created_date"].min())
end_date = st.sidebar.date_input("结束日期", contacts["created_date"].max())

mask = (contacts["created_date"] >= pd.to_datetime(start_date)) & \
       (contacts["created_date"] <= pd.to_datetime(end_date))

contacts_filtered = contacts[mask]


# =========================================
# 3. KPI 指标卡片
# =========================================

total_leads = len(contacts_filtered)
won = (contacts_filtered["stage"] == "Closed Won").sum()
lost = (contacts_filtered["stage"] == "Closed Lost").sum()
total = won + lost
win_rate = won / total if total else 0.0
revenue = contacts_filtered.loc[contacts_filtered["stage"] == "Closed Won", "deal_value"].sum()
pipeline_value = contacts_filtered.loc[
    contacts_filtered["stage"].isin(["Lead", "Prospect", "Negotiation"]),
    "deal_value"
].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("线索总数", total_leads)
col2.metric("Win Rate", f"{win_rate:.1%}")
col3.metric("已实现收入", f"${revenue:,.0f}")
col4.metric("Pipeline 金额", f"${pipeline_value:,.0f}")


# =========================================
# 4. 线索阶段柱状图（Funnel）
# =========================================

stage_stats = contacts_filtered.groupby("stage")["id"].count().reset_index()
stage_stats = stage_stats.sort_values("id", ascending=False)

chart = alt.Chart(stage_stats).mark_bar().encode(
    x=alt.X("id:Q", title="数量"),
    y=alt.Y("stage:N", sort="-x", title="阶段"),
    tooltip=["stage", "id"]
).properties(
    title="线索阶段数量"
)

st.altair_chart(chart, use_container_width=True)


# =========================================
# 5. Pipeline 价值趋势图（按月）
# =========================================

contacts_filtered["month"] = contacts_filtered["created_date"].dt.to_period("M").astype(str)

monthly = contacts_filtered.groupby("month")["deal_value"].sum().reset_index()

trend = alt.Chart(monthly).mark_line(point=True).encode(
    x="month:T",
    y="deal_value:Q",
    tooltip=["month", "deal_value"]
).properties(title="Pipeline 金额趋势")

st.altair_chart(trend, use_container_width=True)


# =========================================
# 6. RFM 客户价值分析
# =========================================

st.subheader("RFM 客户价值分析")

g = tx.groupby("customer_id")
today = tx["date"].max() + pd.Timedelta(days=1)

rfm = pd.DataFrame({
    "customer_id": g.size().index,
    "Recency": (today - g["date"].max()).dt.days,
    "Frequency": g.size(),
    "Monetary": g["amount"].sum()
})

rfm_chart = alt.Chart(rfm).mark_circle(size=60).encode(
    x="Recency:Q",
    y="Frequency:Q",
    color="Monetary:Q",
    tooltip=["customer_id", "Recency", "Frequency", "Monetary"]
).properties(title="RFM 客户分布")

st.altair_chart(rfm_chart, use_container_width=True)


# =========================================
# 7. A/B Test 分析
# =========================================

st.subheader("A/B Test 分析")

ab_mask = contacts_filtered["stage"].isin(["Lead", "Prospect", "Negotiation"])
eligible = contacts_filtered[ab_mask].copy()

eligible["variant"] = np.random.choice(["A", "B"], size=len(eligible))
eligible["responded"] = False
eligible.loc[eligible["variant"] == "A", "responded"] = (np.random.rand(sum(eligible["variant"] == "A")) < 0.20)
eligible.loc[eligible["variant"] == "B", "responded"] = (np.random.rand(sum(eligible["variant"] == "B")) < 0.28)

conv_df = eligible.groupby("variant")["responded"].mean().reset_index()
conv_df.rename(columns={"responded": "conversion"}, inplace=True)

conv_chart = alt.Chart(conv_df).mark_bar().encode(
    x="variant:N",
    y="conversion:Q",
    tooltip=["conversion"]
).properties(title="A/B 转化率对比")

st.altair_chart(conv_chart, use_container_width=True)