import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Анализ расходов", page_icon="📊", layout="wide")

st.title("📊 Твой личный финансовый аналитик (Уфа)")
st.write("Загрузи выписку из банка, и мы посмотрим, где ты переплачиваешь по сравнению с медианой по Уфе.")

# Загружаем медианы для Уфы
@st.cache_data
def load_medians():
    df = pd.read_csv("medians.csv")
    # Оставляем только Уфу
    return df[df['city'] == 'Уфа']

city_medians = load_medians()

uploaded_file = st.file_uploader("Загрузи CSV с расходами (выгрузка из банка)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Проверяем, что нужные колонки есть
    if all(col in df.columns for col in ['Дата', 'Категория', 'Сумма']):
        
        # Преобразуем дату в нормальный формат
        df['Дата'] = pd.to_datetime(df['Дата'])
        
        # --- БЛОК 1: ОБЩАЯ КАРТИНА ЗА ГОД ---
        st.header("📈 Твои траты за год vs Медиана")
        
        # Считаем годовые траты пользователя по категориям
        user_yearly = df.groupby('Категория')['Сумма'].sum().reset_index()
        user_yearly.columns = ['category', 'user_year_total']
        
        # Соединяем с медианами и считаем годовую медиану (месячная * 12)
        yearly_comparison = pd.merge(user_yearly, city_medians, on='category', how='left')
        yearly_comparison['median_year_total'] = yearly_comparison['median'] * 12
        
        # Строим общий график за год
        fig_year = px.bar(yearly_comparison, x='category', y=['user_year_total', 'median_year_total'], 
                          barmode='group', 
                          labels={'value': 'Сумма (руб)', 'variable': 'Тип', 'category': 'Категория'},
                          title="Общие годовые траты (Твои vs Медиана)")
        fig_year.update_traces(name='Твои траты', selector=dict(name='user_year_total'))
        fig_year.update_traces(name='Медиана', selector=dict(name='median_year_total'))
        st.plotly_chart(fig_year, use_container_width=True)

        st.divider() # Разделительная линия

        # --- БЛОК 2: АНАЛИЗ ПОСЛЕДНЕГО МЕСЯЦА ПО КАТЕГОРИЯМ ---
        st.header("🔍 Детальный анализ за последний месяц")
        
        # Находим последний месяц в данных пользователя
        last_month_date = df['Дата'].max().to_period('M')
        st.write(f"Анализируем месяц: **{last_month_date.strftime('%B %Y')}**")
        
        # Берем данные только за этот последний месяц
        last_month_df = df[df['Дата'].dt.to_period('M') == last_month_date]
        user_month = last_month_df.groupby('Категория')['Сумма'].sum().reset_index()
        user_month.columns = ['category', 'user_month_total']
        
        # Соединяем с медианами
        month_comparison = pd.merge(user_month, city_medians, on='category', how='left')
        month_comparison['deviation_%'] = ((month_comparison['user_month_total'] - month_comparison['median']) / month_comparison['median']) * 100

        # Создаем вкладки для каждой категории
        categories = month_comparison['category'].tolist()
        tabs = st.tabs(categories)

        for i, category in enumerate(categories):
            with tabs[i]:
                # Данные только для этой категории
                cat_data = month_comparison[month_comparison['category'] == category].iloc[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label=f"Твои траты на {category}", value=f"{cat_data['user_month_total']} ₽")
                with col2:
                    st.metric(label=f"Медиана по Уфе", value=f"{cat_data['median']} ₽")
                with col3:
                    st.metric(label="Отклонение", value=f"{cat_data['deviation_%']:.0f}%")

                # Строим ГИСТОГРАММУ (столбики) для этой категории
                df_plot = pd.DataFrame({
                    'Тип': ['Твои траты', 'Медиана'],
                    'Сумма': [cat_data['user_month_total'], cat_data['median']]
                })
                
                fig_cat = px.bar(df_plot, x='Тип', y='Сумма', color='Тип',
                                 title=f"Сравнение по категории: {category}",
                                 color_discrete_map={'Твои траты': '#ff7f0e', 'Медиана': '#1f77b4'},
                                 text_auto=True) # text_auto подпишет цифры над столбиками
                st.plotly_chart(fig_cat, use_container_width=True)

                # Выводим рекомендации
                if cat_data['deviation_%'] > 30:
                    st.error(f"⚠️ **Внимание!** Ты тратишь на {cat_data['deviation_%']:.0f}% больше медианы в этой категории.")
                    st.info("💡 **Вот предложения от партнеров:**\n- Скидка 15% в ресторане 'Вкусно и Точка'\n- Промокод на доставку продуктов")
                elif cat_data['deviation_%'] < 0:
                    st.success(f"✅ Отлично! Ты тратишь на {abs(cat_data['deviation_%']):.0f}% меньше медианы.")
                else:
                    st.info("👍 Твои траты в пределах нормы.")

    else:
        st.error("В файле нет колонок 'Дата', 'Категория' и 'Сумма'. Проверь формат.")
