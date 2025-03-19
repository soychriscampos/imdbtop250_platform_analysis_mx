import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("data/imdb_top250.csv")

# Separing platforms
df["Plataforma"] = df["Plataforma"].str.split(", ")
df = df.explode("Plataforma").reset_index(drop=True)

# Position in ranking
df = df.reset_index()
df.rename(columns={"index": "Pos IMDb"}, inplace=True)
df["Pos IMDb"] += 1

# st.title("Análisis sobre el Top 250 de IMDb en Plataformas de Streaming en México")
# st.title("Análisis sobre las mejores 250 películas de IMDb en Plataformas de Streaming en México")
st.title("Análisis de Disponibilidad: ¿Dónde Ver las Mejores 250 Películas de IMDb en Plataformas de Streaming en México?")
st.markdown("Actualización: 18 de marzo de 2025 | Por: [Christian Campos](https://x.com/soychriscampos)")
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(f"""
**📌 Sobre este análisis:**
Este estudio analiza en qué plataformas de streaming en México están disponibles las películas del **Top 250 de IMDb**. 

- Los datos fueron obtenidos de **IMDb** (Top 250) y **JustWatch** (plataformas de streaming).
- **No se tomaron en cuenta** películas disponibles solo para **compra o renta** en plataformas digitales.
- **No se incluyeron "Channels" dentro de plataformas** (ej. *HBO Max en Amazon Channel*).
- Si una película **solo estaba disponible para compra/renta**, se consideró como **"Ninguna Plataforma"**.
- Se consideraron únicamente **las suscripciones estándar de cada plataforma**.

⚠️ **Dado que algunas plataformas realizan cambios constantes en sus catálogos de películas, algunos títulos podrían no encontrarse al momento de tu consulta, sugiero revises la fecha de actualización de la parte de arriba para una mejor orientación.**
""")
st.markdown("<hr>", unsafe_allow_html=True)

# Cake-chart
st.subheader("Panorama General:")
st.markdown("¿Dónde se encuentran las películas?")
platform_counts = df["Plataforma"].value_counts()

category_num = 6
if len(platform_counts) > category_num:
    top_platforms = platform_counts.nlargest(category_num - 1)
    other_platforms = platform_counts.iloc[category_num -1:].sum()
    top_platforms["Otra"] = other_platforms
else:
    top_platforms = platforms_counts

fig, ax = plt.subplots(figsize=(8,6))
fig.patch.set_alpha(0)
ax.set_facecolor("none")

# colors
colors = sns.color_palette("Blues", len(top_platforms))
colors = [(r*0.8, g*0.8, b*0.9) for r, g, b in colors[::-1]]
top_platforms.plot(kind="pie", autopct=lambda p: f'{p:.1f}%', startangle=140, ax=ax,
                   colors=colors,
                  textprops={'color': "white"})
ax.set_ylabel("")
st.pyplot(fig)


st.markdown("<hr>", unsafe_allow_html=True)
# Platform Selection:
st.subheader("Selecciona una plataforma:")
plataform = st.selectbox("", df["Plataforma"].unique())

# Data over platform
filter_df = df[df["Plataforma"] == plataform][["Pos IMDb","Título Original", "Título Alternativo", "Año", "Calificación", "Duración (min)", "Género"]]


st.dataframe(df, hide_index=True)

# Platform summary
st.subheader("Resumen de la Plataforma")
# Movies / platform
st.markdown(f"Se encontraron **{filter_df.shape[0]}** películas en **{plataform}**")

# Top Genres
genres = filter_df["Género"].str.split(", ").explode()
top_generos = genres.value_counts().head(3).index.tolist()
st.markdown(f"🎭 **Géneros más comunes:** {', '.join(top_generos)}")

# Avg duration
duracion_promedio = round(filter_df["Duración (min)"].mean())
st.markdown(f"⏳ **Duración promedio de las películas:** {duracion_promedio} min.")

# Avg rating
calificacion_promedio = round(filter_df["Calificación"].mean(), 1)
st.markdown(f"⭐ **Calificación promedio de las películas:** {calificacion_promedio} (imdb).")

# oldest and newest
oldest_movie = filter_df[filter_df["Año"] == filter_df["Año"].min()]["Título Original"].values[0]
newest_movie = filter_df[filter_df["Año"] == filter_df["Año"].max()]["Título Original"].values[0]
st.markdown(f"🎞 **Película más antigua:** {oldest_movie} ({filter_df['Año'].min()}).")
st.markdown(f"🎬 **Película más reciente:** {newest_movie} ({filter_df['Año'].max()}).")

# decade movie
filter_df["Década"] = (filter_df["Año"] // 10) * 10
decades = filter_df["Década"].value_counts().sort_index()

st.subheader(f"Distribución de Películas por Década en **{plataform}**.")
st.markdown("Para saber en qué década se hicieron mas películas:")
st.bar_chart(decades)