import streamlit as st
import pandas as pd
import io
import datetime
import plotly.express as px

st.set_page_config(
    page_title="SpendWise - Financial Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #f7f7f7;
}
.main-header {
    background-color: #c9302c;
    color: white;
    padding: 20px 0;
    font-size: 36px;
    font-weight: 700;
    text-align: center;
    border-radius: 10px;
    margin-bottom: 30px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}
.main-header h1 {
    color: white !important;
    margin: 0;
    font-size: 36px;
}
.st-emotion-cache-vj1n9y { 
    background-color: #ffffff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    margin-bottom: 25px;
}
[data-testid="metric-container"] {
    background-color: #ffeeee; 
    border-left: 5px solid #c9302c;
    padding: 20px 25px;
    border-radius: 10px;
    color: #333;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}
[data-testid="stSidebar"] {
    background-color: #e5e5e5;
    padding: 20px;
    border-right: 1px solid #ccc;
}
.stAlert.st-emotion-cache-1f8p81k.e1qn4p672 { 
    background-color: #d9edf7;
    border-color: #bce8f1;
    color: #31708f;
    border-radius: 8px;
}
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}
</style>
""", unsafe_allow_html=True)

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
        elif file_type == 'pdf':
            st.error("PDF files are unsupported for accurate financial data extraction. Please convert your bank statement to CSV format to proceed.")
            return None
        else:
            st.error(f"Unsupported file type: .{file_type}. Please upload a CSV or supported format.")
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
        st.error(f"Error processing file. Ensure it has 'Date', 'Amount', and 'Category' columns: {e}")
        return None

def get_date_filters(df, yearly=False):
    unique_years = sorted(df['Year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Year:", unique_years, index=0)
    if yearly:
        df_filtered = df[df['Year'] == selected_year]
        selected_month_name = None
    else:
        months_in_year = df[df['Year'] == selected_year]['MonthName'].unique()
        latest_month_num = df[df['Year'] == selected_year]['Month'].max()
        latest_month_name = df[df['Month'] == latest_month_num]['MonthName'].iloc[0]
        try:
            default_month_index = list(months_in_year).index(latest_month_name)
        except:
            default_month_index = 0
        selected_month_name = st.sidebar.selectbox("Select Month:", months_in_year, index=default_month_index)
        df_filtered = df[(df['Year'] == selected_year) & (df['MonthName'] == selected_month_name)]
    return df_filtered, selected_year, selected_month_name

def generate_contextual_tip(df_filtered):
    if df_filtered.empty:
        return "No spending data available to generate a specific tip."
    category_spending = df_filtered.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    if category_spending.empty:
        return "No categorized spending found. Start by categorizing your transactions!"
    top_categories = category_spending.head(2).index.tolist()
    tips_mapping = {
        'Groceries': "Try meal planning and buying in bulk to save on Groceries. Check for weekly flyers!",
        'Restaurants': "Your spending on Restaurants is high. Consider cooking at home or bringing lunch to work 3-4 times a week.",
        'Transport': "Look into carpooling or using public transportation more often to reduce your Transport costs.",
        'Shopping': "Before making a purchase under Shopping, apply the 30-day rule: if you still want it after 30 days, buy it.",
        'Entertainment': "Seek out free or low-cost Entertainment options like local parks, libraries, or free community events.",
        'Utilities': "Reduce your Utilities bill by being mindful of energy use. Unplug devices and turn off lights when not in use.",
        'Rent': "Rent is a fixed cost. Look for ways to reduce flexible spending to offset this major expense.",
    }
    generic_tip = "Always review your smallest, recurring expenses—they add up quickly! Try setting spending limits."
    tip = "Focus on reducing spending in your top categories: **" + " and ".join(top_categories) + "**. "
    if top_categories:
        top_cat = top_categories[0]
        tip += tips_mapping.get(top_cat, generic_tip)
    return tip

def show_upload_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    st.subheader("Upload Your Bank Statement")
    st.info("⚠️ For accurate financial analysis, please upload a **CSV file** containing columns for 'Date', 'Amount', and 'Category'. PDF files are not supported for table extraction.")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv', 'pdf'], key="uploader")
    if uploaded_file is not None:
        st.session_state['df_spent'] = parse_data(uploaded_file)
        if st.session_state['df_spent'] is not None and not st.session_state['df_spent'].empty:
            st.success("File uploaded and parsed successfully! Navigate to the 'Manage' or 'Analyze' page.")
        elif st.session_state['df_spent'] is not None and st.session_state['df_spent'].empty:
            st.warning("File uploaded, but no relevant spending data (Amount > 0) was found after filtering.")
    else:
        st.session_state['df_spent'] = None

def show_manage_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("⚠️ Please go to the 'Upload' page to load your bank statement first.")
        return

    view_option = st.sidebar.radio("View Type:", ["Monthly", "Yearly"], index=0)
    df_spent = st.session_state['df_spent']
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent, yearly=(view_option=="Yearly"))

    total_spent = df_filtered['Amount'].sum()
    suggested_savings = total_spent * 0.2

    st.subheader(f"{view_option} Dashboard: {selected_year}" + (f" - {selected_month_name}" if selected_month_name else ""))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Spending:", f"${total_spent:,.2f}")
    with col2:
        st.metric("Savings Goal (20%):", f"${suggested_savings:,.2f}")

    st.markdown("---")
    st.subheader("💡 Contextual Saving Tip")
    st.info(generate_contextual_tip(df_filtered))
    st.markdown("---")
    st.subheader("Top Spending Categories")

    top_categories_df = df_filtered.groupby('Category')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False)
    if not top_categories_df.empty:
        top_categories_df['Percentage'] = (top_categories_df['Amount'] / top_categories_df['Amount'].sum()) * 100
        num_cols = min(3, len(top_categories_df))
        col_list = st.columns(num_cols)
        for idx, row in enumerate(top_categories_df.head(num_cols).itertuples(index=False)):
            with col_list[idx]:
                st.metric(
                    label=row.Category,
                    value=f"${row.Amount:,.2f}",
                    delta=f"{row.Percentage:.1f}% of total"
                )
    else:
        st.info("No spending data found for analysis.")

def show_analyze_page():
    st.markdown("<div class='main-header'><h1>SpendWise</h1></div>", unsafe_allow_html=True)
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("⚠️ Please go to the 'Upload' page to load your bank statement first.")
        return

    view_option = st.sidebar.radio("View Type:", ["Monthly", "Yearly"], index=0)
    df_spent = st.session_state['df_spent']
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent, yearly=(view_option=="Yearly"))

    st.subheader(f"Detailed Analysis: {selected_year}" + (f" - {selected_month_name}" if selected_month_name else ""))

    col1, col2 = st.columns(2)
    if not df_filtered.empty:
        with col1:
            st.markdown("### Spending Breakdown by Category")
            pie_data = df_filtered.groupby('Category')['Amount'].sum().reset_index()
            pie_data = pie_data.sort_values(by='Amount', ascending=True)  # ✅ ascending order

            fig_bar = px.bar(
                pie_data, x='Category', y='Amount', color='Category', 
                title='Category Spending (Bar Chart)', color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Amount ($)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("### Weekly Spending Trend")
            if view_option=="Monthly":
                weekly_data = df_filtered.groupby('WeekOfMonth')['Amount'].sum().reset_index()
                weekly_data['Week'] = 'Week ' + weekly_data['WeekOfMonth'].astype(str)
                x_col = 'Week'
            else:
                weekly_data = df_filtered.groupby(df_filtered['Date'].dt.month)['Amount'].sum().reset_index()
                weekly_data['Month'] = weekly_data['Date'].apply(lambda x: datetime.date(1900, x, 1).strftime('%B'))
                x_col = 'Month'
            fig_line = px.line(
                weekly_data, x=x_col, y='Amount', markers=True,
                line_shape='linear', color_discrete_sequence=['#5cb85c'],
                title='Spending Trend'
            )
            fig_line.update_layout(yaxis_title="Amount ($)", xaxis_title="")
            st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.info("No spending data for this period to generate charts.")

    st.markdown("---")
    st.markdown("### Raw Transaction Data")
    if not df_filtered.empty:
        st.dataframe(df_filtered[['Date', 'Category', 'Amount']].sort_values(by='Date'), use_container_width=True, hide_index=True)
    else:
        st.info("No transactions found for the selected period.")

def main():
    st.sidebar.title("SpendWise Navigation")
    if 'df_spent' not in st.session_state:
        st.session_state['df_spent'] = None
    page = st.sidebar.radio("Go to:", ("Upload", "Manage", "Analyze"))
    if page == "Upload":
        show_upload_page()
    elif page == "Manage":
        show_manage_page()
    elif page == "Analyze":
        show_analyze_page()

if __name__ == "__main__":
    main()
