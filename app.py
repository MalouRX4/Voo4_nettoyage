# app.py
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from nettoyage_voo import traiter_fichiers_utilisateur

st.set_page_config(page_title="Nettoyage VOO", layout="wide")

st.title("Analyse et nettoyage de données VOO")

st.markdown("""
Cette application permet d'analyser et de nettoyer automatiquement des fichiers de données VOO (au format CSV).  
Elle détecte les incohérences, signale les erreurs (valeurs hors seuils, formats invalides, etc.) et génère un fichier propre, prêt à être exploité.  
Un rapport détaillé est également fourni pour faciliter les corrections ou validations manuelles.

📄 [Consulter le document des tests effectués](https://docs.google.com/document/d/1jp3abQcA0lIA6kP89i_Ds7JQWw7AlJaKjOc9X7CFzFI/edit?usp=sharing)
""")

fichiers = st.file_uploader(
    "Téléversez vos fichiers CSV (1 à 4)",
    type=["csv"],
    accept_multiple_files=True
)

if fichiers:
    st.success(f"{len(fichiers)} fichier(s) chargé(s).")

    if st.button("Lancer l'analyse"):
        with st.spinner("Traitement en cours..."):
            base_nettoyee, erreurs, rapport_excel = traiter_fichiers_utilisateur(fichiers)

        # --- Aperçu des données nettoyées ---
        st.subheader("✅ Fichier nettoyé : aperçu")
        st.dataframe(base_nettoyee.head(), use_container_width=True)

        # --- Téléchargement CSV (UTF-8 avec BOM pour Excel) ---
        st.download_button(
            "Télécharger les données nettoyées",
            base_nettoyee.to_csv(index=False).encode("utf-8-sig"),
            file_name="donnees_nettoyees.csv",
            mime="text/csv"
        )

        # --- Téléchargement du rapport d’erreurs Excel ---
        try:
            with open(rapport_excel, "rb") as f:
                st.download_button(
                    "📑 Télécharger le rapport d’erreurs Excel",
                    f,
                    file_name=rapport_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except FileNotFoundError:
            st.error("Le fichier de rapport n'a pas été trouvé. Vérifie les permissions d'écriture ou le chemin de sortie.")

        # --- Synthèse rapide des erreurs ---
        st.subheader("Synthèse des erreurs")
        nb_lignes = {
            k: (0 if getattr(v, "empty", True) else len(v))
            for k, v in erreurs.items()
        }
        # On n'affiche que les tests avec au moins 1 ligne en erreur
        resume_erreurs = {k: v for k, v in nb_lignes.items() if v > 0}

        if resume_erreurs:
            st.write(resume_erreurs)
        else:
            st.success("Aucune erreur détectée par les tests configurés. 🔍✅")

else:
    st.info("Charge au moins un fichier CSV pour démarrer.")
