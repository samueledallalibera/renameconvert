import os
import xml.etree.ElementTree as ET
import pandas as pd

# Funzione per decodificare e convertire i file .p7m in .xml
def converti_p7m_in_xml(cartella):
    file = os.listdir(cartella)
    for idx, nome_file in enumerate(file):
        if nome_file.endswith(".p7m"):
            percorso_file = os.path.join(cartella, nome_file)
            xml_output_path = os.path.join(cartella, f"{idx}.xml")
            os.system(f'openssl smime -verify -noverify -in "{percorso_file}" -inform DER -out "{xml_output_path}"')
            os.remove(percorso_file)  # Rimuove il file .p7m originale
            print(f"File {nome_file} convertito in XML.")

# Funzione per estrarre dati essenziali dal file XML
def estrai_dati_da_xml(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        dati = {
            "Denominazione": None,
            "Data": None,
            "Numero": None,
        }

        # Estrazione Denominazione
        header = root.find(".//CedentePrestatore/DatiAnagrafici/Anagrafica/Denominazione")
        if header is not None:
            dati["Denominazione"] = header.text

        # Estrazione Data e Numero
        dati_generali = root.find(".//FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento")
        if dati_generali is not None:
            dati["Data"] = dati_generali.findtext("Data")
            dati["Numero"] = dati_generali.findtext("Numero")

        return dati
    except ET.ParseError as e:
        print(f"Errore nel parsing di {xml_file_path}: {e}")
        return None

# Funzione per rinominare i file XML
def rinomina_file(cartella, dati):
    for _, riga in dati.iterrows():
        vecchio_nome = os.path.join(cartella, riga["FileName"])
        if riga["Dati_Uniti"]:  # Controlla che i dati uniti non siano vuoti
            nuovo_nome = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in riga["Dati_Uniti"]) + ".xml"
            nuovo_percorso = os.path.join(cartella, nuovo_nome)
            try:
                os.rename(vecchio_nome, nuovo_percorso)
                print(f"Rinominato: {riga['FileName']} -> {nuovo_nome}")
            except OSError as e:
                print(f"Errore nella rinomina di {riga['FileName']}: {e}")

# Funzione principale per elaborare i file XML
def processa_file_xml(cartella):
    dati_estratti = []
    for nome_file in os.listdir(cartella):
        if nome_file.endswith(".xml"):
            percorso_file = os.path.join(cartella, nome_file)
            dati = estrai_dati_da_xml(percorso_file)
            if dati:
                dati["FileName"] = nome_file
                dati_estratti.append(dati)

    # Creazione del DataFrame
    df = pd.DataFrame(dati_estratti)

    # Aggiunta colonna per i dati uniti
    if not df.empty:
        df["Dati_Uniti"] = df.apply(
            lambda riga: f"{(riga['Denominazione'][:20] if riga['Denominazione'] and len(riga['Denominazione']) > 20 else riga['Denominazione'])} FT {riga['Numero']} del {riga['Data']}",
            axis=1
        )
    return df

# Implementazione Streamlit
import streamlit as st

st.title("Gestione Fatture XML e P7M")

# Caricamento della cartella
cartella = st.text_input("Inserisci il percorso della cartella con i file:", "")

if cartella and st.button("Avvia elaborazione"):
    if os.path.exists(cartella):
        # Conversione dei file .p7m in .xml
        st.write("Conversione dei file .p7m in XML...")
        converti_p7m_in_xml(cartella)

        # Elaborazione dei file XML
        st.write("Elaborazione dei file XML...")
        dati_df = processa_file_xml(cartella)

        if not dati_df.empty:
            # Rinominare i file
            st.write("Rinominando i file...")
            rinomina_file(cartella, dati_df)

            # Mostrare l'anteprima dei dati
            st.write("Anteprima dei dati estratti:")
            st.dataframe(dati_df)
        else:
            st.write("Nessun dato trovato nei file XML.")
    else:
        st.write("Percorso della cartella non valido.")
