import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAZIONE DATABASE ---
DB_NAME = "laghetti_pesca.db"

def init_db():
    """Crea il database e la tabella se non esistono"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS laghetti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            citta TEXT,
            tipo_pesca TEXT,
            regolamento TEXT,
            note_esche TEXT,
            data_inserimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def aggiungi_laghetto(nome, citta, tipo, regole, note):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO laghetti (nome, citta, tipo_pesca, regolamento, note_esche)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, citta, tipo, regole, note))
    conn.commit()
    conn.close()

def ottieni_laghetti():
    conn = sqlite3.connect(DB_NAME)
    # Legge i dati in un DataFrame Pandas per visualizzarli bene
    df = pd.read_sql_query("SELECT * FROM laghetti ORDER BY data_inserimento DESC", conn)
    conn.close()
    return df

def elimina_laghetto(laghetto_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM laghetti WHERE id = ?", (laghetto_id,))
    conn.commit()
    conn.close()

# --- INTERFACCIA UTENTE (STREAMLIT) ---
st.set_page_config(page_title="🎣 Diario Laghetti Sportivi", page_icon="🐟", layout="wide")
st.title("🎣 Diario dei Laghetti Sportivi")
st.markdown("La tua agenda personale per non dimenticare mai più regole, costi ed esche vincenti!")

init_db()

# Menu a tendina per scegliere l'azione
azione = st.sidebar.radio("Cosa vuoi fare?", ["📋 Consulta Laghetti", "➕ Aggiungi Nuovo", "🗑️ Elimina"])

if azione == "➕ Aggiungi Nuovo":
    st.header("Inserisci un nuovo laghetto")
    with st.form("nuovo_laghetto_form"):
        nome = st.text_input("Nome del laghetto (es. La Fossa, Paradise...)")
        citta = st.text_input("Città / Provincia")
        tipo_pesca = st.multiselect("Tipo di pesca", ["Trota Lago", "Carpfishing", "Cavedano", "Black Bass", "Pesce Gatto", "Storione bianco","Beluga","Pinocchietto","Cobice","Sterlato","Ibrido","betto"])
        regole = st.text_area("Regolamento e Costi (es. 20€ al giorno, max 2 canne, divieto di trattenuta...)")
        note = st.text_area("Note personali ed Esche vincenti (es. Camola del miele a galla, Formaggio...)")
        
        submitted = st.form_submit_button("💾 Salva Laghetto")
        if submitted:
            if nome:
                tipo_str = ", ".join(tipo_pesca)
                aggiungi_laghetto(nome, citta, tipo_str, regole, note)
                st.success(f"✅ {nome} aggiunto con successo!")
            else:
                st.error("⚠️ Inserisci almeno il nome del laghetto!")

elif azione == "📋 Consulta Laghetti":
    st.header("I tuoi Laghetti Salvati")
    df = ottieni_laghetti()
    
    if df.empty:
        st.info("Non hai ancora salvato nessun laghetto. Vai su 'Aggiungi Nuovo' per iniziare!")
    else:
        # Rimuoviamo la colonna id e data per una visione più pulita
        df_vis = df.drop(columns=['id', 'data_inserimento'])
        
        # Mostriamo ogni laghetto come una "card" espandibile
        for index, row in df_vis.iterrows():
            with st.expander(f"📍 {row['nome']} ({row['citta']})"):
                st.markdown(f"**🎣 Tipo di pesca:** {row['tipo_pesca']}")
                st.markdown(f"**📜 Regolamento/Costi:**")
                st.text(row['regolamento'] if row['regolamento'] else "Nessuna nota")
                st.markdown(f"**💡 Note ed Esche:**")
                st.info(row['note_esche'] if row['note_esche'] else "Nessuna nota")

elif azione == "🗑️ Elimina":
    st.header("Elimina un laghetto")
    df = ottieni_laghetti()
    if df.empty:
        st.warning("Il database è vuoto.")
    else:
        # Creiamo una lista per la selectbox
        opzioni = [f"{row['id']}: {row['nome']} ({row['citta']})" for _, row in df.iterrows()]
        scelta = st.selectbox("Selezionere il laghetto da eliminare",opzioni)

        if st.button("🗑️ Conferma Eliminazione"):
            id_da_eliminare = int(scelta.split(":")[0])
            elimina_laghetto(id_da_eliminare)
            st.success("Laghetto eliminato!")
            st.rerun()
