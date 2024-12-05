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

        # Aggiungi pulsanti di download per ogni file convertito
        for file_path in converted_files:
            with open(file_path, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)
                st.download_button(
                    label=f"Scarica {file_name}",
                    data=file_data,
                    file_name=file_name,
                    mime="application/xml"
                )

    else:
        st.write("Nessun file convertito.")
    converti_p7m_in_xml(output_folder, uploaded_file)
    st.success("Conversione completata! Controlla i file convertiti nella cartella di output.")

