import streamlit as st
import pandas as pd
from nettoyage_voo import traiter_fichiers_utilisateur

st.set_page_config(page_title="Nettoyage VOO", layout="wide")

st.title("Analyse et nettoyage de données VOO")

st.markdown("""
Cette application permet d'analyser et de nettoyer automatiquement des fichiers de données VOO (au format CSV).  
Elle détecte les incohérences, signale les erreurs (valeurs hors seuils, formats invalides, etc.) et génère un fichier propre, prêt à être exploité.  
Un rapport détaillé est également fourni pour faciliter les corrections ou validations manuelles.

📄 [Consulter le document des tests effectués](https://docs.google.com/document/d/TON_ID_DE_DOCUMENT)
""")

fichiers = st.file_uploader("Téléversez vos fichiers CSV (1 à 4)", type=["csv"], accept_multiple_files=True)

if fichiers:
    st.success(f"{len(fichiers)} fichier(s) chargé(s).")

    if st.button("Lancer l'analyse"):
        with st.spinner("Traitement en cours..."):
            base_nettoyee, erreurs, rapport_excel = traiter_fichiers_utilisateur(fichiers)

        st.subheader("✅ Fichier nettoyé : aperçu")
        st.dataframe(base_nettoyee.head())

        st.download_button("Télécharger les données nettoyées", base_nettoyee.to_csv(index=False).encode('utf-8'),
                           file_name="donnees_nettoyees.csv", mime="text/csv")

        with open(rapport_excel, "rb") as f:
            st.download_button("📑 Télécharger le rapport d’erreurs Excel", f, file_name=rapport_excel, mime="application/vnd.ms-excel")
