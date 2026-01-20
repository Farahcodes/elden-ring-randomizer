import pandas as pd
import random
import streamlit as st
import os
import sys

# =============================================================================
# 1. LOGIQUE (BACKEND)
# =============================================================================

def charger_donnees(chemin_fichier):
    """
    Charge les données.
    Gestion des chemins pour que ça marche aussi bien en .py qu'en .exe
    """
    # Si on est dans un exe PyInstaller, on cherche le fichier à côté de l'exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    chemin_complet = os.path.join(application_path, chemin_fichier)

    try:
        df = pd.read_csv(chemin_complet, sep=';', header=1, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(chemin_complet, sep=';', header=1, encoding='latin-1')
    except FileNotFoundError:
        return None

    # --- Nettoyage et extraction ---

    # Armes
    df_armes = df.iloc[:, [0, 1, 2, 3]].copy()
    df_armes.columns = ['Class', 'Weapon', 'Dual', '2_Handed']
    df_armes['Class'] = df_armes['Class'].ffill()
    df_armes = df_armes.dropna(subset=['Weapon'])

    # Main Secondaire
    df_main_sec = df.iloc[:, [5, 6, 7]].copy()
    df_main_sec.columns = ['Class', 'Object', 'Catalist_bonus']
    df_main_sec['Class'] = df_main_sec['Class'].ffill()
    df_main_sec = df_main_sec.dropna(subset=['Object'])

    # Magie
    df_magie = df.iloc[:, [9, 10, 11, 12]].copy()
    df_magie.columns = ['Type', 'School', 'Spell', 'Slots']
    df_magie['Type'] = df_magie['Type'].ffill()
    df_magie['School'] = df_magie['School'].ffill()
    df_magie = df_magie.dropna(subset=['Spell'])
    df_magie['Slots'] = pd.to_numeric(df_magie['Slots'], errors='coerce').fillna(1).astype(int)

    # Armures
    df_armure = df.iloc[:, [14, 15]].copy()
    df_armure.columns = ['Set', 'Bonus']
    df_armure = df_armure.dropna(subset=['Set'])

    # Esprits (Colonne 17)
    if len(df.columns) > 17:
        col_spirit = df.columns[17]
        df_esprits = df[[col_spirit]].copy()
        df_esprits.columns = ['Spirit']
        df_esprits = df_esprits.dropna(subset=['Spirit'])
    else:
        df_esprits = pd.DataFrame({'Spirit': []})

    return df_armes, df_main_sec, df_magie, df_armure, df_esprits

def generer_build_logique(data):
    df_armes, df_main_sec, df_magie, df_armure, df_esprits = data

    build = {
        'main_hand': "",
        'grip': "",
        'off_hand': "",
        'armor': "",
        'spells': [],
        'spirit': "Aucun"
    }

    # --- 1. Arme Principale ---
    arme = df_armes.sample(n=1).iloc[0]
    build['main_hand'] = f"{arme['Weapon']}"

    classe_arme = arme['Class']
    nom_arme = arme['Weapon']
    est_double = str(arme['Dual']).strip().lower() == 'yes'
    peut_2_mains = str(arme['2_Handed']).strip().lower() == 'yes'
    est_carian_sword = (nom_arme == "Carian Sorcery Sword")

    # --- 2. Gestion Main / Grip ---
    mode_tenue = '1-Handed'
    objet_sec_row = None
    est_bouclier = False

    if est_double:
        mode_tenue = 'Dual Wield'
        build['off_hand'] = "(Arme Double)"
    elif peut_2_mains:
        if random.random() < (2/3):
            mode_tenue = '2-Handed'
            build['off_hand'] = "Aucune"

    if mode_tenue == '1-Handed':
        # 50% Objet / 50% Arme
        choix_arme = False
        armes_eligibles = df_armes[
            (df_armes['Class'] == classe_arme) &
            (df_armes['Dual'] != 'Yes') &
            (df_armes['Weapon'] != nom_arme)
        ]

        if not armes_eligibles.empty and random.random() < 0.5:
            choix_arme = True

        if choix_arme:
            arme_sec = armes_eligibles.sample(n=1).iloc[0]
            build['off_hand'] = f"{arme_sec['Weapon']}"
        else:
            obj_sec = df_main_sec.sample(n=1).iloc[0]
            objet_sec_row = obj_sec
            build['off_hand'] = f"{obj_sec['Object']}"
            if 'Shield' in str(obj_sec['Class']):
                est_bouclier = True

    build['grip'] = mode_tenue

    # --- 3. Magie ---
    acces_magie = False
    types_auto = []
    sources = []

    # A. Identifier les sources potentielles
    if mode_tenue == '1-Handed' and objet_sec_row is not None:
        c = objet_sec_row['Class']
        if c == 'Glintstone Staves': sources.append('Sorceries')
        elif c == 'Sacred Seals': sources.append('Incantations')
        elif c == 'Universal Catalist': sources.append('All')

    if est_carian_sword:
        sources.append('Sorceries')

    # B. Identifier les blocages
    blocage_magie = False
    if mode_tenue == 'Dual Wield':
        blocage_magie = True
    elif mode_tenue == '2-Handed' and not est_carian_sword:
        blocage_magie = True
    elif est_bouclier and not est_carian_sword:
        blocage_magie = True

    # C. Résultat
    if sources and not blocage_magie:
        acces_magie = True
        if 'All' in sources:
            types_auto = ['Sorceries', 'Incantations']
        else:
            types_auto = list(set(sources))

    # --- 4. Génération Sorts ---
    ecoles_possedees = set()
    if acces_magie:
        pool = df_magie[df_magie['Type'].isin(types_auto)].copy()
        slots = 10
        bonus_ecole = objet_sec_row['Catalist_bonus'] if (objet_sec_row is not None and pd.notna(objet_sec_row['Catalist_bonus'])) else None

        while slots > 0 and not pool.empty:
            candidats = pool[pool['Slots'] <= slots].copy()
            if candidats.empty: break

            candidats['poids'] = 1.0
            if bonus_ecole:
                candidats.loc[candidats['School'] == bonus_ecole, 'poids'] = 3.0

            choix = candidats.sample(n=1, weights='poids').iloc[0]
            build['spells'].append(f"{choix['Spell']} ({choix['Slots']})")
            if pd.notna(choix['School']):
                ecoles_possedees.add(choix['School'])

            slots -= choix['Slots']
            pool = pool.drop(choix.name)

    # --- 5. Armure ---
    df_armure['poids'] = 1.0
    if ecoles_possedees:
        mask = df_armure['Bonus'].isin(ecoles_possedees)
        df_armure.loc[mask, 'poids'] = 5.0

    armure = df_armure.sample(n=1, weights='poids').iloc[0]
    build['armor'] = armure['Set']
    if pd.notna(armure['Bonus']):
        build['armor'] += f" (Bonus: {armure['Bonus']})"

    # --- 6. Esprit ---
    if not df_esprits.empty and random.random() < 0.5:
        build['spirit'] = df_esprits.sample(n=1).iloc[0]['Spirit']

    return build

# =============================================================================

# =============================================================================
# 2. INTERFACE STREAMLIT
# =============================================================================

def main():
    st.set_page_config(page_title="Elden Ring - Build Generator", layout="centered")
    st.markdown("""
        <style>
        .main {
            background-color: #121212;
        }
        .stButton>button {
            background: #d4af37;
            color: #000;
            font-weight: bold;
            font-size: 18px;
            border-radius: 8px;
            padding: 0.5em 2em;
        }
        .stButton>button:hover {
            background: #fff;
            color: #000;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='color:#d4af37; font-family:Garamond; text-align:center;'>ELDEN RING</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#888888; font-family:Garamond; text-align:center;'>RANDOM BUILD GENERATOR</h3>", unsafe_allow_html=True)

    fichier_csv = 'Classeur2.csv'
    donnees = charger_donnees(fichier_csv)

    if not donnees:
        st.error(f"Le fichier '{fichier_csv}' est introuvable. Assurez-vous qu'il est dans le même dossier que l'application.")
        return

    if 'build' not in st.session_state:
        st.session_state['build'] = generer_build_logique(donnees)

    if st.button("NOUVEAU BUILD ALÉATOIRE"):
        st.session_state['build'] = generer_build_logique(donnees)

    build = st.session_state['build']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h4 style='color:#d4af37;'>ÉQUIPEMENT</h4>", unsafe_allow_html=True)
        st.markdown(f"<b>Main Droite:</b> <span style='color:#eeeeee'>{build['main_hand']}</span>", unsafe_allow_html=True)
        st.markdown(f"<b>Tenue:</b> <span style='color:#eeeeee'>{build['grip']}</span>", unsafe_allow_html=True)
        st.markdown(f"<b>Main Gauche:</b> <span style='color:#eeeeee'>{build['off_hand']}</span>", unsafe_allow_html=True)
        st.markdown(f"<b>Armure:</b> <span style='color:#eeeeee'>{build['armor']}</span>", unsafe_allow_html=True)
        color_spirit = '#00ff99' if build['spirit'] != 'Aucun' else '#555555'
        st.markdown(f"<b>Esprit:</b> <span style='color:{color_spirit}'>{build['spirit']}</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='color:#d4af37;'>MAGIE</h4>", unsafe_allow_html=True)
        if not build['spells']:
            st.markdown("<span style='color:#555555;'>(Aucun sort)</span>", unsafe_allow_html=True)
        else:
            for spell in build['spells']:
                st.markdown(f"<span style='color:#a0c0ff;'>• {spell}</span>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()