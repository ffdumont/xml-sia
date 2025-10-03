#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('sia_database.db')
cursor = conn.cursor()

print("=== Volumes TMA PARIS ===")
query = """
SELECT v.plancher, v.plancher_ref_unite, v.plafond, v.plafond_ref_unite, v.classe, p.numero_partie
FROM volumes v 
JOIN parties p ON v.partie_ref = p.pk 
JOIN espaces e ON p.espace_ref = e.pk 
WHERE e.lk LIKE '%TMA PARIS%' 
ORDER BY p.numero_partie, v.plancher
"""

cursor.execute(query)
results = cursor.fetchall()

print(f"Nombre de volumes: {len(results)}")
print("\nDétail des volumes:")
print("Plancher | Unité | Plafond | Unité | Classe | Partie")
print("-" * 60)

for plancher, p_unite, plafond, pl_unite, classe, partie in results:
    print(f"{plancher:8} | {p_unite:5} | {plafond:7} | {pl_unite:5} | {classe:6} | {partie}")

# Vérifier s'il y a des volumes au sol
print("\n=== Volumes au sol (SFC/GND) ===")
cursor.execute("""
SELECT COUNT(*) FROM volumes v 
JOIN parties p ON v.partie_ref = p.pk 
JOIN espaces e ON p.espace_ref = e.pk 
WHERE e.lk LIKE '%TMA PARIS%' 
AND (v.plancher = 'SFC' OR v.plancher = 'GND' OR v.plancher = '0')
""")

count_sol = cursor.fetchone()[0]
print(f"Nombre de volumes au sol: {count_sol}")

if count_sol > 0:
    cursor.execute("""
    SELECT v.plancher, v.plancher_ref_unite, v.plafond, v.plafond_ref_unite, v.classe, p.numero_partie
    FROM volumes v 
    JOIN parties p ON v.partie_ref = p.pk 
    JOIN espaces e ON p.espace_ref = e.pk 
    WHERE e.lk LIKE '%TMA PARIS%' 
    AND (v.plancher = 'SFC' OR v.plancher = 'GND' OR v.plancher = '0')
    ORDER BY p.numero_partie
    """)
    
    sol_results = cursor.fetchall()
    print("\nVolumes au sol:")
    for plancher, p_unite, plafond, pl_unite, classe, partie in sol_results:
        print(f"Partie {partie}: {plancher} -> {plafond} {pl_unite} (classe {classe})")

conn.close()