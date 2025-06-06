import streamlit as st
import pandas as pd
import pymysql

def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123456789',
            database='policeproject_4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None
    
# Fetch data from database
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    
# Streamlit UI
st.set_page_config(page_title="SecureCheck Police Dashboard", layout="wide")

st.title("🚨 SecureCheck: Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insights for law enforcement 🚓")

# Show full table  
st.header("📋 Police log Overview")
query = "SELECT * FROM policelog"
data = fetch_data(query)
st.dataframe(data, use_container_width=True)

# Quick Metrics
st.header("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_stops = data.shape[0]
    st.metric("Total Police Stops", total_stops)

with col2:
    arrests = data[data['stop_outcome'].str.contains("arrest", case=False, na=False)].shape[0]
    st.metric("Total Arrests", arrests)

with col3:
    warnings = data[data['stop_outcome'].str.contains("warning", case=False, na=False)].shape[0]
    st.metric("Total Warnings", warnings)

with col4:
    drug_related = data[data['drugs_related_stop'] == 1].shape[0]
    st.metric("Drug Related Stops", drug_related)
    
# Advanced Queries
st.header("🧩 Advanced Insights")

selected_query = st.selectbox("Select a Query to Run", [
    "Total Number of Police Stops",
    "Count of Stops by Violation Type",
    "Number of Arrests vs. Warnings",
    "Average Age of Drivers Stopped",
    "Top 5 Most Frequent Search Types",
    "Count of Stops by Gender",
    "Most Common Violation for Arrests"
])
query_map = {
    "Total Number of Police Stops": "SELECT COUNT(*) AS total_stops FROM policelog",
    "Count of Stops by Violation Type": "SELECT violation_type, COUNT(*) AS count FROM policelog GROUP BY violation_type",
    "Number of Arrests vs. Warnings": "SELECT action_taken, COUNT(*) AS count FROM policelog GROUP BY action_taken",
    "Average Age of Drivers Stopped": "SELECT AVG(driver_age) AS avg_age FROM policelog",
    "Top 5 Most Frequent Search Types": "SELECT search_type, COUNT(*) AS count FROM policelog GROUP BY search_type ORDER BY count DESC LIMIT 5",
    "Count of Stops by Gender": "SELECT driver_gender, COUNT(*) AS count FROM policelog GROUP BY driver_gender",
    "Most Common Violation for Arrests": "SELECT violation_type, COUNT(*) AS count FROM policelog WHERE action_taken='Arrest' GROUP BY violation_type ORDER BY count DESC LIMIT 1"
}

if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    st.write (result)
    # if not result.empty:
    #     st.write(result)
    # else:
    #     st.warning("No results found for the selected query.")

st.markdown("---")
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")

st.header("🔍 Custom Natural Language Filter")
st.markdown("Fill in the details below to get a natural language prediction of the stop outcome based on existing data.")

st.header("📝 Add New Police Log & Predict Outcome and Violation")

# Input form for all fields (excluding outputs)
with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    county_name = st.text_input("County Name")
    driver_gender = st.selectbox("Driver Gender", ["male", "female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"])

    durations = data['stop_duration'].dropna().unique()
    if len(durations) > 0:
        stop_duration = st.selectbox("Stop Duration", durations)
    else:
        st.warning("No stop duration data available.")
        stop_duration = ""

    vehicle_number = st.text_input("Vehicle Number")
    timestamp = pd.Timestamp.now()

    submitted = st.form_submit_button("Predict Stop Outcome & Violation")
    
if submitted:
    # Filter data for prediction
    filtered_data = data[
        (data['driver_gender'] == driver_gender) &
        (data['driver_age'] == driver_age) &
        (data['search_conducted'] == int(search_conducted)) &
        (data['stop_duration'] == stop_duration) &
        (data['drugs_related_stop'] == int(drugs_related_stop))
    ]

    # Predict stop_outcome and violation
    if not filtered_data.empty:
        predicted_outcome = filtered_data['stop_outcome'].mode()[0]
        predicted_violation = filtered_data['violation'].mode()[0]
    else:
        predicted_outcome = "warning"
        predicted_violation = "speeding"
        
# Natural language summary
    search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
    drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"

    st.markdown(f"""
    🚔 *Prediction Summary*

    - *Predicted Violation:* {predicted_violation}
    - *Predicted Stop Outcome:* {predicted_outcome}

    🗒️ A {driver_age}-year-old {driver_gender} driver in {county_name} was stopped at {stop_time.strftime('%I:%M %p')} on {stop_date}.
    {search_text}, and the stop {drug_text}.
    Stop duration: *{stop_duration}*.
    Vehicle Number: *{vehicle_number}*.
    """)