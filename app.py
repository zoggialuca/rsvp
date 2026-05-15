import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

#test BEGIN

import gspread

st.title("Google Sheets Raw Connection Test")

try:
    # This reads the exact JSON structure from your secrets
    credentials = dict(st.secrets["connections"]["gsheets"])
    
    # Attempt a raw login using gspread (the underlying library)
    gc = gspread.service_account_from_dict(credentials)
    
    # Try to open the sheet
    sh = gc.open_by_url(credentials["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    
    st.success("🎉 Success! Connected directly to Google Sheets.")
    st.write("First row of data:", worksheet.row_values(1))

except Exception as e:
    st.error("❌ Connection failed with the following raw error:")
    st.code(str(e))

return if True

#test END

st.set_page_config(page_title="Event RSVP", page_icon="🎉")

# Setup connection to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
except Exception as e:
    st.error(e)
    st.error("Please configure Google Sheets Secrets in Streamlit Cloud.")
    st.stop()

# Get the 'code' from the URL query parameters
user_code = st.query_params.get("code")

if not user_code:
    st.title("📅 Event Invitation")
    st.info("Please use your personal link to RSVP.")
    st.stop()

# Find the guest and their group
current_user = df[df['guest_code'] == user_code]

if current_user.empty:
    st.error("Invalid invitation code. Please check your link.")
else:
    group_id = current_user.iloc[0]['group_id']
    group_members = df[df['group_id'] == group_id]
    
    st.title("🎉 Welcome!")
    st.write(f"RSVP for **{current_user.iloc[0]['name']}** and linked friends.")

    with st.form("rsvp_form"):
        form_data = []
        for _, member in group_members.iterrows():
            st.subheader(f"Guest: {member['name']}")
            
            # Attending Radio
            current_status = str(member.get('attending', 'Pending'))
            opts = ["Yes", "No", "Pending"]
            idx = opts.index(current_status) if current_status in opts else 2
            
            status = st.radio(f"Attending?", opts, index=idx, key=f"s_{member['guest_code']}", horizontal=True)
            
            # Answer Question
            food = st.text_input("Dietary needs / Special requests?", 
                                 value=member.get('food_preference', '') if pd.notnull(member.get('food_preference')) else '',
                                 key=f"f_{member['guest_code']}")
            
            form_data.append({"guest_code": member['guest_code'], "attending": status, "food_preference": food})
            st.divider()

        if st.form_submit_button("Submit All RSVPs"):
            for entry in form_data:
                df.loc[df['guest_code'] == entry['guest_code'], 'attending'] = entry['attending']
                df.loc[df['guest_code'] == entry['guest_code'], 'food_preference'] = entry['food_preference']
            
            conn.update(data=df)
            st.success("Responses updated! Thank you.")
            st.balloons()
