from __future__ import annotations

import streamlit as st
import sqlite3
import pandas as pd
import os
from typing import List

# Set page config for better aesthetics
st.set_page_config(
    page_title="World Data Visualizer",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0F2027, #203A43, #2C5364);
        color: #ffffff;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #00d2ff;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Database Connection
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "../storage")

# Define available databases
DATABASES = {
    "World Data": os.path.join(STORAGE_DIR, "world_data.db"),
    "Course Data": os.path.join(STORAGE_DIR, "course_data.db")
}

def get_connection(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def get_tables(db_path: str) -> List[str]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
    conn.close()
    return tables

def load_data(db_path: str, table: str) -> pd.DataFrame:
    conn = get_connection(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def save_data(db_path: str, table: str, df: pd.DataFrame) -> None:
    conn = get_connection(db_path)
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
        st.success(f"Successfully saved changes to {table}!")
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
    finally:
        conn.close()

# Sidebar
with st.sidebar:
    st.markdown("## 🔮 Navigation")
    
    # Database Selector
    selected_db_name = st.selectbox("Select Database", list(DATABASES.keys()))
    current_db_path = DATABASES[selected_db_name]


    if not os.path.exists(current_db_path):
        st.error(f"Database not found: {current_db_path}")
        st.stop()
    
    tables = get_tables(current_db_path)
    selected_table = st.selectbox("Select Database Table", tables)
    
    st.markdown("---")
    st.markdown("### 📊 Database Stats")
    total_size = os.path.getsize(current_db_path) / 1024
    st.caption(f"DB Size: {total_size:.2f} KB")
    st.caption(f"Total Tables: {len(tables)}")

# Main Content
st.markdown(f'<h1 class="main-header">{selected_db_name}: {selected_table}</h1>', unsafe_allow_html=True)

if selected_table:
    # Load data
    df = load_data(current_db_path, selected_table)
    
    # Display metrics in a nice row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    
    st.markdown("### 📝 Edit Data")
    st.info("Double click on a cell to edit. You can also add or delete rows.")
    
    # Data Editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch",
        key=f"editor_{selected_db_name}_{selected_table}",
        hide_index=True
    )
    
    # Save Button
    if st.button("💾 Save Changes", type="primary"):
        if not edited_df.equals(df):
            save_data(current_db_path, selected_table, edited_df)
            st.rerun()
        else:
            st.warning("No changes detected to save.")

else:
    st.write("Please select a table from the sidebar.")
