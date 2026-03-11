

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from groq import Groq
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
# -----------------------------
# PDF REPORT GENERATOR
# -----------------------------

def generate_pdf(chat_df):

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    c = canvas.Canvas(temp_file.name, pagesize=letter)

    y = 750

    c.setFont("Helvetica", 12)

    c.drawString(50, y, "Retail AI Chat Report")

    y -= 40

    for index, row in chat_df.iterrows():

        text = f"User: {row['User Query']}"
        c.drawString(50, y, text)
        y -= 20

        text = f"Bot: {row['Bot Response']}"
        c.drawString(50, y, text)
                y -= 30

        if y < 100:
            c.showPage()
            y = 750

    c.save()

    return temp_file.name

# -----------------------------
# LOAD DATASET FIRST (VERY IMPORTANT)
# -----------------------------
df = pd.read_csv("fmcg_cleaned_data.csv")

cat = "product_name"
sales = "sales_amount"
date = "transaction_month"

df[date] = pd.to_datetime(df[date], format="%m", errors="coerce")

# -----------------------------
# SESSION STATE (CHAT MEMORY)
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# GROQ AI CLIENT
# -----------------------------
from groq import Groq

# Replace with your Groq API key
GROQ_API_KEY = "GROQ_API_KEY"

client = Groq(api_key=GROQ_API_KEY)


# -----------------------------
# AI RESPONSE FUNCTION
# -----------------------------
def ai_response(question):

    try:

        completion = client.chat.completions.create(

            messages=[{
                "role": "user",
                "content": question
            }],

            model="llama-3.1-8b-instant"

        )

        return completion.choices[0].message.content

    except Exception as e:

        return f"AI error: {e}"

# -----------------------------
# AI INTENT DETECTION
# -----------------------------
def detect_intent(query):

    prompt = f"""
    Identify the intent of this retail analytics question.

    Possible intents:
    total_sales
    monthly_sales
    top_product
    sales_trend

    Question: {query}

    Respond ONLY with the intent name.
    """

    try:

        intent = ai_response(prompt)

        return intent.strip().lower()

    except:

        return "unknown"

# -----------------------------
# CHATBOT ENGINE
# -----------------------------
def chatbot(query):

    intent = detect_intent(query)

    if intent == "total_sales":

        total = df["sales_amount"].sum()

        return f"Total sales revenue is {total}"

    elif intent == "monthly_sales":

        monthly = df.groupby(df["transaction_month"].dt.month)["sales_amount"].sum()

        return monthly.to_string()

    elif intent == "top_product":

        top = df.groupby("product_name")["sales_amount"].sum().idxmax()

        return f"Top selling product is {top}"

    elif intent == "sales_trend":

        st.line_chart(sales_trend)

        return "Here is the sales trend chart."
    else:
        # AI fallback for any retail question
        data_context = df.head(50).to_string()
        prompt = f"""
        You are a retail analytics assistant.

        Here is sample data from the retail dataset:

        {data_context}

        User question: {query}

        Answer the question using the dataset context.
        """

        return ai_response(prompt)
# -----------------------------
# STREAMLIT UI THEME
# -----------------------------
st.markdown("""
<style>
.stApp {
background:linear-gradient(135deg,#020617,#1e1b4b);
color:#e9d5ff;
}

h1 {
text-align:center;
color:#a78bfa;
text-shadow:0 0 14px #a78bfa;
}

section[data-testid="stSidebar"] {
background:#020617;
border-right:2px solid #8b5cf6;
}
</style>
""", unsafe_allow_html=True)
# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("🧠 AI Insight Control")

st.sidebar.subheader("💡 Suggested Questions")

if st.sidebar.button("Show Total Sales"):
    st.session_state.chat_history.append(
        ("Show Total Sales", chatbot("total sales"),
        {"time": datetime.now(), "response_time": 0})
    )

if st.sidebar.button("Show Monthly Sales"):
    st.session_state.chat_history.append(
        ("Show Monthly Sales", chatbot("monthly sales"),
        {"time": datetime.now(), "response_time": 0})
    )

if st.sidebar.button("Top Selling Product"):
    st.session_state.chat_history.append(
        ("Top Selling Product", chatbot("top product"),
        {"time": datetime.now(), "response_time": 0})
    )

