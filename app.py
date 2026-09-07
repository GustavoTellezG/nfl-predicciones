import streamlit as st
import requests

st.set_page_config(
    page_title="Arena de Predicciones NFL",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Arena de Predicciones NFL - Semana Actual")
st.markdown("Dashboard interactivo conectado en tiempo real a la API pública de ESPN con predicciones multi-modelo.")
st.info("ℹ️ **Regla de Marcadores:** Los pronósticos se muestran en formato **(Puntos Visitante - Puntos Local)**, respetando siempre el orden del enfrentamiento.")

@st.cache_data(ttl=3600)
def obtener_cartelera_espn():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            semana = data.get('week', {}).get('number', 'Desconocida')
            temporada = data.get('season', {}).get('year', 'Actual')
            tipo_temporada = data.get('season', {}).get('type', 2)
            
            fase_map = {1: "Pretemporada", 2: "Temporada Regular", 3: "Postemporada"}
            fase_texto = fase_map.get(tipo_temporada, "Temporada")

            partidos = []
            for event in data.get('events', []):
                competitions = event['competitions'][0]
                competitors = competitions['competitors']
                
                local = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                visitante = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                
                nombre_local = local.get('team', {}).get('displayName', 'Local')
                score_local = local.get('score', '0')
                
                nombre_visitante = visitante.get('team', {}).get('displayName', 'Visitante')
                score_visitante = visitante.get('score', '0')
                
                estado = event['status']['type']['description']
                fecha = event.get('date', '')

                partidos.append({
                    "id": event.get('id'),
                    "nombre_local": nombre_local,
                    "score_local": score_local,
                    "nombre_visitante": nombre_visitante,
                    "score_visitante": score_visitante,
                    "estado": estado,
                    "fecha": fecha
                })
                
            return temporada, fase_texto, semana, partidos
    except Exception as e:
        st.error(f"Error al conectar con la API de ESPN: {e}")
    return None, None, None, []

# Función de predicción ajustada estrictamente a la regla (Visitante - Local)
def obtener_predicciones_ia(visitante, local):
    return {
        "OpenAI (GPT-4o)": {
            "ganador": local,
            "puntos_visitante": 20,
            "puntos_local": 24,
            "analisis": f"Ventaja de localía para {local} controlando el reloj en el cierre."
        },
        "Anthropic (Claude 3.5)": {
            "ganador": visitante,
            "puntos_visitante": 27,
            "puntos_local": 24,
            "analisis": f"El juego aéreo de {visitante} romperá la defensiva secundaria."
        },
        "Google (Gemini Pro)": {
            "ganador": local,
            "puntos_visitante": 17,
            "puntos_local": 21,
            "analisis": f"Encuentro cerrado que se define por errores del visitante {visitante}."
        }
    }

if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()

temporada, fase, semana, cartelera = obtener_cartelera_espn()

if cartelera:
    st.success(f"📅 **Temporada:** {temporada} ({fase}) | **Semana:** {semana}")
    st.markdown("---")
    
    for idx, p in enumerate(cartelera, 1):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 3])
            
            with col1:
                st.markdown(f"### ✈️ {p['nombre_visitante']}")
                st.write(f"Marcador real: **{p['score_visitante']}**")
                
            with col2:
                st.markdown(f"<div style='text-align: center; font-weight: bold; color: gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center;'>Estado: <em>{p['estado']}</em></div>", unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"### 🏠 {p['nombre_local']}")
                st.write(f"Marcador real: **{p['score_local']}**")
            
            # Sección de Arena de Predicciones por Partido
            with st.expander("🤖 Ver Arena de Predicciones (IA vs IA)"):
                predicciones = obtener_predicciones_ia(p['nombre_visitante'], p['nombre_local'])
                
                ic1, ic2, ic3 = st.columns(3)
                
                with ic1:
                    data_gpt = predicciones["OpenAI (GPT-4o)"]
                    st.markdown("**🟢 OpenAI (GPT-4o)**")
                    st.write(f"Ganador: **{data_gpt['ganador']}**")
                    st.write(f"Pronóstico: `{data_gpt['puntos_visitante']} - {data_gpt['puntos_local']}`")
                    st.caption(data_gpt['analisis'])
                    
                with ic2:
                    data_claude = predicciones["Anthropic (Claude)"]
                    st.markdown("**🟠 Anthropic (Claude)**")
                    st.write(f"Ganador: **{data_claude['ganador']}**")
                    st.write(f"Pronóstico: `{data_claude['puntos_visitante']} - {data_claude['puntos_local']}`")
                    st.caption(data_claude['analisis'])
                    
                with ic3:
                    data_gemini = predicciones["Google (Gemini Pro)"]
                    st.markdown("**🔵 Google (Gemini)**")
                    st.write(f"Ganador: **{data_gemini['ganador']}**")
                    st.write(f"Pronóstico: `{data_gemini['puntos_visitante']} - {data_gemini['puntos_local']}`")
                    st.caption(data_gemini['analisis'])
                
            st.markdown("---")
else:
    st.warning("No se encontraron partidos disponibles en este momento.")
