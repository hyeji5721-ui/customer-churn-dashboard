import streamlit as st

st.set_page_config(page_title="고객은 왜 이탈하는가", layout="wide")

pg = st.navigation(
    [
        st.Page("pages/1_대시보드.py", title="대시보드", icon="📊"),
        st.Page("pages/2_개선_제안_리포트.py", title="개선 제안 리포트", icon="📝"),
        st.Page("pages/3_채널_효율.py", title="채널 효율", icon="📈"),
    ]
)
pg.run()
