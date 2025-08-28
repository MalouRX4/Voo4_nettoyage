# -*- coding: utf-8 -*-
import pandas as pd
import datetime
import re
import pycountry

# --------------- Utilitaires ------------------

ID_COL = 'Identifiant CNR'

# Colonnes sur lesquelles on veut conserver un nom "canonique" pour les tests
COLS_CIBLES_TESTS = [
    "Identifiant", "Date du diagnostic biologique", "Esp P falciparum",
    "Date des symptômes", "Date de retour",
    "Date des premiers symptômes de cet accès",
    "Parasitémie", "Score de galsgow", "Esp P vivax",
    "Esp P ovale", "Esp P malariae", "Esp Plasmodium spp",
    "Esp P knowlesi", "Esp Negative", "Température",
    "Densité (%)", "Hb", "Plaquettes", "Durée du séjour",
    "Troubles de la conscience", "Créatininémie",
    "Créatininémie > 265 µmol/l (OMS)",
    "Test de diagnostic rapide (TDR)", "Ag HRP-2", "Ag com pLDH",
    "Ag Pf pLDH", "Ag Pv pLDH", "Coma avéré",
    "Pays de résidence", "Pays visité 1", "Pays visité 2",
    "Parasitémie > 4%"
]

COLS_NUMERIQUES = [
    "Parasitémie", "Créatininémie", "Score de galsgow", "Température",
    "Hb", "Densité (%)", "Plaquettes", "Durée du séjour"
]

def lire_fichiers(fichiers_streamlit):
    # Lis tous les CSV ; pas de normalisation de schéma ici
    return [pd.read_csv(f, encoding="latin-1", sep=";") for f in fichiers_streamlit]

def prefixer_colonnes_par_fichier(dfs, id_col=ID_COL, cols_a_ne_pas_prefixer=None):
    """
    Préfixe TOUTES les colonnes de chaque DataFrame par F{i}__ sauf celles de la liste cols_a_ne_pas_prefixer.
    On conserve donc des versions parallèles (F1__Hb, F2__Hb, …).
    """
    if cols_a_ne_pas_prefixer is None:
        cols_a_ne_pas_prefixer = [id_col]

    dfs_pref = []
    for i, df in enumerate(dfs, start=1):
        df = df.copy()
        prefix = f"F{i}__"
        renames = {}
        for col in df.columns:
            if col not in cols_a_ne_pas_prefixer:
                renames[col] = prefix + str(col)
        df = df.rename(columns=renames)
        dfs_pref.append(df)
    return dfs_pref

def empiler_bases(*dfs):
    # Empilement vertical, union des colonnes. Rien n’est supprimé.
    return pd.concat(dfs, ignore_index=True, sort=False)

def coalesce(df, target_col, candidates):
    """
    Construit/actualise target_col avec la première valeur non nulle trouvée parmi candidates.
    Ne supprime pas les colonnes candidates.
    """
    if target_col not in df.columns:
        df[target_col] = pd.NA
    for c in candidates:
        if c in df.columns:
            df[target_col] = df[target_col].fillna(df[c])
    return df

def normaliser_colonnes(df, cols_cibles=COLS_CIBLES_TESTS):
    """
    Pour chaque colonne cible, crée/rafraîchit la version non préfixée
    en coalesçant les colonnes F1__<col>, F2__<col>, ...
    (on garde aussi les colonnes préfixées intactes).
    """
    all_cols = df.columns.tolist()
    for col in cols_cibles:
        # candidates = toutes les colonnes type F\d+__<col>
        pattern = re.compile(rf"^F\d+__{re.escape(col)}$")
        candidates = [c for c in all_cols if pattern.match(c)]
        if candidates or (col in df.columns):
            # priorité: si une version non préfixée existe déjà, on la garde et on la complète
            base_list = ([] if col not in df.columns else [col])
            df = coalesce(df, col, base_list + candidates)
    return df

def garder_lignes_plus_completes(df, subset_cols):
    df = df.copy()
    df['_nb_non_na'] = df.notna().sum(axis=1)
    df_sorted = df.sort_values(by=subset_cols + ['_nb_non_na'], ascending=[True]*len(subset_cols) + [False])
    df_cleaned = df_sorted.drop_duplicates(subset=subset_cols, keep='first').drop(columns=['_nb_non_na'])
    return df_cleaned

