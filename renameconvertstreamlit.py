import os
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from io import BytesIO
from zipfile import ZipFile

# Funzione di parsing ricorsivo
def parse_element(element, parsed_data, parent_tag=""):
    for child in element:
        tag_name = f"{parent_tag}/{child.tag.split('}')[-1]}" if parent_tag else child.tag.split('}')[-1]
        if list(child):  # Se ha figli
            parse_element(child, parsed_data, tag_name)
        else:
            parsed_data[tag_name] = child.text

# Funzione per estrarre dati da un file XML
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

# Funzione principale per il caricamento e l'elaborazione dei file XML
def process_uploaded_files(uploaded_files, includi_dettaglio_linee):
    all_data_combined = []
    for uploaded_file in uploaded_files:
        try:
            data = parse_xml_file(uploaded_file, includi_dettaglio_linee)
            all_data_combined.extend(data)
        except ET.ParseError as e:
            st.warning(f"Errore nel parsing del file {uploaded_file.name}: {e}")
    return pd.DataFrame(all_data_combined)

# Interfaccia Streamlit
st.title("Estrazione Dati da Fatture Elettroniche XML")

# Caricamento file
uploaded_file = st.file_uploader("Carica file XML o un archivio .zip", type=["xml", "zip"], accept_multiple_files=True)

# Opzione per includere il dettaglio delle linee
includi_dettaglio_linee = st.checkbox("Includi dettaglio linee", value=True)

if uploaded_file:
    all_files = []

    # Gestione file ZIP
    for file in uploaded_file:
        if file.name.endswith(".zip"):
            with ZipFile(file) as z:
                for name in z.namelist():
                    if name.endswith(".xml"):
                        all_files.append(BytesIO(z.read(name)))
        else:
            all_files.append(file)

    # Elaborazione dei file
    with st.spinner("Elaborazione in corso..."):
        extracted_data_df = process_uploaded_files(all_files, includi_dettaglio_linee)

    if not extracted_data_df.empty:
        st.success("Elaborazione completata!")
        st.dataframe(extracted_data_df.head())

        # Esportazione in Excel
        buffer = BytesIO()
        extracted_data_df.to_excel(buffer, index=False)
        st.download_button(
            label="Scarica Dati in Excel",
            data=buffer,
            file_name="fatture_dati_estratti.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Nessun dato valido trovato nei file caricati.")
