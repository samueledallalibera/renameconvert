import streamlit as st
import os
import xml.etree.ElementTree as ET
import pandas as pd
import zipfile
from io import BytesIO

# Funzione di esplorazione ricorsiva per il parsing dei dati
def parse_element(element, parsed_data, parent_tag=""):
    for child in element:
        tag_name = f"{parent_tag}/{child.tag.split('}')[-1]}" if parent_tag else child.tag.split('}')[-1]
        if list(child):  # Se ha figli, chiamata ricorsiva
            parse_element(child, parsed_data, tag_name)
        else:  # Altrimenti, aggiunge il testo alla struttura dei dati
            parsed_data[tag_name] = child.text

# Funzione per estrarre i dati richiesti dal file XML
def extract_required_data_from_xml(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    extracted_data = {}
    header = root.find(".//CedentePrestatore/DatiAnagrafici/Anagrafica")
    if header is not None:
        extracted_data["Denominazione"] = header.find(".//Denominazione").text if header.find(".//Denominazione") is not None else None
    general_data = root.find(".//FatturaElettronicaBody//DatiGenerali//DatiGeneraliDocumento")
    if general_data is not None:
        extracted_data["Data"] = general_data.find(".//Data").text if general_data.find(".//Data") is not None else None
        extracted_data["Numero"] = general_data.find(".//Numero").text if general_data.find(".//Numero") is not None else None
    return extracted_data

# Funzione per processare tutti i file XML in una cartella
def process_all_xml_files(xml_folder_path):
    all_extracted_data = []
    for filename in os.listdir(xml_folder_path):
        if filename.endswith('.xml'):
            xml_file_path = os.path.join(xml_folder_path, filename)
            try:
                file_data = extract_required_data_from_xml(xml_file_path)
                file_data["FileName"] = filename
                all_extracted_data.append(file_data)
            except ET.ParseError as e:
                st.warning(f"Errore nel parsing del file {filename}: {e}.")
    return pd.DataFrame(all_extracted_data)

# Funzione per unire i dati nella forma "Denominazione FT Numero del Data"
def unisci_dati(df):
    df['Dati_Uniti'] = df.apply(
        lambda row: f"{(row['Denominazione'][:20] if row['Denominazione'] and len(row['Denominazione']) > 20 else row['Denominazione'])} FT {row['Numero']} del {row['Data']}",
        axis=1
    )
    return df[['Dati_Uniti', 'FileName']]

# Funzione per rinominare i file con i dati uniti
def rinomina_file(temp_folder_path, df):
    for _, row in df.iterrows():
        old_file_path = os.path.join(temp_folder_path, row['FileName'])
        if row['Dati_Uniti']:
            new_file_name = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in row['Dati_Uniti']) + ".xml"
            new_file_path = os.path.join(temp_folder_path, new_file_name)
            os.rename(old_file_path, new_file_path)

# Streamlit app
st.title("Gestione XML Fatture Elettroniche")

uploaded_zip = st.file_uploader("Carica un file .zip contenente i file XML", type=["zip"])

if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip) as z:
        temp_folder_path = "temp_xml_files"
        os.makedirs(temp_folder_path, exist_ok=True)
        z.extractall(temp_folder_path)

        st.success(f"{len(z.namelist())} file estratti nella cartella temporanea.")

        # Estrazione dati e creazione DataFrame
        extracted_data_df = process_all_xml_files(temp_folder_path)
        if not extracted_data_df.empty:
            st.write("Anteprima dei dati estratti:")
            st.dataframe(extracted_data_df)

            # Unione dei dati
            unified_data_df = unisci_dati(extracted_data_df)
            st.write("Anteprima dei dati uniti per la rinomina:")
            st.dataframe(unified_data_df)

            # Rinominare i file
            rinomina_file(temp_folder_path, unified_data_df)
            st.success("I file sono stati rinominati con successo.")

            # Compressione dei file rinominati in un nuovo zip
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as z:
                for filename in os.listdir(temp_folder_path):
                    file_path = os.path.join(temp_folder_path, filename)
                    z.write(file_path, arcname=filename)

            # Rimozione della cartella temporanea
            for file in os.listdir(temp_folder_path):
                os.remove(os.path.join(temp_folder_path, file))
            os.rmdir(temp_folder_path)

            # Download del nuovo zip
            st.download_button(
                label="Scarica i file XML rinominati",
                data=zip_buffer.getvalue(),
                file_name="file_rinominati.zip",
                mime="application/zip"
            )
        else:
            st.error("Nessun dato valido estratto dai file XML.")
