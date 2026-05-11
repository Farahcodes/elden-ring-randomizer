import random

import pandas as pd
import pytest

import generateur_build


def make_df(columns, rows):
    return pd.DataFrame(rows, columns=columns)


def test_charger_donnees_loads_required_data():
    data = generateur_build.charger_donnees()
    assert data is not None

    main_hand, second_hand, magic, armor_sets, armor_pieces, spirits, tools = data
    assert not main_hand.empty
    assert {'Class', 'Weapon', 'Dual', '2 Handed', 'leveled'}.issubset(set(main_hand.columns))
    assert not second_hand.empty
    assert 'Spell' in magic.columns
    assert not spirits.empty
    assert 'Tool' in tools.columns


def test_generer_build_logique_dual_wield_no_magic():
    main_hand = make_df(
        ['Class', 'Weapon', 'Dual', '2 Handed', 'leveled'],
        [['Daggers', 'Twin Daggers', 'Yes', 'No', 'Yes']]
    )
    second_hand = make_df(
        ['Class', 'Object', 'Catalist bonus', 'leveled'],
        [['Sacred Seals', 'Golden Order Seal', '', 'Yes']]
    )
    magic = make_df(
        ['Type', 'School', 'Spell', 'Slots'],
        [['Incantations', 'Golden Order', 'Golden Vow', '1']]
    )
    armor_sets = make_df(
        ['Category', 'Type', 'Name', 'Bonus'],
        [['Armor Sets', '', 'Raptor Set', 'Golden Order']]
    )
    armor_pieces = make_df(
        ['Category', 'Type', 'Name', 'Bonus'],
        [['Armor Pieces', 'Helms', 'Raptor Helm', 'Golden Order']]
    )
    spirits = make_df(['Spirit'], [['Ancient Dragon']])
    tools = make_df(['Tool'], [['Bone Arrow']])

    build = generateur_build.generer_build_logique((main_hand, second_hand, magic, armor_sets, armor_pieces, spirits, tools))

    assert build['grip'] == 'Dual Wield'
    assert build['off_hand'] == '(Arme Double)'
    assert build['spells'] == []
    assert build['tool'] == 'Aucun' or build['tool'] == 'Bone Arrow'


def test_generer_build_logique_with_carian_sorcery_sword_access_magic(monkeypatch):
    main_hand = make_df(
        ['Class', 'Weapon', 'Dual', '2 Handed', 'leveled'],
        [['Glintstone Staves', 'Carian Sorcery Sword', 'No', 'No', 'Yes']]
    )
    second_hand = make_df(
        ['Class', 'Object', 'Catalist bonus', 'leveled'],
        [['Glintstone Staves', 'Glintstone Staff', '', 'Yes']]
    )
    magic = make_df(
        ['Type', 'School', 'Spell', 'Slots'],
        [['Sorceries', 'Glintstone', 'Glintstone Arc', '1']]
    )
    armor_sets = make_df(
        ['Category', 'Type', 'Name', 'Bonus'],
        [['Armor Sets', '', 'Raptor Set', 'Glintstone']]
    )
    armor_pieces = make_df(
        ['Category', 'Type', 'Name', 'Bonus'],
        [['Armor Pieces', 'Helms', 'Raptor Helm', 'Glintstone']]
    )
    spirits = make_df(['Spirit'], [['Ancient Dragon']])
    tools = make_df(['Tool'], [['Bone Arrow']])

    monkeypatch.setattr(random, 'random', lambda: 0.4)

    build = generateur_build.generer_build_logique((main_hand, second_hand, magic, armor_sets, armor_pieces, spirits, tools))

    assert build['main_hand'] == 'Carian Sorcery Sword'
    assert any('Glintstone Arc' in spell for spell in build['spells'])
    assert build['off_hand'] == 'Glintstone Staff'
