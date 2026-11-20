# impot-revenu-fr

Estimer son impôt sur le revenu en France, en ligne de commande ou en Python, avec le détail des étapes : parts, impôt brut, plafonnement du quotient familial, décote, taux marginal et taux moyen. Aucune dépendance.

Paramètres inclus : imposition 2026 des revenus 2025 (loi de finances pour 2026).

## Installation

```bash
pip install git+https://github.com/TheoPSR01/impot-revenu-fr.git
```

Python 3.10 ou plus récent.

## En ligne de commande

Couple marié ou pacsé avec deux enfants et 60 000 € de revenu net imposable :

```bash
impot-revenu-fr 60000 --couple --enfants 2
```

```
Nombre de parts            : 3
Impôt brut                 : 2 772 €
Décote                     : 229 €
Impôt net                  : 2 543 €
Taux marginal / moyen      : 11 % / 4,2 %
Avant réductions et crédits d'impôt, hors contribution sur les hauts revenus.
```

```bash
impot-revenu-fr 30000                              # célibataire
impot-revenu-fr 40000 --enfants 1 --parent-isole   # parent isolé (case T)
```

## En Python

```python
from impot_revenu import calculer

r = calculer(200000, couple=True, enfants=2)
print(r.impot_brut, r.plafonnement)   # 45987 True
print(r.taux_marginal, r.taux_moyen)
```

## Règles appliquées (revenus 2025)

Barème par part : 0 % jusqu'à 11 600 €, 11 % jusqu'à 29 579 €, 30 % jusqu'à 84 577 €, 41 % jusqu'à 181 917 €, 45 % au-delà.

Parts : 1 par adulte, 0,5 pour chacun des deux premiers enfants, 1 à partir du troisième, 0,5 de plus pour un parent qui élève seul ses enfants (case T).

Plafonnement du quotient familial : l'avantage de chaque demi-part supplémentaire est limité à 1 807 € ; pour un parent isolé, la part entière du premier enfant est limitée à 4 262 €.

Décote : 897 € (personne seule) ou 1 483 € (couple) moins 45,25 % de l'impôt brut. Un impôt inférieur à 61 € n'est pas recouvré.

## Limites

Le point de départ est le revenu net imposable : l'outil n'applique ni l'abattement de 10 % sur les salaires, ni les frais réels. Il ne gère pas les demi-parts pour invalidité, anciens combattants ou enfants en résidence alternée, ni les réductions et crédits d'impôt, la contribution exceptionnelle sur les hauts revenus, les revenus soumis au prélèvement forfaitaire unique ou les revenus exceptionnels. Pour votre déclaration, le simulateur d'impots.gouv.fr fait foi.

Quand une nouvelle loi de finances paraît, il suffit d'ajouter une entrée dans `PARAMETRES`.

## Contribuer

```bash
git clone https://github.com/TheoPSR01/impot-revenu-fr.git
cd impot-revenu-fr
pip install -e ".[dev]"
pytest
```

## Licence

MIT
