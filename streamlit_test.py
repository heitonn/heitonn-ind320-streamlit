
import streamlit as st
import numpy as np

st.title("Collatz")

# Initialize session state with dynamic text on button
if "value" not in st.session_state:
    st.session_state.value = None
    st.session_state.started = False
    st.session_state.counter = 0
    button_label = 'Start'
else: 
    st.session_state.counter += 1 
    if st.session_state.value == 1:
        button_label = 'Success!'
    else: 
        if st.session_state.value % 2 == 0:
            button_label = 'Half it!'
        else:
            button_label = 'Tripple and add one'


# Lag knappen med dynamisk tekst
st.button(button_label, disabled=st.session_state.value == 1)


if not st.session_state.started:
    st.write('Try me')
else:
    st.write(st.session_state.value)

if not st.session_state.started:
    st.session_state.value = np.random.randint(1, 11)
    st.session_state.started = True

else:
    if st.session_state.value == 1:
        st.balloons()
    else:
        if st.session_state.value % 2 == 0:
            st.session_state.value //= 2
        else:
            st.session_state.value  = st.session_state.value * 3 + 1
st.write(f'Knappen er trykket {st.session_state.counter} ganger.')
