import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Анализ расходов", page_icon="📊")

st.title("📊 Твой личный финансовый аналитик")

city = st.selectbox("Выбери свой город:", ["Москва", "Санкт-Петербург"])

# Загружаем медианы из нашего файла
@st.cache_data
def load_medians():
    return pd.read_csv("medians.csv")

medians_df = load_medians()
city_medians = medians_df[medians_df['city'] == city]

uploaded_file = st.file_uploader("Загрузи CSV с расходами (выгрузка из банка)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Для теста предположим, что у нас есть колонки 'Категория' и 'Сумма'
    # В реальности нужно будет написать парсер под формат твоего банка
    if 'Категория' in df.columns and 'Сумма' in df.columns:
        
        # Группируем траты пользователя по категориям
        user_spending = df.groupby('Категория')['Сумма'].sum().reset_index()
        user_spending.columns = ['category', 'user_amount']
        
        # Объединяем с медианами
        comparison = pd.merge(user_spending, city_medians, on='category', how='left')
        
        # Считаем отклонение
        comparison['deviation_%'] = ((comparison['user_amount'] - comparison['median']) / comparison['median']) * 100
        
        # Выводим график
        fig = px.bar(comparison, x='category', y=['user_amount', 'median'], 
                     barmode='group', title=f"Твои траты vs Медиана ({city})")
        st.plotly_chart(fig)

        # Выводим предупреждения
        st.subheader("Где ты переплачиваешь?")
        for index, row in comparison.iterrows():
            if row['deviation_%'] > 30:
                st.warning(f"⚠️ На категорию **{row['category']}** ты тратишь на **{row['deviation_%']:.0f}%** больше медианы! Вот скидки, которые помогут сэкономить:")
                st.write("- Скидка 15% в ресторане 'Вкусно и Точка' по студенческому")
                st.write("- Промокод на доставку продуктов")
            elif row['deviation_%'] < 0:
                st.success(f"✅ На категорию **{row['category']}** ты тратишь меньше медианы. Так держать!")
                
    else:
        st.error("В файле нет колонок 'Категория' и 'Сумма'. Проверь формат выгрузки.")
