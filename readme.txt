# 🧼 VOO - Application de Nettoyage et Contrôle de Qualité des Données

Cette application permet de téléverser jusqu'à 4 fichiers CSV issus de la surveillance VOO, de les fusionner, nettoyer, vérifier l'unicité des identifiants, et de générer un rapport Excel d'erreurs de qualité et de cohérence.

## 🚀 Déploiement rapide via Streamlit Cloud

1. Créer un dépôt GitHub contenant les fichiers :
   - `app.py`
   - `nettoyage_voo.py`
   - `requirements.txt`

2. Aller sur [https://streamlit.io/cloud](https://streamlit.io/cloud)

3. Se connecter avec GitHub, puis :
   - Cliquer sur "New app"
   - Sélectionner votre dépôt
   - Choisir `app.py` comme fichier principal
   - Cliquer sur "Deploy"

## 📂 Structure attendue des données
- Format : CSV, encodage **latin-1**, séparateur `;`
- Contenir la colonne `Identifiant CNR`

## 🧪 Fonctions principales
- Suppression des doublons
- Fusion intelligente par identifiant
- Tests de complétude, cohérence temporelle, logique médicale
- Contrôle des formats et valeurs
- Détection des outliers

## 📑 Rapport d’erreurs
- Un fichier Excel est généré avec un onglet par type d’erreur détectée.

## 🧰 Dépendances (requirements.txt)
```
streamlit
pandas
openpyxl
pycountry
```

## 🙌 Auteur
Application initialement conçue et développée par Maëlle.

---
❤️ Merci d'utiliser cet outil pour garantir la qualité des données VOO !
