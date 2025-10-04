import streamlit as st
import pandas as pd
import io
import datetime

st.set_page_config(
    page_title="SpendWise - Financial Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Header styling */
.css-h5aa2j {
    background-color: #d9534f;
    color: white;
    padding: 30px 0;
    font-size: 32px;
    font-weight: bold;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 1000;
}
.css-h5aa2j h1 {
    color: white !important;
    margin: 0;
    font-size: 32px;
}
/* Card styling */
div.st-emotion-cache-1r4r9wr { /* Targets the main column block */
    padding: 10px;
}
.st-emotion-cache-vj1n9y { /* Targets markdown card background */
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    margin-bottom: 20px;
}
/* Spending metrics */
[data-testid="metric-container"] {
    background-color: #f5f0f0;
    border: 1px solid #d9534f;
    padding: 15px 20px;
    border-radius: 10px;
    color: #d9534f;
    overflow-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)




def get_week_of_month(date):
    """Calculates the approximate week number within a month."""
    return (date.day - 1) // 7 + 1

def parse_data(uploaded_file):
    """Reads the uploaded CSV and prepares the DataFrame."""
    try:
        data = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        df = pd.read_csv(data)
        
       
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

def get_date_filters(df):
    """Creates sidebar filters for year and month."""
    unique_years = sorted(df['Year'].unique(), reverse=True)
    
    
    latest_year = unique_years[0]
    latest_month_num = df[df['Year'] == latest_year]['Month'].max()
    latest_month_name = df[df['Month'] == latest_month_num]['MonthName'].iloc[0]


    selected_year = st.sidebar.selectbox("Select Year:", unique_years, index=0)
    
    months_in_year = df[df['Year'] == selected_year]['MonthName'].unique()
    
    try:
        default_month_index = list(months_in_year).index(latest_month_name)
    except:
        default_month_index = 0 
        
    selected_month_name = st.sidebar.selectbox("Select Month:", months_in_year, index=default_month_index)
    
    
    df_filtered = df[
        (df['Year'] == selected_year) & 
        (df['MonthName'] == selected_month_name)
    ]
    return df_filtered, selected_year, selected_month_name

def generate_contextual_tip(df_filtered):
    """Generates a saving tip based on the top spending categories."""
    if df_filtered.empty:
        return "No spending data available for this month to generate a specific tip."

    
    category_spending = df_filtered.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    
    if category_spending.empty:
        return "No categorized spending found. Start by categorizing your transactions!"

    top_categories = category_spending.head(2).index.tolist()
    
    tips_mapping = {
        'Groceries': "Try meal planning and buying in bulk to save on your Groceries. Check for weekly flyers!",
        'Restaurants': "Your spending on Restaurants is high. Consider cooking at home or bringing lunch to work 3-4 times a week.",
        'Transport': "Look into carpooling or using public transportation more often to reduce your Transport costs.",
        'Shopping': "Before making a purchase under Shopping, apply the 30-day rule: if you still want it after 30 days, buy it.",
        'Entertainment': "Seek out free or low-cost Entertainment options like local parks, libraries, or free community events.",
        'Utilities': "Reduce your Utilities bill by being mindful of energy use. Unplug devices and turn off lights when not in use.",
        'Rent': "Rent is a fixed cost. Look for ways to reduce flexible spending to offset this major expense.",
        
    }

    generic_tip = "Always review your smallest, recurring expenses—they add up quickly!"
    
    
    tip = "Focus on reducing spending in your top categories: **" + " and ".join(top_categories) + "**. "
    
   
    if top_categories:
        top_cat = top_categories[0]
        tip += tips_mapping.get(top_cat, generic_tip)
    
    return tip




def show_upload_page():
    """Renders the file upload screen."""
    st.title("SpendWise")
    st.subheader("Upload Your Bank Statement (CSV only)")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="uploader")
    
    if uploaded_file is not None:
        
        st.session_state['df_spent'] = parse_data(uploaded_file)
        
        if st.session_state['df_spent'] is not None:
            st.success("File uploaded and parsed successfully! Switch to the 'Manage' or 'Analyze' page.")
    else:
        st.session_state['df_spent'] = None

def show_manage_page():
    """Renders the monthly summary and savings tips."""
    st.markdown("<h1>SpendWise</h1>", unsafe_allow_html=True)
    
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("⚠️ Please go to the 'Upload' page to load and parse your bank statement first.")
        return

    df_spent = st.session_state['df_spent']
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent)

    total_spent = df_filtered['Amount'].sum()
    suggested_savings = total_spent * 0.2
    
    st.subheader(f"Monthly Summary ({selected_month_name} {selected_year})")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Spent This Month:", f"${total_spent:,.2f}")
    with col2:
        st.metric("Suggested Savings (20%):", f"${suggested_savings:,.2f}")

    st.markdown("---")

    st.subheader("💡 Saving Tip:")
    
    contextual_tip = generate_contextual_tip(df_filtered)
    st.info(contextual_tip)


def show_analyze_page():
    """Renders the analysis (charts and raw data table)."""
    st.markdown("<h1>SpendWise</h1>", unsafe_allow_html=True)
    
    if st.session_state.get('df_spent') is None or st.session_state['df_spent'].empty:
        st.warning("⚠️ Please go to the 'Upload' page to load and parse your bank statement first.")
        return

    df_spent = st.session_state['df_spent']
    df_filtered, selected_year, selected_month_name = get_date_filters(df_spent)
    
    st.subheader(f"Data Analysis ({selected_month_name} {selected_year})")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Category Spending (Bar Chart)")
        if not df_filtered.empty:
            
            pie_data = df_filtered.groupby('Category')['Amount'].sum().reset_index()
            
            st.bar_chart(pie_data, x='Category', y='Amount', color='#d9534f')
        else:
            st.info("No spending data for this period.")

    with col2:
        st.markdown("### Weekly Graph (Spending Trends)")
        if not df_filtered.empty:
            
            weekly_data = df_filtered.groupby('WeekOfMonth')['Amount'].sum().reset_index()
            weekly_data['Week'] = 'Week ' + weekly_data['WeekOfMonth'].astype(str)
            
            st.line_chart(weekly_data, x='Week', y='Amount', color='#5cb85c')
        else:
            st.info("No spending data for this period.")

    st.markdown("---")
    st.markdown("### Bank Statement (Filtered Data)")
    

    if not df_filtered.empty:
        st.dataframe(df_filtered[['Date', 'Category', 'Amount']].sort_values(by='Date'), 
                     use_container_width=True, 
                     hide_index=True)
    else:
        st.info("No transactions found for the selected period.")

def main():
   
    st.sidebar.title("SpendWise Navigation")

    if 'df_spent' not in st.session_state:
        st.session_state['df_spent'] = None
    
    page = st.sidebar.radio(
        "Go to:", 
        ("Upload", "Manage", "Analyze")
    )
    if page == "Upload":
        show_upload_page()
    elif page == "Manage":
        show_manage_page()
    elif page == "Analyze":
        show_analyze_page()

if __name__ == "__main__":
    main()