import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Анализ расходов", page_icon="📊")

st.title("📊 Твой личный финансовый аналитик")
st.write("Загрузи выписку из банка, и мы посмотрим, где ты переплачиваешь по сравнению с медианой по городу.")

# Выбор города (для MVP пока один)
city = st.selectbox("Выбери свой город:", ["Москва", "Санкт-Петербург"])

# Загрузка файла
uploaded_file = st.file_uploader("Загрузи CSV с расходами (выгрузка из банка)", type=["csv"])

if uploaded_file is not None:
    # Читаем файл
    df = pd.read_csv(uploaded_file)
    st.write("Вот твои первые транзакции:")
    st.dataframe(df.head())
else:
    st.info("Пожалуйста, загрузи файл, чтобы увидеть анализ.")
