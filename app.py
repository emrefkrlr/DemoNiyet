import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Swiss AI Rental Pro", layout="wide", page_icon="🇨🇭")

# --- API ANAHTARI (SECRETS) ---
# Streamlit Cloud Dashboard -> Settings -> Secrets kısmına GROQ_API_KEY eklemiş olmalısın.
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Hata: API anahtarı (Secrets) bulunamadı. Lütfen Streamlit Cloud ayarlarını kontrol edin.")
    st.stop()

# --- UI SÖZLÜĞÜ ---
UI_LANGS = {
    "Türkçe": {
        "title": "İsviçre Emlak Başvuru Sihirbazı",
        "name": "Ad Soyad", "partner": "Eş/Partner Bilgisi", "job": "Mesleğiniz", 
        "income": "Toplam Gelir (CHF)", "location": "Aranan Şehir", "rooms": "Oda Sayısı",
        "lifestyle": ["Sigara Yok", "Hayvan Yok", "Sakin Yaşam"], "note": "Özel Not", "btn": "Mektubu CV ile Zenginleştir 🚀",
        "out_lang_label": "🎯 Mektup Dili (Çıktı)",
        "langs": ["Fransızca", "Almanca", "İtalyanca", "İngilizce"]
    },
    "Almanca": {
        "title": "Schweizer Mietbewerbungs-Assistent",
        "name": "Vor- und Nachname", "partner": "Partner-Info", "job": "Beruf", 
        "income": "Haushaltseinkommen", "location": "Ort", "rooms": "Zimmer",
        "lifestyle": ["Nichtraucher", "Keine Haustiere", "Ruhiger Lebensstil"], "note": "Persönliche Notiz", "btn": "Brief mit CV optimieren 🚀",
        "out_lang_label": "🎯 Sprache des Briefes (Output)",
        "langs": ["Französisch", "Deutsch", "Italienisch", "Englisch"]
    }
}

# --- SİSTEM PROMPTLARI (ADAY PERSPEKTİFİ) ---
SYSTEM_PROMPTS = {
    "Fransızca": "Tu es l'aspirant locataire. RÉDIGE LA LETTRE À LA PREMIÈRE PERSONNE (JE). Utilise les informations pertinentes du CV (expérience, stabilité) pour renforcer la candidature. À la fin, ajoute une liste de 'Pièces jointes'.",
    "Almanca": "Du bist der Mietinteressent. SCHREIBE AUS DER ICH-PERSPEKTIVE (ICH/WIR). Nutze Schweizer Hochdeutsch (ss statt ß). Nutze Details aus dem Lebenslauf. Füge am Ende eine Liste der 'Beilagen' hinzu.",
    "İtalyanca": "Tu sei il potenziale inquilino. SCRIVI IN PRIMA PERSONA (IO). Usa dettagli dal CV per mostrare professionalità. Aggiungi alla fine l'elenco degli 'Allegati'.",
    "İngilizce": "You are the potential tenant. WRITE IN THE FIRST PERSON (I). Use CV highlights to prove you are a responsible professional. Add an 'Enclosures' list at the end."
}

LANG_MAP = {
    "Fransızca": "Fransızca", "Französisch": "Fransızca",
    "Almanca": "Almanca", "Deutsch": "Almanca",
    "İtalyanca": "İtalyanca", "Italienisch": "İtalyanca",
    "İngilizce": "İngilizce", "Englisch": "İngilizce"
}

# --- SIDEBAR: CV YÜKLEME ---
if 'cv_content' not in st.session_state: 
    st.session_state['cv_content'] = "No CV uploaded yet."

st.sidebar.header("📄 Belge Merkezi")
uploaded_file = st.sidebar.file_uploader("Özgeçmişinizi (PDF) yükleyin", type="pdf")

if uploaded_file:
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        st.session_state['cv_content'] = text
        st.sidebar.success("✅ CV Analiz Edildi!")
    except Exception as e:
        st.sidebar.error(f"PDF okuma hatası: {e}")

# --- ARAYÜZ DİL SEÇİMİ ---
ui_lang_choice = st.sidebar.selectbox("Arayüz Dili / UI Language", ["Türkçe", "Almanca"])
u = UI_LANGS[ui_lang_choice]

st.title(f"🇨🇭 {u['title']}")

# --- FORM ---
with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        full_name = st.text_input(u['name'], value="Emre Fikirlier")
        partner_info = st.text_input(u['partner'], value="Schweizer Staatsbürgerin, Angestellte")
        job_title = st.text_input(u['job'], value="Mitarbeiter im Einzelhandel")
        
        selected_out_lang = st.selectbox(u['out_lang_label'], u['langs'])
        output_lang_key = LANG_MAP[selected_out_lang]

    with c2:
        total_income = st.text_input(u['income'], value="7700")
        location = st.text_input(u['location'], value="Zürich")
        rooms = st.slider(u['rooms'], 1.0, 5.5, 2.5, 0.5)
        lifestyle = st.multiselect("Lifestyle", u['lifestyle'], default=u['lifestyle'])

    motivation = st.text_area(u['note'], placeholder="Neden bu daire? (Örn: İşime 5 dakika mesafede)")
    submit = st.form_submit_button(u['btn'])

# --- AI İŞLEME VE ÇIKTI ---
if submit:
    with st.status("🛠️ AI Mektubu Hazırlıyor (CV Analiz Ediliyor)...") as status:
        prompt = f"""
        {SYSTEM_PROMPTS[output_lang_key]}
        
        MY DATA:
        - Name: {full_name}
        - Total Household Income: {total_income} CHF
        - My Partner: {partner_info}
        - My Job: {job_title}
        - Target Location: {location}
        - Lifestyle: {', '.join(lifestyle)}
        - Personal Motivation: {motivation}
        
        RAW CV CONTENT FOR ANALYSIS:
        {st.session_state['cv_content']}
        
        INSTRUCTIONS:
        1. Write a formal Swiss rental motivation letter in {output_lang_key}.
        2. Use the first person (I/We).
        3. Mention specific professional stability or skills from the CV.
        4. Be respectful, stable, and polite.
        5. Add 'Enclosures' section at the end:
           - Extrait du Registre des Poursuites
           - Attestation de l'employeur
           - Copie des pièces d'identité
           - Curriculum Vitae
        """
        
        try:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=25)
            res_data = res.json()
            
            if 'choices' in res_data:
                final_text = res_data['choices'][0]['message']['content']
                status.update(label="✅ Başarıyla Hazırlandı!", state="complete")
                
                st.divider()
                st.subheader(f"📄 Nihai Mektup ({output_lang_key})")
                st.markdown(final_text)
                
                st.download_button(
                    label="📥 Mektubu İndir (.txt)",
                    data=final_text,
                    file_name=f"basvuru_mektubu_{output_lang_key}.txt",
                    mime="text/plain"
                )
            else:
                st.error(f"API Hatası: {res_data.get('error', {}).get('message', 'Bilinmeyen hata')}")
        
        except Exception as e:
            st.error(f"Bağlantı Hatası: {str(e)}")
