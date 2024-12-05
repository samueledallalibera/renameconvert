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
        return

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
                st.write(f"Convertito con successo: {file_name} in XML.")
            else:  # OpenSSL ha fallito
                st.error(f"Errore nella conversione del file {file_name}. Comando eseguito: {comando}")

# Streamlit App
st.title("Conversione file .p7m in XML")

# Upload del file ZIP
uploaded_file = st.file_uploader("Carica un file ZIP con i file .p7m:", type=["zip"])
output_folder = "output_temp"

if uploaded_file and st.button("Avvia Conversione"):
    os.makedirs(output_folder, exist_ok=True)  # Crea una cartella temporanea
    converti_p7m_in_xml(output_folder, uploaded_file)
    st.success("Conversione completata! Controlla i file convertiti nella cartella di output.")

