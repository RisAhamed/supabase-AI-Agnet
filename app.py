import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Leads Dashboard", layout="wide")
st.title("🚀 AI Leads Dashboard")

# Sidebar for filters
st.sidebar.header("Filters")

# Hardcoded client_id for now (will make dynamic later)
client_id = st.sidebar.text_input("Client ID", value="test_client_1")

# Status filter
status_filter = st.sidebar.multiselect(
    "Filter by Status",
    options=["new", "contacted", "qualified", "closed-won", "closed-lost"],
    default=["new", "contacted", "qualified"]
)

# Source filter
source_filter = st.sidebar.multiselect(
    "Filter by Source",
    options=["website_form", "linkedin", "cold_email", "referral", "other"],
    default=None
)

# Date range filter
date_range = st.sidebar.date_input(
    "Filter by Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

st.sidebar.divider()

# Fetch data from Supabase
@st.cache_data(ttl=60)
def fetch_leads(client_id, status_list, source_list, start_date, end_date):
    try:
        # Start with base query
        query = supabase.table("leads").select("*").eq("client_id", client_id)
        
        # Apply filters
        if status_list:
            query = query.in_("status", status_list)
        
        response = query.execute()
        
        if not response.data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(response.data)
        
        # Convert created_at to datetime
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Apply date filter
        df = df[(df['created_at'].dt.date >= start_date) & 
                (df['created_at'].dt.date <= end_date)]
        
        # Apply source filter if selected
        if source_list:
            df = df[df['source'].isin(source_list)]
        
        # Sort by created_at descending
        df = df.sort_values('created_at', ascending=False)
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Fetch and display data
df_leads = fetch_leads(client_id, status_filter, source_filter, date_range[0], date_range[1])

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Leads", len(df_leads))

with col2:
    new_count = len(df_leads[df_leads['status'] == 'new'])
    st.metric("New Leads", new_count)

with col3:
    qualified_count = len(df_leads[df_leads['status'] == 'qualified'])
    st.metric("Qualified", qualified_count)

with col4:
    closed_won = len(df_leads[df_leads['status'] == 'closed-won'])
    st.metric("Closed Won", closed_won)

st.divider()

# Display table
if not df_leads.empty:
    st.subheader("Lead Pipeline")
    
    # Format for display
    display_df = df_leads[[
        'lead_name', 'lead_email', 'lead_phone', 'company', 
        'source', 'status', 'created_at', 'notes'
    ]].copy()
    
    display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download CSV
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"leads_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("No leads found for the selected filters.")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
