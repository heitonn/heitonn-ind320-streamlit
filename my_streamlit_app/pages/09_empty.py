import streamlit as st

# Title and wide layout
st.set_page_config(layout="wide")
st.header("Dear Streamlit" )

# Dividing page in two columns
col1, col2 = st.columns(2)

with col1:
    st.write("""
        I just wanna tell you how I'm feeling \n
        Gotta make you understand \n
        Never gonna give you up \n
        Never gonna let you down \n
        Never gonna run around and desert you \n
        Never gonna make you cry \n
        Never gonna say goodbye \n
        Never gonna tell a lie and hurt you \n
            """)
with col2:
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

