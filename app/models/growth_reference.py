"""WHO Child Growth Standards (2006) - Referenzperzentile für Wachstumskurven.

Quelle: WHO Child Growth Standards, https://www.who.int/tools/child-growth-standards
(Weight-for-age und Length/height-for-age, Geburt bis 24 Monate, getrennt nach
Geschlecht). Die Werte sind an Ankerpunkten hinterlegt (monatlich im ersten
Lebensjahr, alle drei Monate danach) und werden linear zwischen den Ankerpunkten
interpoliert - ausreichend genau für eine rein visuelle Einordnung im Trends-Chart.

Wichtig: Dies ist keine medizinische Bewertung oder Diagnose, sondern eine
Orientierungshilfe. Bei Fragen zur Entwicklung des Kindes bitte immer die
Kinderärztin/den Kinderarzt konsultieren.
"""

PERCENTILE_KEYS = ['p3', 'p15', 'p50', 'p85', 'p97']

# Gewicht-für-Alter in kg: {gender: {age_months: [p3, p15, p50, p85, p97]}}
WEIGHT_FOR_AGE_KG = {
    'm': {
        0: [2.5, 2.9, 3.3, 3.9, 4.4],
        1: [3.4, 3.9, 4.5, 5.1, 5.8],
        2: [4.3, 4.9, 5.6, 6.3, 7.1],
        3: [5.0, 5.6, 6.4, 7.2, 8.0],
        4: [5.6, 6.2, 7.0, 7.8, 8.7],
        5: [6.0, 6.7, 7.5, 8.4, 9.3],
        6: [6.4, 7.1, 7.9, 8.8, 9.8],
        7: [6.7, 7.4, 8.3, 9.2, 10.3],
        8: [6.9, 7.7, 8.6, 9.6, 10.7],
        9: [7.1, 7.9, 8.9, 9.9, 11.0],
        10: [7.4, 8.2, 9.2, 10.2, 11.4],
        11: [7.6, 8.4, 9.4, 10.5, 11.7],
        12: [7.7, 8.6, 9.6, 10.8, 12.0],
        15: [8.3, 9.2, 10.3, 11.5, 12.8],
        18: [8.8, 9.8, 10.9, 12.2, 13.7],
        21: [9.2, 10.3, 11.5, 12.9, 14.5],
        24: [9.7, 10.8, 12.2, 13.6, 15.3],
    },
    'f': {
        0: [2.4, 2.8, 3.2, 3.7, 4.2],
        1: [3.2, 3.6, 4.2, 4.8, 5.5],
        2: [3.9, 4.5, 5.1, 5.8, 6.6],
        3: [4.5, 5.2, 5.8, 6.6, 7.5],
        4: [5.0, 5.7, 6.4, 7.3, 8.2],
        5: [5.4, 6.1, 6.9, 7.8, 8.8],
        6: [5.7, 6.5, 7.3, 8.2, 9.3],
        7: [6.0, 6.8, 7.6, 8.6, 9.8],
        8: [6.3, 7.0, 7.9, 8.9, 10.2],
        9: [6.5, 7.3, 8.2, 9.3, 10.5],
        10: [6.7, 7.5, 8.5, 9.6, 10.9],
        11: [6.9, 7.7, 8.7, 9.9, 11.2],
        12: [7.0, 7.9, 8.9, 10.1, 11.5],
        15: [7.6, 8.5, 9.6, 10.9, 12.4],
        18: [8.1, 9.1, 10.2, 11.6, 13.2],
        21: [8.6, 9.6, 10.9, 12.4, 14.1],
        24: [9.0, 10.2, 11.5, 13.0, 14.8],
    },
}

