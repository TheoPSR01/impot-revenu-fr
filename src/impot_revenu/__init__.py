"""impot_revenu : calcul de l'impôt sur le revenu français.

Paramètres de l'imposition 2026 des revenus 2025 (loi de finances pour 2026) :
barème par part, plafonnement des effets du quotient familial, décote et
seuil de mise en recouvrement.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Union

__version__ = "0.1.0"

Montant = Union[int, float, str, Decimal]
D = Decimal


@dataclass(frozen=True)
class Parametres:
    annee_revenus: int
    tranches: tuple            # (plafond haut de la tranche ou None, taux)
    plafond_demi_part: Decimal
    plafond_parent_isole: Decimal   # part entière du premier enfant d'un parent isolé (case T)
    decote_seule: Decimal
    decote_couple: Decimal
    taux_decote: Decimal
    seuil_recouvrement: Decimal


PARAMETRES = {
    2025: Parametres(
        annee_revenus=2025,
        tranches=((D(11600), D(0)), (D(29579), D("0.11")), (D(84577), D("0.30")),
                  (D(181917), D("0.41")), (None, D("0.45"))),
        plafond_demi_part=D(1807),
        plafond_parent_isole=D(4262),
        decote_seule=D(897),
        decote_couple=D(1483),
        taux_decote=D("0.4525"),
        seuil_recouvrement=D(61),
    ),
}


def _d(x: Montant) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x).replace(",", ".").replace(" ", ""))


def _euro(x: Decimal) -> Decimal:
    return x.quantize(D(1), rounding=ROUND_HALF_UP)


def nombre_de_parts(couple: bool = False, enfants: int = 0, parent_isole: bool = False) -> Decimal:
    """Parts de quotient familial : 1 par adulte, 0,5 pour chacun des deux premiers
    enfants, 1 à partir du troisième, 0,5 de plus pour un parent isolé (case T)."""
    if enfants < 0:
        raise ValueError("nombre d'enfants négatif")
    parts = D(2) if couple else D(1)
    parts += D("0.5") * min(enfants, 2) + D(1) * max(enfants - 2, 0)
    if parent_isole and not couple and enfants > 0:
        parts += D("0.5")
    return parts


def impot_bareme(revenu: Montant, parts: Montant, annee: int = 2025) -> Decimal:
    """Impôt issu du barème progressif, non arrondi : parts × barème(revenu / parts)."""
    p = PARAMETRES[annee]
    r, n = _d(revenu), _d(parts)
    if r < 0 or n <= 0:
        raise ValueError("revenu positif et nombre de parts strictement positif attendus")
    q = r / n
    impot, bas = D(0), D(0)
    for haut, taux in p.tranches:
        if haut is None or q > haut:
            tranche = (q if haut is None else haut) - bas
        else:
            tranche = q - bas
        if tranche > 0:
            impot += tranche * taux
        if haut is None or q <= haut:
            break
        bas = haut
    return impot * n


@dataclass(frozen=True)
class Resultat:
    revenu: Decimal
    parts: Decimal
    impot_avant_plafonnement: Decimal
    plafonnement: bool
    impot_brut: Decimal
    decote: Decimal
    impot_net: Decimal           # avant réductions et crédits d'impôt
    recouvre: bool              # False si l'impôt est inférieur au seuil de 61 €
    taux_marginal: Decimal
    taux_moyen: Decimal


def taux_marginal(revenu: Montant, parts: Montant, annee: int = 2025) -> Decimal:
    q = _d(revenu) / _d(parts)
    for haut, taux in PARAMETRES[annee].tranches:
        if haut is None or q <= haut:
            return taux
    return PARAMETRES[annee].tranches[-1][1]


def calculer(revenu: Montant, couple: bool = False, enfants: int = 0, parent_isole: bool = False,
             annee: int = 2025) -> Resultat:
    """Impôt dû pour un revenu net imposable annuel (après abattements)."""
    if annee not in PARAMETRES:
        raise ValueError(f"paramètres disponibles pour les revenus {sorted(PARAMETRES)}")
    p = PARAMETRES[annee]
    r = _d(revenu)
    parts = nombre_de_parts(couple, enfants, parent_isole)
    base = D(2) if couple else D(1)

    avec_parts = impot_bareme(r, parts, annee)
    demi_parts = int((parts - base) * 2)
    if parent_isole and not couple and enfants > 0:
        avantage_max = p.plafond_parent_isole + p.plafond_demi_part * max(demi_parts - 2, 0)
    else:
        avantage_max = p.plafond_demi_part * demi_parts
    sans_parts = impot_bareme(r, base, annee) - avantage_max
    plafonne = demi_parts > 0 and sans_parts > avec_parts
    brut = _euro(max(avec_parts, sans_parts))

    seuil = p.decote_couple if couple else p.decote_seule
    decote = max(D(0), _euro(seuil - p.taux_decote * brut))
    decote = min(decote, brut)
    net = brut - decote
    recouvre = net >= p.seuil_recouvrement
    moyen = (net / r * 100).quantize(D("0.1"), rounding=ROUND_HALF_UP) if r else D(0)
    return Resultat(r, parts, _euro(avec_parts), plafonne, brut, decote, net, recouvre,
                    taux_marginal(r, parts, annee) * 100, moyen)


def _fr(x: Decimal) -> str:
    return f"{x:,.0f}".replace(",", " ")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="impot-revenu-fr", description="Impôt sur le revenu 2026 (revenus 2025).")
    ap.add_argument("--version", action="version", version=f"impot-revenu-fr {__version__}")
    ap.add_argument("revenu", help="revenu net imposable annuel du foyer")
    ap.add_argument("--couple", action="store_true", help="mariés ou pacsés (imposition commune)")
    ap.add_argument("--enfants", type=int, default=0, help="nombre d'enfants à charge")
    ap.add_argument("--parent-isole", action="store_true", help="vous élevez seul vos enfants (case T)")
    a = ap.parse_args(argv)
    try:
        r = calculer(a.revenu, a.couple, a.enfants, a.parent_isole)
    except (ValueError, InvalidOperation) as exc:
        print(f"impot-revenu-fr : {exc}", file=sys.stderr)
        return 2
    parts = str(r.parts.normalize()).replace(".", ",")
    print(f"Nombre de parts            : {parts}")
    print(f"Impôt brut                 : {_fr(r.impot_brut)} €" + (" (quotient familial plafonné)" if r.plafonnement else ""))
    print(f"Décote                     : {_fr(r.decote)} €")
    print(f"Impôt net                  : {_fr(r.impot_net)} €" + ("" if r.recouvre else " (inférieur à 61 € : non recouvré)"))
    print(f"Taux marginal / moyen      : {r.taux_marginal.normalize()} % / {str(r.taux_moyen).replace('.', ',')} %")
    print("Avant réductions et crédits d'impôt, hors contribution sur les hauts revenus.")
    return 0


__all__ = ["PARAMETRES", "Parametres", "Resultat", "calculer", "impot_bareme", "main", "nombre_de_parts", "taux_marginal"]
