import os
import xml.etree.ElementTree as ET
import pandas as pd
import zipfile
from io import BytesIO
import streamlit as st

# Funzione per decodificare e convertire i file .p7m in .xml
def converti_p7m_in_xml(cartella):
    file = os.listdir(cartella)
    for idx, nome_file in enumerate(file):
        if nome_file.endswith(".p7m"):
            percorso_file = os.path.join(cartella, nome_file)
            xml_output_path = os.path.join(cartella, f"{idx}.xml")
            os.system(f'openssl smime -verify -noverify -in "{percorso_file}" -inform DER -out "{xml_output_path}"')
            os.remove(percorso_file)  # Rimuove il file .p7m originale
            st.write(f"File {nome_file} convertito in XML.")

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
        st.warning(f"Errore nel parsing di {xml_file_path}: {e}")
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
                st.write(f"Rinominato: {riga['FileName']} -> {nuovo_nome}")
            except OSError as e:
                st.error(f"Errore nella rinomina di {riga['FileName']}: {e}")

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

# Streamlit app
st.title("Gestione Fatture XML e P7M")

# Caricamento del file ZIP
uploaded_zip = st.file_uploader("Carica un file .zip contenente i file P7M/XML", type=["zip"])

if uploaded_zip:
    # Creazione di una cartella temporanea per gestire i file
    temp_folder = "temp_files"
    os.makedirs(temp_folder, exist_ok=True)

    # Estrazione dei file dal .zip
    with zipfile.ZipFile(uploaded_zip) as z:
        z.extractall(temp_folder)
        st.write(f"{len(z.namelist())} file estratti nella cartella temporanea.")

        # Conversione dei file .p7m in .xml
        st.write("Conversione dei file .p7m in XML...")
        converti_p7m_in_xml(temp_folder)

        # Elaborazione dei file XML
        st.write("Elaborazione dei file XML...")
        dati_df = processa_file_xml(temp_folder)

        if not dati_df.empty:
            # Rinominare i file
            st.write("Rinominando i file...")
            rinomina_file(temp_folder, dati_df)

            # Mostrare l'anteprima dei dati
            st.write("Anteprima dei dati estratti:")
            st.dataframe(dati_df)

            # Creare un nuovo file .zip con i file rinominati
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as z:
                for nome_file in os.listdir(temp_folder):
                    percorso_file = os.path.join(temp_folder, nome_file)
                    z.write(percorso_file, arcname=nome_file)

            # Rimozione della cartella temporanea
            for file in os.listdir(temp_folder):
                os.remove(os.path.join(temp_folder, file))
            os.rmdir(temp_folder)

            # Offrire il download del nuovo file .zip
            st.download_button(
                label="Scarica i file rinominati",
                data=zip_buffer.getvalue(),
                file_name="file_rinominati.zip",
                mime="application/zip"
            )
        else:
            st.error("Nessun dato valido trovato nei file XML.")
