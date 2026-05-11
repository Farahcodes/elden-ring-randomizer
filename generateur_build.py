import os
import sys
import random

import pandas as pd
import streamlit as st

# =============================================================================
# 1. LOGIQUE (BACKEND)
# =============================================================================

RANGED_CLASSES = {
    'Light Bows', 'Bows', 'Greatbows', 'Crossbows', 'Ballistas'
}
SHIELD_CLASSES = {
    'Small Shields', 'Medium Shields', 'Greatshields'
}
MAGIC_OBJECT_CLASSES = {'Glintstone Staves', 'Sacred Seals'}


def _get_application_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _read_csv_file(filename, header=0, names=None):
    path = os.path.join(_get_application_path(), filename)
    try:
        for encoding in ('utf-8', 'latin-1'):
            try:
                df = pd.read_csv(path, sep=';', header=header, names=names, encoding=encoding, dtype=str, keep_default_na=False)
                return df
            except UnicodeDecodeError:
                continue
    except FileNotFoundError:
        return None
    return None


def _to_yes(value):
    return str(value).strip().lower() == 'yes'


def charger_donnees(_=None):
    df_main_hand = _read_csv_file('Main Hand.csv', header=0)
    df_second_hand = _read_csv_file('Second Hand.csv', header=0)
    df_magic = _read_csv_file('Magic.csv', header=0)
    df_armor = _read_csv_file('Armor.csv', header=0)
    df_spirits = _read_csv_file('Spirit.csv', header=None, names=['Spirit'])
    df_tools = _read_csv_file('Tools.csv', header=None, names=['Tool'])

    if df_main_hand is None or df_second_hand is None or df_magic is None or df_armor is None or df_spirits is None:
        return None

    df_main_hand.columns = [c.strip() for c in df_main_hand.columns]
    df_second_hand.columns = [c.strip() for c in df_second_hand.columns]
    df_magic.columns = [c.strip() for c in df_magic.columns]
    df_armor.columns = [c.strip() for c in df_armor.columns]

    df_main_hand = df_main_hand.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_second_hand = df_second_hand.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_magic = df_magic.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_armor = df_armor.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
    df_spirits = df_spirits.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x)) if not df_spirits.empty else df_spirits
    df_tools = df_tools.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x)) if df_tools is not None else pd.DataFrame(columns=['Tool'])

    df_main_hand = df_main_hand[df_main_hand['leveled'].apply(_to_yes)]
    df_main_hand = df_main_hand[df_main_hand['Weapon'].astype(bool)].copy()
    df_main_hand['Dual'] = df_main_hand['Dual'].fillna('No')
    df_main_hand['2 Handed'] = df_main_hand['2 Handed'].fillna('No')

    df_second_hand = df_second_hand[df_second_hand['leveled'].apply(_to_yes)]
    df_second_hand = df_second_hand[df_second_hand['Object'].astype(bool)].copy()
    df_second_hand['Catalist bonus'] = df_second_hand['Catalist bonus'].fillna('')

    df_magic = df_magic[df_magic['Spell'].astype(bool)].copy()
    df_magic['Slots'] = pd.to_numeric(df_magic['Slots'], errors='coerce').fillna(1).astype(int)

    df_armor = df_armor[df_armor['Name'].astype(bool)].copy()
    df_armor_sets = df_armor[df_armor['Category'] == 'Armor Sets'].copy()
    df_armor_pieces = df_armor[df_armor['Category'] == 'Armor Pieces'].copy()

    df_spirits = df_spirits[df_spirits['Spirit'].astype(bool)].copy()

    if df_tools is None:
        df_tools = pd.DataFrame(columns=['Tool'])
    else:
        df_tools = df_tools[df_tools['Tool'].astype(bool)].copy()

    return df_main_hand, df_second_hand, df_magic, df_armor_sets, df_armor_pieces, df_spirits, df_tools


