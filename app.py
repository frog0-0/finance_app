import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Анализ расходов (Уфа)", page_icon="📊", layout="wide")

st.title("📊 DataSmart - Твой личный финансовый аналитик")

RECOMMENDATIONS = {
    "Кафе и рестораны": {
        "text": "«Додо-пицца»: скидка 15% при заказе в ресторане.",
        "link": "https://example.com/dodo",
        "link_text": "Получить скидку",
        "instruction": "Промокод на скидку в описании к посту."
    },
    "Транспорт": {
        "text": "Ты тратишь много на проезд. Советуем купить транспортную карту «Алга».",
        "link": "https://alga-card.ru/stores/",
        "link_text": "Где купить карту «Алга»",
        "instruction": "Карту можно купить у кондукторов в автобусах «Башавтотранс» или в магазинах сети «Байрам». Проезд по ней значительно выгоднее."
    },
    "Хобби и развлечения": {
        "text": "Скидка 20% на билеты в кинотеатр «Синема Парк» (ТРК «Галерея АРТ») по промокоду.",
        "link": "https://example.com/sinema-promo",
        "link_text": "Забрать промокод",
        "instruction": "Введите промокод при покупке билета онлайн."
    },
    "Супермаркеты": {
        "text": "Студенческая скидка 10% по вторникам в сети супермаркетов «Байрам».",
        "link": "https://example.com/bayram-student",
        "link_text": "Узнать подробности",
        "instruction": "Предъявите студенческий билет на кассе перед оплатой."
    },
    "Одежда и обувь": {
        "text": "Скидка 15% на весь ассортимент в магазине «SNEAKER STORE» (ТРК «Июнь»).",
        "link": "https://example.com/sneaker-store-promo",
        "link_text": "Получить скидку",
        "instruction": "Скажите на кассе промокод из поста."
    },
    "ЖКХ и связь": {
        "text": "Специальный молодежный тариф от МегаФон, Билайн и МТС для членов профсоюза УГНТУ.",
        "link": "https://vk.ru/wall-24636249_32527",
        "link_text": "Перейти на тариф",
        "instruction": "Оформите переход в личном кабинете или в салоне связи."
    }
}

@st.cache_data
def load_medians():
    # Читаем файл с медианами
    df = pd.read_csv("medians.csv")
    # Убираем возможные пробелы в названиях колонок и категорий
    df.columns = df.columns.str.strip()
    df['category'] = df['category'].str.strip()
    return df[df['city'] == 'Уфа']

city_medians = load_medians()

uploaded_file = st.file_uploader("Загрузи CSV с расходами (выгрузка из банка)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Очищаем названия колонок и категорий от лишних пробелов на всякий случай
    df.columns = df.columns.str.strip()
    df['Категория'] = df['Категория'].str.strip()
    
    if all(col in df.columns for col in ['Дата', 'Категория', 'Сумма']):
        
        df['Дата'] = pd.to_datetime(df['Дата'])
        
        # --- БЛОК 1: ГОД ---
        st.header("📈 Твои траты за год vs Медиана")
        
        user_yearly = df.groupby('Категория')['Сумма'].sum().reset_index()
        user_yearly.columns = ['category', 'user_year_total']
        
        yearly_comparison = pd.merge(user_yearly, city_medians, on='category', how='left').fillna(0)
        yearly_comparison['median_year_total'] = yearly_comparison['median'] * 12
        
        fig_year = px.bar(yearly_comparison, x='category', y=['user_year_total', 'median_year_total'], 
                          barmode='group', 
                          labels={'value': 'Сумма (руб)', 'variable': 'Тип', 'category': 'Категория'},
                          title="Общие годовые траты (Твои vs Медиана)")
        fig_year.update_traces(name='Твои траты', selector=dict(name='user_year_total'))
        fig_year.update_traces(name='Медиана', selector=dict(name='median_year_total'))
        st.plotly_chart(fig_year, use_container_width=True)

        st.divider()

        # --- БЛОК 2: ПОСЛЕДНИЙ МЕСЯЦ ---
        st.header("🔍 Детальный анализ за последний месяц")
        
        last_month_date = df['Дата'].max().to_period('M')
        st.write(f"Анализируем месяц: **{last_month_date.strftime('%B %Y')}**")
        
        last_month_df = df[df['Дата'].dt.to_period('M') == last_month_date]
        user_month = last_month_df.groupby('Категория')['Сумма'].sum().reset_index()
        user_month.columns = ['category', 'user_month_total']
        
        month_comparison = pd.merge(user_month, city_medians, on='category', how='left').fillna(0)
        
        month_comparison['deviation_%'] = np.where(month_comparison['median'] > 0, 
            ((month_comparison['user_month_total'] - month_comparison['median']) / month_comparison['median']) * 100, 0)

        categories = month_comparison['category'].tolist()
        tabs = st.tabs(categories)

        for i, category in enumerate(categories):
            with tabs[i]:
                cat_data = month_comparison[month_comparison['category'] == category].iloc[0]
                
                col1, col2, col3 = st.columns(3)
                col1.metric(label=f"Твои траты", value=f"{cat_data['user_month_total']} ₽")
                col2.metric(label=f"Медиана по Уфе", value=f"{cat_data['median']} ₽")
                col3.metric(label="Отклонение", value=f"{cat_data['deviation_%']:.0f}%")

                df_plot = pd.DataFrame({
                    'Тип': ['Твои траты', 'Медиана'],
                    'Сумма': [cat_data['user_month_total'], cat_data['median']]
                })
                
                fig_cat = px.bar(df_plot, x='Тип', y='Сумма', color='Тип',
                                 title=f"Сравнение по категории: {category}",
                                 color_discrete_map={'Твои траты': '#ff7f0e', 'Медиана': '#1f77b4'},
                                 text_auto=True)
                st.plotly_chart(fig_cat, use_container_width=True)

                # --- ЛОГИКА РЕКОМЕНДАЦИЙ (С ЗАЩИТОЙ ОТ НУЛЕЙ) ---
                if cat_data['median'] == 0:
                    st.warning("⚠️ Для этой категории пока нет данных о медиане по Уфе. Мы не можем провести анализ.")
                elif cat_data['deviation_%'] > 30:
                    st.error(f"⚠️ **Внимание!** Ты тратишь на {cat_data['deviation_%']:.0f}% больше медианы в этой категории.")
                    
                    rec = RECOMMENDATIONS.get(category)
                    if rec:
                        with st.container(border=True):
                            st.subheader("💡 Как сэкономить?")
                            st.write(rec["text"])
                            st.markdown(f"👉 **Как это работает:** {rec['instruction']}")
                            st.link_button(rec["link_text"], rec["link"])
                elif cat_data['deviation_%'] < 0:
                    st.success(f"✅ Отлично! Ты тратишь на {abs(cat_data['deviation_%']):.0f}% меньше медианы.")
                else:
                    st.info("👍 Твои траты в пределах нормы.")
    else:
        st.error("В файле нет колонок 'Дата', 'Категория' и 'Сумма'.")
