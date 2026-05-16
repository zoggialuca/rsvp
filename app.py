import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Event RSVP", page_icon="🎉")

# Setup connection to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 1. Read the raw data
    df = conn.read(usecols=list(range(5)))
    
    # 2. Force the column types explicitly
    df = df.astype({
        'guest_code': str,        # Keeps codes like '00123' or 'A1B2' as pure text
        'name': str,              # Explicit string
        'group_id': str,          # CRITICAL: Treats IDs as text so '101' doesn't become '101.0'
        'attending': str,         # Text status ('Yes', 'No', 'Pending')
        'food_preference': str    # Text answers
    })
    
    # 3. Clean up missing/empty values (NaN) so they don't break your text boxes
    df = df.fillna("")
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
