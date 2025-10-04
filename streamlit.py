import streamlit as st
import pandas as pd
import io
import datetime
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(
    page_title="SpendWise - Financial Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #f7f7f7; }
.main-header { background-color: #c9302c; color: white; padding: 20px 0; font-size: 36px; font-weight: 700; text-align: center; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15); }
.st-emotion-cache-vj1n9y { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); margin-bottom: 25px; }
[data-testid="metric-container"] { background-color: #ffeeee; border-left: 5px solid #c9302c; padding: 20px 25px; border-radius: 10px; color: #333; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); }
[data-testid="stSidebar"] { background-color: #e5e5e5; padding: 20px; border-right: 1px solid #ccc; }
.stAlert.st-emotion-cache-1f8p81k.e1qn4p672 { background-color: #d9edf7; border-color: #bce8f1; color: #31708f; border-radius: 8px; }
.stDataFrame { border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def get_week_of_month(date):
    return (date.day - 1) // 7 + 1

def parse_data(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    df = None
    try:
        if file_type == 'csv':
            data = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            df = pd.read_csv(data)
            st.success("CSV file loaded successfully.")
        else:
            st.error(f"Unsupported file type: .{file_type}. Please upload CSV.")
            return None

        df.columns = [col.strip() for col in df.columns]
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df.dropna(subset=['Date', 'Amount'], inplace=True)
        
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.strftime('%B')
        df['WeekOfMonth'] = df['Date'].apply(get_week_of_month)
        
        df_spent = df[df['Amount'] > 0].copy()
        df_spent = df_spent[~df_spent['Category'].isin(['Savings', 'Income'])].copy()
        
        return df_spent
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

def get_date_filters(df, view_type="Monthly"):
    if view_type == "Monthly":
        unique_years = sorted(df['Year'].unique(), reverse=True)
        latest_year = unique_years[0]
        latest_month_num = df[df['Year'] == latest_year]['Month'].max()
        latest_month_name = df[df['Month'] == latest_month_num]['MonthName'].iloc[0]

        selected_year = st.sidebar.selectbox("Select Year:", unique_years, index=0)
        months_in_year = df[df['Year'] == selected_year]['MonthName'].unique()
        default_month_index = list(months_in_year).index(latest_month_name) if latest_month_name in months_in_year else 0
        selected_month_name = st.sidebar.selectbox("Select Month:", months_in_year, index=default_month_index)
        
        df_filtered = df[(df['Year'] == selected_year) & (df['MonthName'] == selected_month_name)]
        return df_filtered, selected_year, selected_month_name
    else:  # Yearly
        unique_years = sorted(df['Year'].unique(), reverse=True)
        selected_year = st.sidebar.selectbox("Select Year:", unique_years, index=0)
        df_filtered = df[df['Year'] == selected_year]
        return df_filtered, selected_year, None

def generate_contextual_tip(df_filtered):
    if df_filtered.empty:
        return "No spending data available for this period."
    category_spending = df_filtered.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    if category_spending.empty:
        return "No categorized spending found. Start categorizing your transactions!"
    top_categories = category_spending.head(2).index.tolist()
    tips_mapping = {
        'Groceries': "Try meal planning and buying in bulk.",
        'Restaurants': "Consider cooking at home 3-4 times a week.",
        'Transport': "Use public transportation or carpool.",
        'Shopping': "Apply the 30-day rule before purchases.",
        'Entertainment': "Seek free or low-cost entertainment.",
        'Utilities': "Be mindful of energy use and unplug devices.",
        'Rent': "Reduce flexible spending to offset rent costs.",
    }
    generic_tip = "Review recurring small expenses—they add up!"
    tip = "Focus on reducing spending in: **" + " and ".join(top_categories) + "**. "
    if top_categories:
        tip += tips_mapping.get(top_categories[0], generic_tip)
    return tip

# --- Pages ---
def show_upload_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    st.subheader("Upload Your Bank Statement")
    st.info("⚠️ Upload a CSV file with columns: 'Date', 'Amount', 'Category'.")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="uploader")
    
    if uploaded_file is not None:
        st.session_state['df_spent'] = parse_data(uploaded_file)
        if st.session_state['df_spent'] is not None and not st.session_state['df_spent'].empty:
            st.success("File uploaded successfully!")
        else:
            st.warning("No relevant spending data found.")

    # Salary input
    st.subheader("💰 Enter Your Monthly Salary")
    salary = st.number_input("Monthly Salary ($):", min_value=0.0, value=0.0, step=100.0)
    st.session_state['salary'] = salary

def show_manage_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("Please upload your bank statement first.")
        return

    df_spent = st.session_state['df_spent']
    view_type = st.radio("View Type:", ["Monthly", "Yearly"], horizontal=True)
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent, view_type=view_type)

    total_spent = df_filtered['Amount'].sum()
    salary = st.session_state.get('salary', 0)
    suggested_savings = salary * 0.2 if salary > 0 else total_spent * 0.2

    title = f"{view_type} Dashboard: {selected_month_name+' ' if selected_month_name else ''}{selected_year}"
    st.subheader(title)

    col1, col2 = st.columns(2)
    col1.metric("Total Spending:", f"${total_spent:,.2f}")
    col2.metric("Savings Goal (20%):", f"${suggested_savings:,.2f}")

    st.markdown("---")
    st.subheader("💡 Contextual Saving Tip")
    st.info(generate_contextual_tip(df_filtered))
    
    st.markdown("---")
    st.subheader("Top Spending Categories")
    top_categories_df = df_filtered.groupby('Category')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False)
    if not top_categories_df.empty:
        top_categories_df['Percentage'] = (top_categories_df['Amount'] / top_categories_df['Amount'].sum()) * 100
        col_list = st.columns(min(3, len(top_categories_df)))
        for i, row in top_categories_df.head(3).iterrows():
            with col_list[i]:
                st.metric(row['Category'], f"${row['Amount']:,.2f}", f"{row['Percentage']:.1f}% of total")
    else:
        st.info("No spending data found.")

def show_analyze_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("Please upload your bank statement first.")
        return

    df_spent = st.session_state['df_spent']
    view_type = st.radio("View Type:", ["Monthly", "Yearly"], horizontal=True)
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent, view_type=view_type)

    title = f"Detailed Analysis: {selected_month_name+' ' if selected_month_name else ''}{selected_year}"
    st.subheader(title)

    col1, col2 = st.columns(2)
    if not df_filtered.empty:
        with col1:
            st.markdown("### Spending Breakdown by Category")
            pie_data = df_filtered.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(pie_data, values='Amount', names='Category', title='Spending Distribution', hole=.3, color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
            fig_pie.update_layout(showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("### Weekly/Monthly Spending Trend")
            if view_type == "Monthly":
                weekly_data = df_filtered.groupby('WeekOfMonth')['Amount'].sum().reset_index()
                weekly_data['Week'] = 'Week ' + weekly_data['WeekOfMonth'].astype(str)
                fig_line = px.line(weekly_data, x='Week', y='Amount', title='Total Spent per Week', markers=True, color_discrete_sequence=['#5cb85c'])
            else:  # Yearly
                monthly_data = df_filtered.groupby('MonthName')['Amount'].sum().reset_index()
                month_order = pd.to_datetime(monthly_data['MonthName'], format='%B').dt.month
                monthly_data = monthly_data.iloc[month_order.argsort()]
                fig_line = px.line(monthly_data, x='MonthName', y='Amount', title='Total Spent per Month', markers=True, color_discrete_sequence=['#5cb85c'])
            fig_line.update_layout(yaxis_title="Amount ($)", xaxis_title="")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No spending data for this period.")

    st.markdown("---")
    st.markdown("### Raw Transaction Data")
    if not df_filtered.empty:
        st.dataframe(df_filtered[['Date', 'Category', 'Amount']].sort_values(by='Date'), use_container_width=True, hide_index=True)
    else:
        st.info("No transactions found.")

def show_predict_page():
    st.markdown("<div class='main-header'><h1>SpendWise - Forecast</h1></div>", unsafe_allow_html=True)
    
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("Please upload your bank statement first.")
        return

    df_spent = st.session_state['df_spent']
    salary = st.session_state.get('salary', 0)

    st.subheader("💹 Forecasting Expenses and Savings (Linear Regression)")

    # --- Prepare data ---
    df_monthly = df_spent.groupby(['Year', 'Month'])['Amount'].sum().reset_index()
    df_monthly['MonthNum'] = (df_monthly['Year'] - df_monthly['Year'].min()) * 12 + df_monthly['Month']

    X = df_monthly[['MonthNum']].values
    y = df_monthly['Amount'].values

    if len(X) < 2:
        st.warning("Not enough data for linear regression forecast. Need at least 2 months of data.")
        return

    # --- Fit Linear Regression ---
    model = LinearRegression()
    model.fit(X, y)

    # --- Predict next 12 months ---
    last_month_num = df_monthly['MonthNum'].max()
    future_months = np.arange(last_month_num + 1, last_month_num + 13).reshape(-1, 1)
    predicted_spending = model.predict(future_months)

    # --- Prepare results ---
    predicted_monthly = pd.DataFrame({
        'MonthNum': future_months.flatten(),
        'PredictedSpending': predicted_spending
    })
    predicted_yearly = predicted_monthly['PredictedSpending'].sum()
    predicted_monthly_savings = [max(salary - x, 0) if salary > 0 else x*0.2 for x in predicted_spending]
    predicted_yearly_savings = sum(predicted_monthly_savings)

    # --- Display ---
    st.subheader("Predicted Monthly Spending & Savings (Next 12 Months)")
    for i, amt in enumerate(predicted_spending):
        st.write(f"Month {i+1}: Spending: ${amt:,.2f}, Savings: ${predicted_monthly_savings[i]:,.2f}")

    st.markdown("---")
    st.metric("Predicted Yearly Spending", f"${predicted_yearly:,.2f}")
    st.metric("Predicted Yearly Savings", f"${predicted_yearly_savings:,.2f}")

    # --- Plot ---
    st.subheader("📈 Predicted Spending Trend")
    fig = px.line(predicted_monthly, x='MonthNum', y='PredictedSpending', title="Next 12 Months Predicted Spending", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- Main ---
def main():
    st.sidebar.title("SpendWise Navigation")
    if 'df_spent' not in st.session_state:
        st.session_state['df_spent'] = None
    if 'salary' not in st.session_state:
        st.session_state['salary'] = 0

    page = st.sidebar.radio("Go to:", ("Upload", "Manage", "Analyze", "Predict"))

    if page == "Upload":
        show_upload_page()
    elif page == "Manage":
        show_manage_page()
    elif page == "Analyze":
        show_analyze_page()
    elif page == "Predict":
        show_predict_page()

if __name__ == "__main__":
    main()
