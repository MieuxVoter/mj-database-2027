# coding: utf-8

import copy
import pathlib
import re
from typing import List, Tuple

from poll import CandidatePollInterface

# doc : https://pdfminersix.readthedocs.io/en/latest/reference/highlevel.html

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


class InconsistentScoreSum(ValueError):
    pass


class TextElement:
    def __init__(self, container: LTTextContainer):
        self.text = container.get_text().strip()
        self.x = container.x0
        self.y = container.y0


class Line(CandidatePollInterface):
    def __init__(self, name: str, y: float):
        name = name.strip()
        if not name:
            raise ValueError("Une ligne doit avoir un nom")

        self.name = name
        self.y = y
        self._scores: list[TextElement] = []

        self.favorable_score = None
        self.unfavorable_score = None

        self.scores: List[str] = None

    def get_name(self) -> str:
        return self.name

    def get_scores(self) -> List[str]:
        return self.scores

    def add_score(self, score: TextElement):
        score.text = score.text.replace("%", "").strip()
        self._scores.append(score)

    def check(self, score_number: int, totals: Tuple[str, str]):
        if not self._scores:
            raise ValueError("Une ligne doit avoir des scores")

        if not totals:
            raise ValueError("Totaux manquants pour la vérification")

        # On trie les scores par position horizontale (x)
        self._scores.sort(key=lambda s: s.x)

        last_score = self._scores[-1]

        # Si le dernier score est sur deux lignes => abstentions
        if last_score.text.count("\n") > 0:
            last_score_parts = last_score.text.strip().split("\n")

            if len(last_score_parts) > 2:
                raise ValueError(f"Les abstentions représentent au plus 2 catégories, found {len(last_score_parts)}")

            # On modifie le texte du dernier score pour ne garder que la première partie
            last_score.text = last_score_parts[0].strip()

            # On ajoute un nouveau score pour la deuxième partie
            new_score = copy.deepcopy(last_score)
            new_score.text = last_score_parts[1].strip()
            self._scores.append(new_score)

        self._check_totals(totals)

        # On complète si nécessaire
        actual_score_number = len(self._scores)
        if actual_score_number > score_number:
            raise ValueError(f"Le nombre de mentions pour {self.name} dépasse le nombre attendu ({score_number})")

        self.scores = [s.text for s in self._scores]

        if actual_score_number < score_number:
            missing_score_number = score_number - actual_score_number
            while missing_score_number:
                self.scores.append("0")
                missing_score_number -= 1

    def _check_totals(self, totals: Tuple[str, str]):
        """Vérifie les totaux d'opinions favorables et défavorables"""

        self.favorable_score = int(self._scores[0].text) + int(self._scores[1].text)
        self.unfavorable_score = int(self._scores[2].text) + int(self._scores[3].text)

        if len(totals) != 2:
            raise ValueError(f"Totaux invalides : {totals}")
        favorable = int(totals[0])
        unfavorable = int(totals[1])

        actual_favorable = self.favorable_score
        if favorable != actual_favorable:
            raise ValueError(
                f"Score d'opinion favorable incorrect pour {self.name} : attendu {favorable}, trouvé {actual_favorable}"
            )

        actual_unfavorable = self.unfavorable_score
        if unfavorable != actual_unfavorable:
            raise ValueError(
                f"Score d'opinion défavorable incorrect pour {self.name} : attendu {unfavorable}, trouvé {actual_unfavorable}"
            )

    def __str__(self):
        name = self.name
        return (
            f"{name} : {', '.join([s.text for s in self._scores])} => {self.favorable_score}, {self.unfavorable_score}"
        )


