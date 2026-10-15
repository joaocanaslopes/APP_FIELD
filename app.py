import os
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Navigator - Recolha de Campo", page_icon="🌲", layout="centered"
)

st.title("🌲 Navigator: Recolha de Dados de Campo")
st.markdown(
    "Sistema oficial de Active Data Harvesting e Diagnóstico Fitossanitário."
)

# Obter a Connection String do Supabase (compatível com Streamlit Secrets e Variáveis de Ambiente)
DATABASE_URL = None
try:
  if "DATABASE_URL" in st.secrets:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
  pass

if not DATABASE_URL:
  DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
  if not DATABASE_URL:
    st.error(
        "⚠️ A variável DATABASE_URL não está configurada. Adiciona-a aos"
        " Secrets no painel do Streamlit Cloud."
    )
    return None
  return psycopg2.connect(DATABASE_URL)


# Formulário de Recolha em Campo
with st.form("form_recolha_rigoroso"):
  st.subheader("📝 Formulário de Registo de Campo")
  st.markdown(
      "*Todos os campos marcados com asterisco (*) são de preenchimento"
      " obrigatório.*"
  )

  col1, col2 = st.columns(2)

  with col1:
    user_id = st.number_input("ID do Técnico (User ID) *", min_value=1, value=1, step=1)
    stand_id = st.number_input(
        "ID do Talhão (Stand ID) *", min_value=1, value=1, step=1
    )
    tree_age = st.number_input(
        "Idade da Árvore / Talhão (meses) *", min_value=1, value=36, step=1
    )

  with col2:
    plant_section = st.selectbox(
        "Parte da Planta (Secção) *", ["Base", "Meio", "Topo"]
    )
    soil_deficiency = st.selectbox(
        "Deficiência de Solo Conhecida (Manual) *",
        [
            "Nitrogénio (N)",
            "Fósforo (P)",
            "Potássio (K)",
            "Boro (B)",
            "Cálcio (Ca)",
            "Saudável",
        ],
    )
    manual_deficiency = st.selectbox(
        "Diagnóstico Manual do Técnico *",
        [
            "Nitrogénio (N)",
            "Fósforo (P)",
            "Potássio (K)",
            "Boro (B)",
            "Cálcio (Ca)",
            "Saudável",
        ],
    )

  st.markdown("---")
  st.markdown("📍 **Coordenadas GPS Obrigatórias**")
  col_lat, col_lon = st.columns(2)
  with col_lat:
    gps_lat = st.number_input("Latitude *", value=38.892100, format="%.6f")
  with col_lon:
    gps_lon = st.number_input("Longitude *", value=-9.083400, format="%.6f")

  st.markdown("---")
  uploaded_image = st.file_uploader(
      "📸 Fotografia da Folha/Árvore *", type=["jpg", "jpeg", "png"]
  )

  # Único campo estritamente opcional
  extra_notes = st.text_area(
      "Observações Extra (Opcional)",
      placeholder=(
          "Ex: Solo muito seco, forte incidência de vento, sintomas visíveis"
          " nas margens..."
      ),
  )

  submitted = st.form_submit_button("Submeter Registo Completo")

  if submitted:
    # Validação rigorosa de obrigatoriedade da imagem
    if uploaded_image is None:
      st.error(
          "⚠️ Erro: A fotografia da folha/árvore é obrigatória para submeter o"
          " registo!"
      )
    else:
      try:
        conn = get_db_connection()
        if conn:
          cur = conn.cursor()

          # Outputs simulados do modelo de IA
          app_predicted_class = "Boro"
          app_probabilities = '{"N": 0.02, "P": 0.01, "K": 0.03, "Boro": 0.89, "Calcio": 0.03, "Saudavel": 0.02}'
          image_path_simulado = f"/storage/images/{uploaded_image.name}"

          expert_validated_class = None
          is_verified_for_retraining = False

          query = """
                        INSERT INTO field_observations 
                        (
                            user_id, stand_id, gps_latitude, gps_longitude, 
                            tree_age_months, plant_section, soil_deficiency, 
                            extra_notes, manual_deficiency, app_predicted_class, 
                            app_probabilities, image_path, expert_validated_class, 
                            is_verified_for_retraining
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

          cur.execute(
              query,
              (
                  user_id,
                  stand_id,
                  gps_lat,
                  gps_lon,
                  tree_age,
                  plant_section,
                  soil_deficiency,
                  extra_notes if extra_notes else None,
                  manual_deficiency,
                  app_predicted_class,
                  app_probabilities,
                  image_path_simulado,
                  expert_validated_class,
                  is_verified_for_retraining,
              ),
          )

          conn.commit()
          cur.close()
          conn.close()

          st.success(
              "✅ Registo completo submetido e validado com sucesso na base de"
              " dados do Supabase!"
          )
          st.info(
              f"🤖 **Diagnóstico da IA (Simulado):** {app_predicted_class}"
              " (89% de confiança)"
          )
      except Exception as e:
        st.error(
            f"Erro ao inserir registo na base de dados (certifica-te de que o"
            f" User ID e Stand ID existem nas respetivas tabelas): {e}"
        )