def garder_lignes_les_plus_completes_par_id(df, id_col=ID_COL):
    df = df.copy()
    df['_nb_non_na'] = df.notna().sum(axis=1)
    df_sorted = df.sort_values(by=[id_col, '_nb_non_na'], ascending=[True, False])
    df_cleaned = df_sorted.drop_duplicates(subset=[id_col], keep='first').drop(columns=['_nb_non_na'])
    return df_cleaned

def convertir_colonnes_numeriques(df, colonnes):
    df = df.copy()
    for col in colonnes:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --------------- Tests (inchangés) ------------------

def test_completude(df):
    erreurs = {}
    colonnes_obligatoires = ["Identifiant", "Date du diagnostic biologique", "Esp P falciparum"]
    for col in colonnes_obligatoires:
        if col in df.columns:
            erreurs[f"manquant_{col}"] = df[df[col].isna()]

    dates_critiques = ["Date des symptômes", "Date de retour", "Date du diagnostic biologique"]
    for col in dates_critiques:
        if col in df.columns:
            erreurs[f"date_critique_manquante_{col}"] = df[df[col].isna()]

    champs_essentiels = [
        "Parasitémie", "Score de galsgow", "Esp P falciparum", "Esp P vivax",
        "Esp P ovale", "Esp P malariae", "Esp Plasmodium spp", "Esp P knowlesi", "Esp Negative"
    ]
    found_cols = [col for col in champs_essentiels if col in df.columns]
    if found_cols:
        erreurs["especes_toutes_absentes"] = df[df[found_cols].isna().all(axis=1)]
    return erreurs

def test_dates_coherentes(df):
    erreurs = {}
    now = pd.Timestamp(datetime.date.today())
    def safe_to_datetime(serie): return pd.to_datetime(serie, errors='coerce')

    date_cols = ["Date des symptômes", "Date du diagnostic biologique", "Date des premiers symptômes de cet accès", "Date de retour"]
    df = df.copy()
    for col in date_cols:
        if col in df.columns:
            df[col] = safe_to_datetime(df[col])
    if "Date des symptômes" in df.columns and "Date du diagnostic biologique" in df.columns:
        erreurs["symptomes_diagnostic"] = df[df["Date des symptômes"] > df["Date du diagnostic biologique"]]
    if "Date des premiers symptômes de cet accès" in df.columns and "Date des symptômes" in df.columns:
        erreurs["acces_symptomes"] = df[df["Date des premiers symptômes de cet accès"] > df["Date des symptômes"]]
    for col in date_cols:
        if col in df.columns:
            erreurs[f"{col}_futur"] = df[df[col].notna() & (df[col] > now)]
    return erreurs

def test_coherence_logique(df):
    erreurs = {}
    if "Esp P falciparum" in df.columns and "Esp Negative" in df.columns:
        erreurs["falciparum_et_negative"] = df[(df["Esp P falciparum"] == 1) & (df["Esp Negative"] == 1)]
    if "Parasitémie > 4%" in df.columns and "Parasitémie" in df.columns:
        erreurs["parasitemie_incoherente"] = df[(df["Parasitémie > 4%"] == 1) & (df["Parasitémie"] <= 4)]
    if "Score de galsgow" in df.columns and "Troubles de la conscience" in df.columns:
        erreurs["glasgow_et_conscience"] = df[(df["Score de galsgow"] <= 8) & (df["Troubles de la conscience"] != "Oui")]
    if "Créatininémie > 265 µmol/l (OMS)" in df.columns and "Créatininémie" in df.columns:
        erreurs["creat_incoherente"] = df[(df["Créatininémie > 265 µmol/l (OMS)"] == 1) & (df["Créatininémie"] <= 265)]
    return erreurs

def test_validite_valeurs(df):
    erreurs = {}
    if "Température" in df.columns:
        erreurs["temperature_invalide"] = df[(df["Température"] < 30) | (df["Température"] > 45)]
    if "Score de galsgow" in df.columns:
        erreurs["glasgow_invalide"] = df[(df["Score de galsgow"] < 3) | (df["Score de galsgow"] > 15)]
    if "Densité (%)" in df.columns:
        erreurs["parasitemie_pourcentage"] = df[(df["Densité (%)"] < 0) | (df["Densité (%)"] > 100)]
    if "Hb" in df.columns:
        erreurs["hb_invalide"] = df[(df["Hb"] < 50) | (df["Hb"] > 200)]
    if "Durée du séjour" in df.columns:
        erreurs["duree_negative"] = df[df["Durée du séjour"] < 0]
    return erreurs