def generer_build_logique(data):
    df_main_hand, df_second_hand, df_magic, df_armor_sets, df_armor_pieces, df_spirits, df_tools = data

    build = {
        'main_hand': '',
        'grip': '',
        'off_hand': '',
        'tool': 'Aucun',
        'armor': '',
        'spells': [],
        'spirit': 'Aucun'
    }

    main_weapon = df_main_hand.sample(n=1).iloc[0]
    build['main_hand'] = main_weapon['Weapon']
    main_class = main_weapon['Class']
    est_double = _to_yes(main_weapon['Dual'])
    peut_2_mains = _to_yes(main_weapon['2 Handed'])
    est_carian_sword = main_weapon['Weapon'] == 'Carian Sorcery Sword'

    off_hand_row = None
    mode_tenue = '1-Handed'

    if est_double:
        mode_tenue = 'Dual Wield'
        build['off_hand'] = '(Arme Double)'
    elif peut_2_mains and random.random() < 2 / 3:
        mode_tenue = '2-Handed'
        build['off_hand'] = 'Aucune'

    if mode_tenue == '1-Handed':
        if main_class in RANGED_CLASSES:
            torches = df_second_hand[df_second_hand['Class'] == 'Torches']
            if not torches.empty:
                off_hand_row = torches.sample(n=1).iloc[0]
                build['off_hand'] = off_hand_row['Object']
            if not df_tools.empty:
                build['tool'] = df_tools.sample(n=1).iloc[0]['Tool']
        elif main_class in SHIELD_CLASSES:
            choices = df_second_hand[df_second_hand['Class'].isin(MAGIC_OBJECT_CLASSES)]
            if not choices.empty:
                off_hand_row = choices.sample(n=1).iloc[0]
                build['off_hand'] = off_hand_row['Object']
        elif build['main_hand'] in {'Wakizashi', 'Main Gauche'}:
            choices = df_second_hand[df_second_hand['Class'].isin(MAGIC_OBJECT_CLASSES)]
            if not choices.empty:
                off_hand_row = choices.sample(n=1).iloc[0]
                build['off_hand'] = off_hand_row['Object']
        else:
            if random.random() < 0.5:
                choices = df_second_hand[df_second_hand['Class'].isin(MAGIC_OBJECT_CLASSES)]
                if not choices.empty:
                    off_hand_row = choices.sample(n=1).iloc[0]
                    build['off_hand'] = off_hand_row['Object']
            else:
                same_class = df_main_hand[
                    (df_main_hand['Class'] == main_class) &
                    (df_main_hand['Weapon'] != main_weapon['Weapon']) &
                    (~df_main_hand['Dual'].apply(_to_yes))
                ]

                if main_weapon['Weapon'] == 'Pickaxe':
                    same_class = df_main_hand[df_main_hand['Class'] == 'Greataxes']
                elif main_class == 'Daggers':
                    same_class = same_class[~same_class['Weapon'].isin(['Wakizashi', 'Main Gauche'])]

                if main_class == 'Greataxes':
                    extra = df_main_hand[df_main_hand['Weapon'] == 'Pickaxe']
                    same_class = pd.concat([same_class, extra], ignore_index=True).drop_duplicates(subset=['Weapon'])
                elif main_class == 'Katanas':
                    extra = df_main_hand[df_main_hand['Weapon'] == 'Wakizashi']
                    same_class = pd.concat([same_class, extra], ignore_index=True).drop_duplicates(subset=['Weapon'])
                elif main_class == 'Thrusting Swords':
                    extra = df_main_hand[df_main_hand['Weapon'] == 'Main Gauche']
                    same_class = pd.concat([same_class, extra], ignore_index=True).drop_duplicates(subset=['Weapon'])

                if not same_class.empty:
                    off_hand_row = same_class.sample(n=1).iloc[0]
                    build['off_hand'] = off_hand_row['Weapon']
                else:
                    choices = df_second_hand[df_second_hand['Class'].isin(MAGIC_OBJECT_CLASSES)]
                    if not choices.empty:
                        off_hand_row = choices.sample(n=1).iloc[0]
                        build['off_hand'] = off_hand_row['Object']

    build['grip'] = mode_tenue

    acces_magie = False
    accessible_types = []
    bonus_ecole = None
    spell_schools = set()

    if mode_tenue == '1-Handed':
        if off_hand_row is not None and off_hand_row['Class'] in MAGIC_OBJECT_CLASSES:
            if off_hand_row['Object'] == 'Staff of the Great Beyond':
                acces_magie = True
                accessible_types = None
            elif off_hand_row['Class'] == 'Glintstone Staves':
                acces_magie = True
                accessible_types = ['Sorceries']
            elif off_hand_row['Class'] == 'Sacred Seals':
                acces_magie = True
                accessible_types = ['Incantations']
            bonus_ecole = off_hand_row['Catalist bonus'] if pd.notna(off_hand_row.get('Catalist bonus', None)) else None
        if est_carian_sword:
            acces_magie = True
            accessible_types = ['Sorceries']

    if mode_tenue in {'Dual Wield', '2-Handed'}:
        acces_magie = False
        accessible_types = []

    if acces_magie:
        pool = df_magic.copy() if accessible_types is None else df_magic[df_magic['Type'].isin(accessible_types)].copy()
        pool['Slots'] = pd.to_numeric(pool['Slots'], errors='coerce').fillna(1).astype(int)
        remaining_slots = 10

        while remaining_slots > 0 and not pool.empty:
            candidates = pool[pool['Slots'] <= remaining_slots].copy()
            if candidates.empty:
                break

            weights = pd.Series(1.0, index=candidates.index)
            if bonus_ecole:
                weights += (candidates['School'] == bonus_ecole).astype(float) * 2.0

            choix = candidates.sample(n=1, weights=weights).iloc[0]
            build['spells'].append(f"{choix['Spell']} ({choix['Slots']})")
            if pd.notna(choix['School']):
                spell_schools.add(choix['School'])

            remaining_slots -= int(choix['Slots'])
            pool = pool.drop(choix.name)

    weight_school = spell_schools

    if random.random() < 0.9 and not df_armor_sets.empty:
        armor_pool = df_armor_sets.copy()
        weights = pd.Series(1.0, index=armor_pool.index)
        if weight_school:
            weights += armor_pool['Bonus'].isin(weight_school).astype(float) * 4.0
        armor_choice = armor_pool.sample(n=1, weights=weights).iloc[0]
        build['armor'] = armor_choice['Name']
        if pd.notna(armor_choice['Bonus']) and armor_choice['Bonus']:
            build['armor'] += f" (Bonus: {armor_choice['Bonus']})"
    else:
        helms = df_armor_pieces[df_armor_pieces['Type'] == 'Helms'].copy()
        chests = df_armor_pieces[df_armor_pieces['Type'] == 'Chests Armor'].copy()
        if helms.empty or chests.empty:
            armor_pool = df_armor_sets.copy()
            weights = pd.Series(1.0, index=armor_pool.index)
            if weight_school:
                weights += armor_pool['Bonus'].isin(weight_school).astype(float) * 4.0
            armor_choice = armor_pool.sample(n=1, weights=weights).iloc[0]
            build['armor'] = armor_choice['Name']
            if pd.notna(armor_choice['Bonus']) and armor_choice['Bonus']:
                build['armor'] += f" (Bonus: {armor_choice['Bonus']})"
        else:
            helm_weights = pd.Series(1.0, index=helms.index)
            chest_weights = pd.Series(1.0, index=chests.index)
            if weight_school:
                helm_weights += helms['Bonus'].isin(weight_school).astype(float) * 4.0
                chest_weights += chests['Bonus'].isin(weight_school).astype(float) * 4.0
            helm_choice = helms.sample(n=1, weights=helm_weights).iloc[0]
            chest_choice = chests.sample(n=1, weights=chest_weights).iloc[0]
            armor_text = f"Helm: {helm_choice['Name']}"
            if pd.notna(helm_choice['Bonus']) and helm_choice['Bonus']:
                armor_text += f" (Bonus: {helm_choice['Bonus']})"
            armor_text += f" / Chest: {chest_choice['Name']}"
            if pd.notna(chest_choice['Bonus']) and chest_choice['Bonus']:
                armor_text += f" (Bonus: {chest_choice['Bonus']})"
            build['armor'] = armor_text

    if not df_spirits.empty and random.random() < 0.5:
        build['spirit'] = df_spirits.sample(n=1).iloc[0]['Spirit']

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

    donnees = charger_donnees()

    if not donnees:
        st.error('Impossible de charger les fichiers de données. Assurez-vous que Main Hand.csv, Second Hand.csv, Magic.csv, Armor.csv, Spirit.csv et Tools.csv sont présents.')
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
        st.markdown(f"<b>Outil:</b> <span style='color:#eeeeee'>{build['tool']}</span>", unsafe_allow_html=True)
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