class PollPage:
    def __init__(self):
        self.lines = []
        self.names = []
        self.scores = []

        self.totals: List[TextElement] = []
        self.total_blocks: List[TextElement] = []

        self.favorable_totals = []
        self.unfavorable_totals = []

    def add_total_block(self, total_block: LTTextContainer):
        """Définit les totaux lorsqu'ils sont détectés en bloc"""
        self.total_blocks.append(TextElement(total_block))

    def add_total(self, total: LTTextContainer):
        self.totals.append(TextElement(total))

    def add_name(self, name: LTTextContainer):
        self.names.append(TextElement(name))

    def add_score(self, score: LTTextContainer):
        self.scores.append(TextElement(score))

    def organize(self, score_number: int):
        # Classer les noms et scores par position verticale (y0)
        self.names.sort(key=lambda n: n.y, reverse=True)
        self.scores.sort(key=lambda s: s.y, reverse=True)

        line_count = len(self.names)

        # Couples de totaux (favorable, défavorable)
        total_couples = self._organize_totals()

        # Pour chaque nom
        for i in range(line_count):
            name = self.names[i]
            line = Line(name.text, name.y)

            next_name = self.names[i + 1] if i + 1 < line_count else None

            # On cherche les scores positionnés sur la même ligne
            while True:
                if not self.scores:
                    break

                score = self.scores.pop(0)
                current_delta = abs(score.y - name.y)

                if next_name:
                    next_delta = abs(score.y - next_name.y)

                    # Si le score est plus proche de la ligne actuelle que de la suivante, on l'ajoute
                    if current_delta < next_delta:
                        line.add_score(score)
                    else:
                        # Sinon, on remet le score dans la liste et on arrête la recherche
                        self.scores.insert(0, score)
                        break
                else:
                    # Si c'est la dernière ligne, on ajoute le score
                    line.add_score(score)

            # Vérification des scores, des totaux
            line.check(score_number, total_couples[i])

            self.lines.append(line)

        # On classe les lignes par position verticale (y)
        self.lines.sort(key=lambda l: l.y, reverse=True)

    def _organize_totals(self) -> List[Tuple[str, str]]:
        """Organisation des totaux collectés. Renvoie un tuple de totaux (favorable, défavorable)"""
        results = []

        line_count = len(self.names)

        single_count = len(self.totals)
        block_count = len(self.total_blocks)

        if single_count > 0 and block_count > 0:
            raise ValueError("La prise en charge de totaux en blocs et individuels n'est pas encore assurée")

        # Les totaux sont groupés en un seul bloc ?
        if self.total_blocks:
            if block_count == 1 and self.total_blocks[0].text.count("\n") == line_count - 1:
                # Un seul bloc de totaux
                splitted_blocks = self.total_blocks[0].text.split("\n")
                for block in splitted_blocks:
                    total_parts = block.split("%")
                    results.append((total_parts[0].strip(), total_parts[1].strip()))

            elif block_count == line_count:  # Autant de blocs que de candidats (totaux groupés par 2)
                self.total_blocks.sort(key=lambda t: t.y, reverse=True)

                for total_block in self.total_blocks:
                    total_parts = total_block.text.split("%")
                    results.append(
                        (
                            total_parts[0].strip(),
                            total_parts[1].strip(),
                        )
                    )

            else:
                raise NotImplementedError("Plusieurs blocs de totaux non supportés pour l'instant")

        elif self.totals:  # Totaux individuels
            # On s'attend à avoir deux fois plus de totaux que de candidats.
            if single_count != line_count * 2:
                raise ValueError(f"{line_count} noms, mais {single_count} totaux trouvés")

            self.totals.sort(key=lambda t: t.y, reverse=True)
            while self.totals:
                first = self.totals.pop(0)
                first.text = first.text.replace("%", "").strip()
                second = self.totals.pop(0)
                second.text = second.text.replace("%", "").strip()

                if first.x < second.x:
                    results.append((first.text, second.text))
                else:
                    results.append((second.text, first.text))

        return results


class Miner:
    def __init__(self):
        self.pages: List[PollPage] = []

    def load_pdf(self, pdf_path: pathlib.Path, score_number: int, pages: List[int] = None):
        # Parfois les totaux sont groupés en un bloc
        # Note : on peut distinguer les totaux des scores car les totaux ont des espaces entre les pourcentages
        total_block_regex = re.compile(r"^\d{1,2} +% +\d{1,2} +% *$", re.MULTILINE)
        total_single_regex = re.compile(r"^\d{1,2} +% *$")

        score_regex = re.compile(r"^\d{1,2}%$", re.MULTILINE)
        name_regex = re.compile(r"^[A-Z][\w-]+\s[\w-]+\s{0,1}[\w-]+$")

        for page_layout in extract_pages(pdf_path, page_numbers=pages):
            poll_page = PollPage()
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()

                    if not text:
                        continue

                    # Bloc de totaux ?
                    if total_block_regex.match(text):
                        poll_page.add_total_block(element)
                        continue

                    # Total seul ?
                    if total_single_regex.match(text):
                        poll_page.add_total(element)
                        continue

                    if score_regex.findall(text):
                        # On sauve le score ainsi que ses coordonnées
                        poll_page.add_score(element)
                        continue

                    if name_regex.match(text):
                        # On sauve le nom ainsi que ses coordonnées
                        poll_page.add_name(element)
                        continue

            poll_page.organize(score_number)

            self.pages.append(poll_page)

    def get_results(self) -> List[CandidatePollInterface]:
        results = []
        for page in self.pages:
            for line in page.lines:
                results.append(line)
        return results