def test_format(df):
    erreurs = {}
    pays_valides = [country.name for country in pycountry.countries]
    for col in ["Pays de résidence", "Pays visité 1", "Pays visité 2"]:
        if col in df.columns:
            erreurs[f"{col}_invalide"] = df[~df[col].isin(pays_valides)]
    bool_cols = [col for col in df.columns if df[col].dropna().isin(["Oui", "Non"]).all()]
    for col in bool_cols:
        erreurs[f"{col}_bool_format"] = df[~df[col].isin(["Oui", "Non"])]
    return erreurs

def test_dependances(df):
    erreurs = {}
    if "Esp P vivax" in df.columns and "Ag Pv pLDH" in df.columns:
        erreurs["vivax_sans_antigene"] = df[(df["Esp P vivax"] == 1) & (df["Ag Pv pLDH"] != 1)]
    if "Test de diagnostic rapide (TDR)" in df.columns:
        antigene_cols = [c for c in ["Ag HRP-2", "Ag com pLDH", "Ag Pf pLDH", "Ag Pv pLDH"] if c in df.columns]
        if antigene_cols:
            condition = df["Test de diagnostic rapide (TDR)"] == "Oui"
            has_result = df[antigene_cols].isin([1]).any(axis=1)
            erreurs["tdr_sans_resultat"] = df[condition & ~has_result]
    return erreurs

def test_integrite_medicale(df):
    erreurs = {}
    if "Coma avéré" in df.columns and "Score de galsgow" in df.columns:
        erreurs["coma_score_haut"] = df[(df["Coma avéré"] == "Oui") & (df["Score de galsgow"] > 8)]
    return erreurs

def detecter_outliers(df, colonne, borne_inf, borne_sup):
    erreurs = pd.DataFrame()
    if colonne in df.columns:
        df_clean = df[pd.to_numeric(df[colonne], errors='coerce').notna()].copy()
        df_clean[colonne] = pd.to_numeric(df_clean[colonne], errors='coerce')
        erreurs = df_clean[(df_clean[colonne] < borne_inf) | (df_clean[colonne] > borne_sup)]
    return erreurs

def executer_tous_les_tests(df):
    all_tests = {}
    all_tests.update(test_completude(df))
    all_tests.update(test_dates_coherentes(df))
    all_tests.update(test_coherence_logique(df))
    all_tests.update(test_validite_valeurs(df))
    all_tests.update(test_format(df))
    all_tests.update(test_dependances(df))
    all_tests['outliers_plaquettes'] = detecter_outliers(df, "Plaquettes", 150, 450)
    all_tests['outliers_hemoglobine'] = detecter_outliers(df, "Hb", 50, 200)
    all_tests.update(test_integrite_medicale(df))
    return all_tests

def generer_rapport_erreurs_excel(erreurs_dict, filename="rapport_erreurs_voo.xlsx"):
    with pd.ExcelWriter(filename) as writer:
        for nom_test, df_erreurs in erreurs_dict.items():
            if isinstance(df_erreurs, pd.DataFrame) and not df_erreurs.empty:
                sheet_name = nom_test[:31].replace(' ', '_')
                df_erreurs.to_excel(writer, sheet_name=sheet_name, index=False)
    return filename

# --------------- Pipeline principal ------------------

def traiter_fichiers_utilisateur(fichiers_streamlit):
    # 1) Lecture
    dfs = lire_fichiers(fichiers_streamlit)

    # 2) Nettoyage intra-fichier : garder la ligne la plus complète par Identifiant CNR (dans chaque fichier)
    dfs_cleaned = [garder_lignes_plus_completes(df, [ID_COL]) for df in dfs]

    # 3) Préfixage par fichier (AUCUNE suppression de colonnes)
    dfs_pref = prefixer_colonnes_par_fichier(dfs_cleaned, id_col=ID_COL)

    # 4) Empilement vertical
    base = empiler_bases(*dfs_pref)

    # 5) Colonnes normalisées (non préfixées) par coalescence des Fk__<col>
    base = normaliser_colonnes(base, COLS_CIBLES_TESTS)

    # 6) Dédupliquage des LIGNES par Identifiant CNR (on garde la plus complète)
    base = garder_lignes_les_plus_completes_par_id(base, id_col=ID_COL)

    # 7) Conversions numériques sur les colonnes normalisées
    base = convertir_colonnes_numeriques(base, COLS_NUMERIQUES)

    # 8) Tests + rapport
    erreurs = executer_tous_les_tests(base)
    nom_rapport = generer_rapport_erreurs_excel(erreurs)

    return base, erreurs, nom_rapport
