import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAZIONE DATABASE ---
DB_NAME = "laghetti_pesca.db"

def init_db():
    """Crea il database e la tabella se non esistono, e aggiorna lo schema se necessario"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Crea la tabella con la colonna zone_migliori
    c.execute('''
        CREATE TABLE IF NOT EXISTS laghetti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            citta TEXT,
            tipo_pesca TEXT,
            regolamento TEXT,
            note_esche TEXT,
            zone_migliori TEXT,
            data_inserimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Aggiungi la colonna zone_migliori se il database è stato creato prima di questo aggiornamento
    try:
        c.execute("ALTER TABLE laghetti ADD COLUMN zone_migliori TEXT")
    except sqlite3.OperationalError:
        pass  # La colonna esiste già, ignoriamo l'errore
        
    conn.commit()
    conn.close()

def aggiungi_laghetto(nome, citta, tipo, regole, note, zone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO laghetti (nome, citta, tipo_pesca, regolamento, note_esche, zone_migliori)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, citta, tipo, regole, note, zone))
    conn.commit()
    conn.close()

def modifica_laghetto(laghetto_id, nome, citta, tipo, regole, note, zone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE laghetti 
        SET nome = ?, citta = ?, tipo_pesca = ?, regolamento = ?, note_esche = ?, zone_migliori = ?
        WHERE id = ?
    ''', (nome, citta, tipo, regole, note, zone, laghetto_id))
    conn.commit()
    conn.close()

def ottieni_laghetti():
    conn = sqlite3.connect(DB_NAME)
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
st.markdown("La tua agenda personale per non dimenticare mai più regole, costi, esche e zone vincenti!")

init_db()

# Menu a tendina per scegliere l'azione
azione = st.sidebar.radio("Cosa vuoi fare?", ["📋 Consulta Laghetti", "➕ Aggiungi Nuovo", "✏️ Modifica", "🗑️ Elimina"])

if azione == "➕ Aggiungi Nuovo":
    st.header("Inserisci un nuovo laghetto")
    with st.form("nuovo_laghetto_form"):
        nome = st.text_input("Nome del laghetto (es. La Fossa, Paradise...)", max_chars=100)
        citta = st.text_input("Città / Provincia", max_chars=100)
        tipo_pesca = st.multiselect(
            "Tipo di pesca", 
            ["Trota Lago", "Carpfishing", "Cavedano", "Black Bass", "Pesce Gatto", "Storione bianco", "Beluga", "Pinocchietto", "Cobice", "Sterlato", "Ibrido"]
        )
        regole = st.text_area("Regolamento e Costi (es. 20€ al giorno, max 2 canne, divieto di trattenuta...)")
        
        # 1. Note personali ed esche
        note = st.text_area("Note personali ed Esche vincenti (es. Camola del miele a galla, Formaggio...)")
        # 2. Zone migliori (SUBITO SOTTO)
        zone = st.text_area("Zone migliori di pesca (es. lato nord, vicino ai canneti, getto 15-20 metri...)")
        
        submitted = st.form_submit_button("💾 Salva Laghetto")
        if submitted:
            if nome:
                tipo_str = ", ".join(tipo_pesca) if tipo_pesca else "Non specificato"
                aggiungi_laghetto(nome, citta, tipo_str, regole, note, zone)
                st.success(f"✅ **{nome}** aggiunto con successo!")
            else:
                st.error("⚠️ Inserisci almeno il nome del laghetto!")

elif azione == "✏️ Modifica":
    st.header("Modifica un laghetto esistente")
    df = ottieni_laghetti()
    if df.empty:
        st.warning("Il database è vuoto. Aggiungi prima un laghetto!")
    else:
        opzioni = {f"{row['id']}: {row['nome']} ({row['citta'] or 'Sede sconosciuta'})": row['id'] for _, row in df.iterrows()}
        scelta_label = st.selectbox("Seleziona il laghetto da modificare", list(opzioni.keys()))
        
        if scelta_label:
            id_da_modificare = opzioni[scelta_label]
            row = df[df['id'] == id_da_modificare].iloc[0]
            
            with st.form("modifica_laghetto_form"):
                nome = st.text_input("Nome del laghetto", value=row['nome'])
                citta = st.text_input("Città / Provincia", value=row['citta'] or "")
                
                tipi_salvati = [t.strip() for t in str(row['tipo_pesca']).split(",")] if row['tipo_pesca'] and str(row['tipo_pesca']) != "Non specificato" else []
                tipo_pesca = st.multiselect(
                    "Tipo di pesca", 
                    ["Trota Lago", "Carpfishing", "Cavedano", "Black Bass", "Pesce Gatto", "Storione bianco", "Beluga", "Pinocchietto", "Cobice", "Sterlato", "Ibrido"],
                    default=tipi_salvati
                )
                
                regole = st.text_area("Regolamento e Costi", value=row['regolamento'] or "")
                
                # 1. Note personali ed esche
                note = st.text_area("Note personali ed Esche vincenti", value=row['note_esche'] or "")
                # 2. Zone migliori (SUBITO SOTTO)
                zone = st.text_area("Zone migliori di pesca", value=row.get('zone_migliori', '') or "")
                
                submitted = st.form_submit_button("💾 Aggiorna Laghetto")
                if submitted:
                    if nome:
                        tipo_str = ", ".join(tipo_pesca) if tipo_pesca else "Non specificato"
                        modifica_laghetto(id_da_modificare, nome, citta, tipo_str, regole, note, zone)
                        st.success(f"✅ **{nome}** aggiornato con successo!")
                        st.rerun()
                    else:
                        st.error("⚠️ Il nome del laghetto è obbligatorio!")

elif azione == "📋 Consulta Laghetti":
    st.header("I tuoi Laghetti Salvati")
    df = ottieni_laghetti()
    
    if df.empty:
        st.info("Non hai ancora salvato nessun laghetto. Vai su '➕ Aggiungi Nuovo' per iniziare!")
    else:
        df_vis = df.drop(columns=['id', 'data_inserimento'], errors='ignore')
        
        for _, row in df_vis.iterrows():
            with st.expander(f"📍 **{row['nome']}** ({row['citta'] or 'Città non specificata'})"):
                st.markdown(f"**🎣 Tipo di pesca:** {row['tipo_pesca']}")
                
                st.markdown("**📜 Regolamento/Costi:**")
                st.text(row['regolamento'] if row['regolamento'] else "Nessuna nota inserita")
                
                st.markdown("**💡 Note ed Esche:**")
                st.info(row['note_esche'] if row['note_esche'] else "Nessuna nota inserita")
                
                # Zone migliori SUBITO SOTTO alle note
                st.markdown("**🎯 Zone migliori:**")
                if row.get('zone_migliori'):
                    st.markdown(f"> *{row['zone_migliori']}*")
                else:
                    st.text("Nessuna zona specifica indicata")

elif azione == "🗑️ Elimina":
    st.header("Elimina un laghetto")
    df = ottieni_laghetti()
    if df.empty:
        st.warning("Il database è vuoto. Non c'è nulla da eliminare.")
    else:
        opzioni = {f"{row['id']}: {row['nome']} ({row['citta'] or 'Sede sconosciuta'})": row['id'] for _, row in df.iterrows()}
        scelta_label = st.selectbox("Seleziona il laghetto da eliminare", list(opzioni.keys()))
        
        if st.button("🗑️ Conferma Eliminazione", type="primary"):
            id_da_eliminare = opzioni[scelta_label]
            elimina_laghetto(id_da_eliminare)
            st.success("Laghetto eliminato con successo!")
            st.rerun()
