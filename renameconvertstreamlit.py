import os
import zipfile
import streamlit as st

# Funzione per convertire file .p7m in .xml
def converti_p7m_in_xml(cartella_output, file_zip):
    # Estrai file ZIP
    try:
        with zipfile.ZipFile(file_zip, 'r') as zip_ref:
            zip_ref.extractall(cartella_output)
    except Exception as e:
        st.error(f"Errore durante l'estrazione del file ZIP: {e}")
        return []

    converted_files = []
    # Itera sui file estratti
    for file_name in os.listdir(cartella_output):
        if file_name.endswith(".p7m"):
            percorso_file = os.path.join(cartella_output, file_name)
            percorso_output = os.path.splitext(percorso_file)[0] + ".xml"

            # Usa il comando OpenSSL per convertire il file
            comando = f'openssl smime -verify -noverify -in "{percorso_file}" -inform DER -out "{percorso_output}"'
            risultato = os.system(comando)

            # Controlla l'esito del comando
            if risultato == 0:  # OpenSSL ha avuto successo
                os.remove(percorso_file)  # Rimuovi il file originale
                converted_files.append(percorso_output)  # Aggiungi il percorso del file convertito
                st.write(f"Convertito con successo: {file_name} in XML.")
            else:  # OpenSSL ha fallito
                st.error(f"Errore nella conversione del file {file_name}. Comando eseguito: {comando}")

    return converted_files

# Funzione per creare un file ZIP contenente i file XML convertiti
def crea_zip_con_file(xml_files, nome_zip):
    zip_path = os.path.join("output_temp", nome_zip)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in xml_files:
            zipf.write(file, os.path.basename(file))
    return zip_path

# Streamlit App
st.title("Conversione file .p7m in XML")

# Upload del file ZIP
uploaded_file = st.file_uploader("Carica un file ZIP con i file .p7m:", type=["zip"])
output_folder = "output_temp"

if uploaded_file and st.button("Avvia Conversione"):
    os.makedirs(output_folder, exist_ok=True)  # Crea una cartella temporanea
    converted_files = converti_p7m_in_xml(output_folder, uploaded_file)

    if converted_files:
        st.success("Conversione completata! Puoi scaricare i file convertiti.")

        # Crea un file ZIP contenente tutti i file XML convertiti
        zip_path = crea_zip_con_file(converted_files, "file_convertiti.zip")

        # Aggiungi un pulsante di download per il file ZIP
        with open(zip_path, "rb") as f:
            file_data = f.read()
            st.download_button(
                label="Scarica il file ZIP con i file XML",
                data=file_data,
                file_name="file_convertiti.zip",
                mime="application/zip"
            )

    else:
        st.write("Nessun file convertito.")


