"""
Find a way to install the package mining_IFOP first, with pip install .
Todo: need to finish the script from mining_IFOP/ifop_build.py
"""

from mining_IFOP import Miner, Builder

pdf_path = ...
score_number = ...
pages = ...
candidates_path = ...
output_path = ...
poll_type = "pt3"
population = "all"

miner = Miner()
# Traitement du PDF
miner = Miner()
miner.load_pdf(pdf_path, score_number, pages=pages)

results = miner.get_results()

builder = Builder(candidates_path, results)
builder.write(output_path, poll_type, population)
print(f"Résultats écrits dans {output_path}")
