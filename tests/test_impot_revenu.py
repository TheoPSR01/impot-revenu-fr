from decimal import Decimal

import pytest

from impot_revenu import calculer, impot_bareme, main, nombre_de_parts, taux_marginal


@pytest.mark.parametrize("couple,enfants,isole,attendu", [
    (False, 0, False, "1"),
    (True, 0, False, "2"),
    (True, 2, False, "3"),
    (True, 3, False, "4"),
    (False, 1, True, "2"),
    (False, 2, True, "2.5"),
    (False, 1, False, "1.5"),
])
def test_parts(couple, enfants, isole, attendu):
    assert nombre_de_parts(couple, enfants, isole) == Decimal(attendu)


def test_bareme():
    assert impot_bareme(11600, 1) == 0
    assert impot_bareme(29579, 1) == Decimal("1977.69")
    assert impot_bareme(30000, 1) == Decimal("2103.99")


def test_celibataire_30000():
    r = calculer(30000)
    assert r.impot_brut == 2104 and r.decote == 0 and r.impot_net == 2104
    assert r.taux_marginal == 30


def test_couple_deux_enfants_avec_decote():
    r = calculer(60000, couple=True, enfants=2)
    assert r.parts == 3
    assert r.impot_brut == 2772
    assert r.decote == 229          # 1 483 - 45,25 % × 2 772
    assert r.impot_net == 2543
    assert not r.plafonnement


def test_parent_isole():
    r = calculer(40000, enfants=1, parent_isole=True)
    assert r.parts == 2
    assert r.impot_brut == 1848
    assert r.impot_net == 1848 - 61


def test_plafonnement_du_quotient_familial():
    r = calculer(200000, couple=True, enfants=2)
    assert r.plafonnement
    assert r.impot_brut == 45987     # 49 601,04 - 2 × 1 807


def test_petit_revenu_non_recouvre():
    r = calculer(17000)
    assert r.impot_brut == 594
    assert r.impot_net == 0
    assert not r.recouvre


def test_taux_marginal():
    assert taux_marginal(20000, 1) == Decimal("0.11")
    assert taux_marginal(500000, 1) == Decimal("0.45")


def test_erreurs():
    with pytest.raises(ValueError):
        calculer(-1)
    with pytest.raises(ValueError):
        calculer(30000, annee=2019)


def test_cli(capsys):
    assert main(["60000", "--couple", "--enfants", "2"]) == 0
    out = capsys.readouterr().out
    assert "Impôt net                  : 2 543 €" in out
    assert "Nombre de parts            : 3" in out


def test_cli_aide():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
