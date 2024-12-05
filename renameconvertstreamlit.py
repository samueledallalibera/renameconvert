import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import os
import zipfile
from io import BytesIO

# Funzione di parsing degli elementi XML
def parse_element(element, parsed_data, parent_tag=""):
    for child in element:
        tag_name = f"{parent_tag}/{child.tag.split('}')[-1]}" if parent_tag else child.tag.split('}')[-1]
        if list(child):  # Ricorsione sui figli
            parse_element(child, parsed_data, tag_name)
        else:
            parsed_data[tag_name] = child.text

# Funzione per parsare il file XML
def parse_xml_file(xml_file, includi_dettaglio_linee=True):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    header_data = {}
    header = root.find(".//FatturaElettronicaHeader")
    if header is not None:
        parse_element(header, header_data)

    general_data = {}
    dati_generali = root.find(".//FatturaElettronicaBody//DatiGenerali//DatiGeneraliDocumento")
    if dati_generali is not None:
        parse_element(dati_generali, general_data)

    riepilogo_dati = {}
    riepiloghi = root.findall(".//FatturaElettronicaBody//DatiBeniServizi//DatiRiepilogo")
    for riepilogo in riepiloghi:
        parse_element(riepilogo, riepilogo_dati)

    line_items = []
    descrizioni = []
    lines = root.findall(".//FatturaElettronicaBody//DettaglioLinee")
    for line in lines:
        line_data = {}
        parse_element(line, line_data)
        if "Descrizione" in line_data:
            descrizioni.append(line_data["Descrizione"])
        if includi_dettaglio_linee:
            line_items.append(line_data)

    all_data = []
    combined_data = {**header_data, **general_data, **riepilogo_dati}

    if not includi_dettaglio_linee and descrizioni:
        combined_data["Descrizione"] = " | ".join(descrizioni)
        all_data.append(combined_data)
    elif line_items:
        first_line_data = line_items[0]
        combined_data = {**combined_data, **first_line_data}
        all_data.append(combined_data)
        for line_data in line_items[1:]:
            line_row = {**{key: None for key in combined_data.keys()}, **line_data}
            all_data.append(line_row)
    else:
        all_data.append(combined_data)

    return all_data

# Funzione per processare tutti i file XML
def process_all_files(uploaded_files, includi_dettaglio_linee=True):
    all_data_combined = []

    for uploaded_file in uploaded_files:
        try:
            file_data = parse_xml_file(uploaded_file, includi_dettaglio_linee)
            all_data_combined.extend(file_data)
        except ET.ParseError as e:
            st.error(f"Errore nel parsing del file {uploaded_file.name}: {e}")

    return pd.DataFrame(all_data_combined)

# Interfaccia Streamlit
st.title("Gestione Fatture Elettroniche XML")

uploaded_zip = st.file_uploader("Carica un file .zip contenente XML o singoli file XML", type=["zip", "xml"])
includi_dettaglio_linee = st.checkbox("Includi dettaglio delle linee", value=True)

if uploaded_zip:
    with st.spinner("Elaborazione file..."):
        # Estrazione dei file XML
        extracted_files = []
        if uploaded_zip.name.endswith(".zip"):
            with zipfile.ZipFile(uploaded_zip) as z:
                for file_name in z.namelist():
                    if file_name.endswith(".xml"):
                        extracted_files.append(BytesIO(z.read(file_name)))
        else:
            extracted_files.append(uploaded_zip)

        # Parsing e creazione del DataFrame
        df = process_all_files(extracted_files, includi_dettaglio_linee)

        if not df.empty:
            # Esportazione Excel
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.success("Elaborazione completata!")
            st.download_button(
                label="Scarica il file Excel",
                data=output,
                file_name="fatture_elaborate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nessun dato valido trovato nei file caricati.")
