import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
from datetime import datetime

st.set_page_config(page_title="Swiss AI Rental Pro", layout="wide", page_icon="🇨🇭")

# API anahtarını güvenli sistemden çekiyoruz
API_KEY = st.secrets["GROQ_API_KEY"] 

# İstek atarken bu değişkeni kullan:
headers = {"Authorization": f"Bearer {API_KEY}"}

# --- UI SÖZLÜĞÜ ---
UI_LANGS = {
    "Türkçe": {
        "title": "İsviçre Emlak Başvuru Sihirbazı",
        "name": "Ad Soyad", "partner": "Eş/Partner Bilgisi", "job": "Mesleğiniz", 
        "income": "Toplam Gelir (CHF)", "location": "Aranan Şehir", "rooms": "Oda Sayısı",
        "lifestyle": ["Sigara Yok", "Hayvan Yok", "Sakin Yaşam"], "note": "Özel Not", "btn": "Mektubu CV ile Zenginleştir 🚀",
        "out_lang_label": "🎯 Mektup Dili (Çıktı)",
        "langs": ["Fransızca", "Almanca", "İtalyanca", "İngilizce"],
        "enclosure_label": "Ekler Listesi: "
    },
    "Almanca": {
        "title": "Schweizer Mietbewerbungs-Assistent",
        "name": "Vor- und Nachname", "partner": "Partner-Info", "job": "Beruf", 
        "income": "Haushaltseinkommen", "location": "Ort", "rooms": "Zimmer",
        "lifestyle": ["Nichtraucher", "Keine Haustiere", "Ruhiger Lebensstil"], "note": "Persönliche Notiz", "btn": "Brief mit CV optimieren 🚀",
        "out_lang_label": "🎯 Sprache des Briefes (Output)",
        "langs": ["Französisch", "Deutsch", "Italienisch", "Englisch"],
        "enclosure_label": "Beilagen: "
    }
}

# --- SİSTEM PROMPTLARI ---
SYSTEM_PROMPTS = {
    "Fransızca": "Tu es l'aspirant locataire. RÉDIGE À LA PREMIÈRE PERSONNE (JE). Utilise les informations pertinentes du CV (expérience, stabilité) pour renforcer la candidature. À la fin, ajoute une liste de 'Pièces jointes'.",
    "Almanca": "Du bist der Mietinteressent. SCHREIBE AUS DER ICH-PERSPEKTIVE. Nutze wichtige Details aus dem Lebenslauf, um Zuverlässigkeit zu zeigen. Füge am Ende eine Liste der 'Beilagen' hinzu.",
    "İtalyanca": "Tu sei il potenziale inquilino. SCRIVI IN PRIMA PERSONA (IO). Usa dettagli dal CV per mostrare professionalità. Aggiungi alla fine l'elenco degli 'Allegati'.",
    "İngilizce": "You are the potential tenant. WRITE IN THE FIRST PERSON (I). Use CV highlights to prove you are a responsible professional. Add an 'Enclosures' list at the end."
}

LANG_MAP = {"Fransızca": "Fransızca", "Französisch": "Fransızca", "Almanca": "Almanca", "Deutsch": "Almanca", "İtalyanca": "İtalyanca", "Italienisch": "İtalyanca", "İngilizce": "İngilizce", "Englisch": "İngilizce"}

# --- SIDEBAR: CV YÜKLEME ---
if 'cv_content' not in st.session_state: st.session_state['cv_content'] = "No CV uploaded yet."

st.sidebar.header("📄 Belge Merkezi")
uploaded_file = st.sidebar.file_uploader("Özgeçmişinizi (PDF) yükleyin", type="pdf")
if uploaded_file:
    reader = PdfReader(uploaded_file)
    st.session_state['cv_content'] = "".join([page.extract_text() for page in reader.pages])
    st.sidebar.success("✅ CV Analiz Edildi!")

# UI Seçimi
ui_lang_choice = st.sidebar.selectbox("Arayüz Dili", ["Türkçe", "Almanca"])
u = UI_LANGS[ui_lang_choice]

st.title(f"🇨🇭 {u['title']}")

# --- FORM ---
with st.form("cv_enhanced_form"):
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

    motivation = st.text_area(u['note'])
    submit = st.form_submit_button(u['btn'])

if submit:
    with st.status("🛠️ CV Analiz Ediliyor ve Mektup Yazılıyor...") as status:
        prompt = f"""
        {SYSTEM_PROMPTS[output_lang_key]}
        
        APPLICANT CONTEXT:
        - Name: {full_name}
        - Income: {total_income} CHF
        - Partner: {partner_info}
        - Job: {job_title}
        - City: {location}
        - Lifestyle: {', '.join(lifestyle)}
        - Personal Note: {motivation}
        
        RAW CV CONTENT FOR ANALYSIS:
        {st.session_state['cv_content']}
        
        INSTRUCTION: 
        1. Identify the applicant's professional background from the CV.
        2. Briefly mention their stability or specific skills (like discipline or reliability) in the letter.
        3. Ensure the tone is 'I' (first person).
        4. AT THE VERY END, add a section called 'Enclosures' (in {output_lang_key}) listing: 
           - Extrait du Registre des Poursuites (Debt collection registry)
           - Attestation de l'employeur (Employer confirmation)
           - Copie des pièces d'identité (ID Copies)
           - Curriculum Vitae
        """
        
        try:
            headers = {"Authorization": f"Bearer {API_KEYS['GROQ']}"}
            # En yeni ve en güçlü modeli kullanıyoruz
            payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
            
            result = res.json()['choices'][0]['message']['content']
            st.subheader(f"📄 CV Destekli Mektubunuz ({output_lang_key})")
            st.markdown(result)
            st.download_button("📥 İndir", result, file_name=f"basvuru_ve_cv_{output_lang_key}.txt")
            status.update(label="✅ Hazır!", state="complete")
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
