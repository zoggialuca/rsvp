import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Event RSVP", page_icon="🎉")

# Setup connection to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="List")
except Exception as e:
    st.error("Please configure Google Sheets Secrets in Streamlit Cloud.")
    st.stop()

# Force column types right away and clean up empty cells
df = df.astype({
    'name': str,
    'group_id': str,
    'attending': str,
    'food_preference': str
})
df = df.fillna("")

# Get the 'group' from the URL query parameters (e.g., ?group=101)
url_group_id = st.query_params.get("group")

if not url_group_id:
    st.title("📅 Event Invitation")
    st.info("Please use your group's personal link to RSVP.")
    st.stop()

# Find all members belonging to this group ID
group_members = df[df['group_id'] == url_group_id]

if group_members.empty:
    st.error("Invalid group invitation link. Please verify your link.")
else:
    # Use the first member's name to personalize the welcome message
    primary_guest = group_members.iloc[0]['name']
    
    st.title("Luca and Ben wedding party!")
    st.write("_When:_ **Sat 10 Apr 2027 18:00**")
    st.write("_Where:_ [*Ristorante Ai Sette Nani*](https://maps.app.goo.gl/M5T9kSUeiPYRqAay6) Via Grave di Sopra, 37/a, 31045 Ponte di Piave TV, Italy")

    with st.form("rsvp_form"):
        form_data = []
        
        for idx, member in group_members.iterrows():
            st.subheader(f"Guest: {member['name']}")
            
            # Attending Radio Setup
            current_status = member['attending'].strip()
            opts = ["Yes", "No", "Pending"]
            # Default to 'Pending' if the current status isn't Yes or No
            default_idx = opts.index(current_status) if current_status in opts else 2
            
            status = st.radio(
                f"Will {member['name']} be attending?", 
                opts, 
                index=default_idx, 
                key=f"s_{idx}", # Using row index as a unique key
                horizontal=True
            )
            
            # Answer Question
            food = st.text_input(
                "Dietary needs / Special requests?", 
                value=member['food_preference'],
                key=f"f_{idx}"
            )
            
            # Keep track of the row index so we can update the correct row later
            form_data.append({
                "row_index": idx, 
                "attending": status, 
                "food_preference": food
            })
            st.divider()

        if st.form_submit_button("Submit"):
            # Update the dataframe using the tracked row indexes
            for entry in form_data:
                df.loc[entry['row_index'], 'attending'] = entry['attending']
                df.loc[entry['row_index'], 'food_preference'] = entry['food_preference']
            
            # Save back to Google Sheets
            conn.update(data=df)
            st.success("Group responses updated successfully! Thank you.")
            st.balloons()