# Länge/Größe-für-Alter in cm: {gender: {age_months: [p3, p15, p50, p85, p97]}}
LENGTH_FOR_AGE_CM = {
    'm': {
        0: [46.1, 47.9, 49.9, 51.8, 53.7],
        1: [50.8, 52.8, 54.7, 56.7, 58.6],
        2: [54.4, 56.4, 58.4, 60.4, 62.4],
        3: [57.3, 59.4, 61.4, 63.5, 65.5],
        4: [59.7, 61.8, 63.9, 66.0, 68.0],
        5: [61.7, 63.8, 65.9, 68.0, 70.1],
        6: [63.3, 65.5, 67.6, 69.8, 72.0],
        7: [64.8, 67.0, 69.2, 71.3, 73.5],
        8: [66.2, 68.4, 70.6, 72.8, 75.0],
        9: [67.5, 69.7, 72.0, 74.2, 76.5],
        10: [68.7, 71.0, 73.3, 75.6, 78.0],
        11: [69.9, 72.2, 74.5, 76.9, 79.2],
        12: [71.0, 73.4, 75.7, 78.1, 80.5],
        15: [74.1, 76.6, 79.1, 81.7, 84.2],
        18: [76.9, 79.6, 82.3, 85.0, 87.7],
        21: [79.4, 82.3, 85.1, 88.0, 90.9],
        24: [81.7, 84.8, 87.8, 90.9, 93.9],
    },
    'f': {
        0: [45.4, 47.3, 49.1, 51.0, 52.9],
        1: [49.8, 51.7, 53.7, 55.6, 57.6],
        2: [53.0, 55.0, 57.1, 59.1, 61.1],
        3: [55.6, 57.7, 59.8, 61.9, 64.0],
        4: [57.8, 59.9, 62.1, 64.3, 66.4],
        5: [59.6, 61.8, 64.0, 66.2, 68.5],
        6: [61.2, 63.5, 65.7, 68.0, 70.3],
        7: [62.7, 64.9, 67.3, 69.6, 71.9],
        8: [64.0, 66.4, 68.7, 71.1, 73.5],
        9: [65.3, 67.7, 70.1, 72.6, 75.0],
        10: [66.5, 69.0, 71.5, 74.0, 76.4],
        11: [67.7, 70.3, 72.8, 75.3, 77.9],
        12: [68.9, 71.4, 74.0, 76.6, 79.2],
        15: [72.0, 74.8, 77.5, 80.2, 83.0],
        18: [74.9, 77.8, 80.7, 83.6, 86.5],
        21: [77.5, 80.6, 83.7, 86.7, 89.8],
        24: [80.0, 83.2, 86.4, 89.6, 92.9],
    },
}


def _interpolate(table, age_months):
    """Interpoliert linear zwischen den Ankerpunkten der Referenztabelle."""
    months = sorted(table.keys())
    if age_months <= months[0]:
        values = table[months[0]]
    elif age_months >= months[-1]:
        values = table[months[-1]]
    else:
        values = None
        for lo, hi in zip(months, months[1:]):
            if lo <= age_months <= hi:
                lo_vals, hi_vals = table[lo], table[hi]
                frac = (age_months - lo) / (hi - lo) if hi != lo else 0
                values = [lo_v + (hi_v - lo_v) * frac for lo_v, hi_v in zip(lo_vals, hi_vals)]
                break
        if values is None:
            values = table[months[-1]]
    return dict(zip(PERCENTILE_KEYS, [round(v, 2) for v in values]))


def get_weight_percentiles(gender, age_months):
    """Gibt {p3, p15, p50, p85, p97} in kg für Geschlecht/Alter zurück, oder None."""
    if gender not in ('m', 'f') or age_months is None or age_months < 0:
        return None
    return _interpolate(WEIGHT_FOR_AGE_KG[gender], age_months)


def get_height_percentiles(gender, age_months):
    """Gibt {p3, p15, p50, p85, p97} in cm für Geschlecht/Alter zurück, oder None."""
    if gender not in ('m', 'f') or age_months is None or age_months < 0:
        return None
    return _interpolate(LENGTH_FOR_AGE_CM[gender], age_months)