st.sidebar.info("Filter products & explore smart analytics")

product_filter = st.sidebar.selectbox(
    "🛍 Select Product",
    ["All"] + list(df[cat].unique())
)

if product_filter != "All":
    df = df[df[cat] == product_filter]


# -----------------------------
# DASHBOARD DATA
# -----------------------------
sales_by_product = df.groupby(cat)[sales].sum()
sales_trend = df.groupby(df[date].dt.month)[sales].sum()
top_product = sales_by_product.idxmax()


# -----------------------------
# TITLE
# -----------------------------
st.title("GenAI-Powered Retail Sales Analytics Chatbot")


# -----------------------------
# CHATBOT INTERFACE
# -----------------------------
st.subheader("💬 Conversational Retail Sales Analytics Assistant")
st.caption("Example questions you can ask:")

st.write("""
• What is the total sales revenue?
• Which product sells the most?
• Show monthly sales trend
• Show sales trend chart
""")

user_query = st.text_input("Ask something about sales")
if user_query:

    start = time.time()

    response = chatbot(user_query)

    end = time.time()

    response_time = round(end - start, 2)

    metadata = {
        "time": datetime.now(),
        "response_time": response_time
    }

    st.session_state.chat_history.append(
        (user_query, response, metadata)
    )


# -----------------------------
# DISPLAY CHAT HISTORY (CHAT BUBBLES)
# -----------------------------

for chat in st.session_state.chat_history:

    with st.chat_message("user"):
        st.write(chat[0])

    with st.chat_message("assistant"):
        st.write(chat[1])

        st.caption(
            f"Time: {chat[2]['time']} | Response time: {chat[2]['response_time']} sec"
        )

# -----------------------------
# DOWNLOAD CHAT REPORT
# -----------------------------

if st.session_state.chat_history:

    chat_df = pd.DataFrame([
        {
            "User Query": c[0],
            "Bot Response": c[1],
            "Timestamp": c[2]["time"],
            "Response Time": c[2]["response_time"]
        }
        for c in st.session_state.chat_history
    ])

    st.subheader("📥 Download Chat Report")

    col1, col2 = st.columns(2)

    # CSV download
    with col1:
        st.download_button(
            label="Download CSV",
            data=chat_df.to_csv(index=False),
            file_name="chat_report.csv",
            mime="text/csv"
        )

    # PDF download
    with col2:

        pdf_file = generate_pdf(chat_df)

        with open(pdf_file, "rb") as f:

            st.download_button(
                label="Download PDF",
                data=f,
                file_name="chat_report.pdf",
                mime="application/pdf"
            )
# -----------------------------
# KPI DASHBOARD
# -----------------------------
st.subheader("📊 Retail Performance Snapshot")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total Revenue", f"{df[sales].sum():,.0f}")
c2.metric("🧾 Total Transactions", len(df))
c3.metric("🏆 Best Selling Product", top_product)


# -----------------------------
# AI GENERATED SUMMARY
# -----------------------------

st.subheader("🤖 AI Retail Summary")

insight_prompt = f"""
Analyze this retail dataset summary:

Total Revenue: {df[sales].sum()}
Top Product: {top_product}
Transactions: {len(df)}

Give 3 short business insights.
"""

try:
    ai_summary = ai_response(insight_prompt)
    st.success(ai_summary)

except:
    st.success(f"""
🏆 Best selling product → {top_product}  
💰 Total revenue generated → {df[sales].sum():,.0f}  
📊 Monthly sales variation detected across transactions
""")

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("📈 Sales Insights")

g1, g2 = st.columns(2)

with g1:
    st.line_chart(sales_trend)

with g2:
    st.bar_chart(sales_by_product.head(5))
# -----------------------------
# AI CHART INSIGHTS
# -----------------------------

st.subheader("🧠 AI Chart Insight")

try:

    chart_prompt = f"""
    Analyze this retail sales data and provide a short business insight.

    Total Revenue: {df[sales].sum()}
    Total Transactions: {len(df)}
    Best Selling Product: {top_product}

    Monthly Sales:
    {sales_trend.to_string()}

    Explain key trends in simple business language.
    """

    insight = ai_response(chart_prompt)

    st.success(insight)

except:


    st.info("AI insight unavailable.")  
