import os
import tempfile
import zipfile
import streamlit as st

# Funzione per convertire i file .p7m in .xml
def converti_p7m_in_xml(cartella):
    file = os.listdir(cartella)
    for idx, nome_file in enumerate(file):
        if nome_file.endswith(".p7m"):
            percorso_file = os.path.join(cartella, nome_file)
            xml_output_path = os.path.join(cartella, f"{idx}.xml")
            os.system(f'openssl smime -verify -noverify -in "{percorso_file}" -inform DER -out "{xml_output_path}"')
            os.remove(percorso_file)  # Rimuove il file .p7m originale
            st.write(f"File {nome_file} convertito in XML.")

# Interfaccia Streamlit
st.title("Conversione File P7M in XML")

# Caricamento file ZIP
uploaded_file = st.file_uploader("Carica un file ZIP contenente i file .p7m", type="zip")

if uploaded_file:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Estrai il contenuto dello ZIP
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.read())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        st.write("File estratti, avvio della conversione...")
        
        # Conversione dei file .p7m in .xml
        converti_p7m_in_xml(temp_dir)

        # Creazione di un nuovo ZIP con i file XML
        output_zip_path = os.path.join(temp_dir, "converted_files.zip")
        with zipfile.ZipFile(output_zip_path, 'w') as zip_out:
            for file_name in os.listdir(temp_dir):
                if file_name.endswith(".xml"):
                    zip_out.write(os.path.join(temp_dir, file_name), file_name)

        # Download del nuovo ZIP
        with open(output_zip_path, "rb") as f:
            st.download_button("Scarica i file XML convertiti", f, "converted_files.zip")
