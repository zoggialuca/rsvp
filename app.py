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
    'group_id_base64': str,
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

# Find all members belonging to this group ID based on the initial load
group_members = df[df['group_id_base64'] == url_group_id]

if group_members.empty:
    st.error("Invalid group invitation link. Please verify your link.")
else:
    st.title("Luca and Ben's wedding!")
    st.write("**Sat 10 Apr 2027 18:00**")
    st.write("[**Ristorante Ai Sette Nani**](https://maps.app.goo.gl/M5T9kSUeiPYRqAay6) Via Grave di Sopra, 37/a, 31045 Ponte di Piave TV, Italy")

    with st.form("rsvp_form"):
        form_data = []
        
        for idx, member in group_members.iterrows():
            st.subheader(f"{member['name']}")
            
            # Attending Radio Setup
            current_status = member['attending'].strip()
            opts = ["Yes", "No", "Pending (In attesa di conferma)"]
            default_idx = opts.index(current_status) if current_status in opts else 2
            
            status = st.radio(
                f"Will {member['name']} be attending? ({member['name']} ci sarà)", 
                opts, 
                index=default_idx, 
                key=f"s_{idx}",
                horizontal=True
            )
            
            food = st.text_input(
                "Dietary needs / Special requests? (Esigenze per il cibo / Richieste particolari)", 
                value=member['food_preference'],
                key=f"f_{idx}"
            )
            
            # CRITICAL CHANGE: Track the guest by name or unique ID, NOT the old row index
            form_data.append({
                "name": member['name'], 
                "attending": status, 
                "food_preference": food
            })
            st.divider()

        if st.form_submit_button("Submit"):
            # 1. Clear Streamlit's internal cache and read a FRESH copy of the sheet
            st.cache_data.clear()
            fresh_df = conn.read(worksheet="List")
            fresh_df = fresh_df.fillna("")
            
            # 2. Map user changes dynamically onto the fresh data frame
            for entry in form_data:
                # Find the matching row in the new sheet by name to prevent misalignments
                condition = (fresh_df['group_id_base64'] == url_group_id) & (fresh_df['name'] == entry['name'])
                
                if not fresh_df[condition].empty:
                    fresh_df.loc[condition, 'attending'] = entry['attending']
                    fresh_df.loc[condition, 'food_preference'] = entry['food_preference']
            
            # 3. Overwrite with the fresh, safely modified dataframe
            conn.update(data=fresh_df)
            st.success("Thank you.")
            st.balloons()
