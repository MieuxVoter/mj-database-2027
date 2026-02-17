import re
from enum import Enum
from core.utils.helpers import normalize


class Population(str, Enum):
    """
    Enum représentant les populations/candidats et les enquêtes auxquelles ils appartiennent.
    """

    ALL = "all"
    LEFT = "left"
    MACRON = "macron"
    FARRIGHT = "farright"
    ABSTENTIONISTS = "absentionists"
    JLMELENCHON = "melenchon"
    MLPEN = "lepen"
    LFI = "lfi"
    ECOLOGISTES = "ecologistes"
    PSPP = "pspp"
    RENAISSANCE = "renaissance"
    LR = "lr"
    RN = "rn"
    RECONQUETE = "reconquete"

    # Définition des enquêtes par population/candidats
    __SURVEY_MAP__ = {
        "CLUSTER17": [
            "all",
            "macron",
            "lepen",
            "melenchon",
            "lfi",
            "ecologistes",
            "pspp",
            "renaissance",
            "lr",
            "rn",
            "reconquete",
        ],
        "ELABE": ["all", "macron", "left", "farright", "absentionists"],
    }

    def __str__(self):
        return self.value

    @property
    def label(self) -> str:
        """Étiquette lisible"""
        LABELS = {
            "all": "Ensemble des Français",
            "left": "Électeurs de gauche",
            "macron": "Électeurs d'Emmanuel Macron",
            "farright": "Électeurs d'extrême droite",
            "absentionists": "Abstentionnistes",
            "lepen": "Électeurs de Marine Le Pen 2022",
            "melenchon": "Électeurs de Jean-Luc Mélenchon 2022",
            "lfi": "Électeurs de LFI aux Européennes 2024",
            "ecologistes": "Électeurs Les Ecologistes aux Européennes 2024",
            "pspp": "Électeurs PS/PP aux Européennes 2024",
            "renaissance": "Électeurs Renaissance aux Européennes 2024",
            "lr": "Électeurs LR aux Européennes 2024",
            "rn": "Électeurs RN aux Européennes 2024",
            "reconquete": "Électeurs Reconquête aux Européennes 2024",
        }
        return LABELS[self.value]

    @classmethod
    def by_survey(cls, survey_name: str) -> list["Population"]:
        """Retourne les populations appartenant à une enquête donnée (ex: 'CLUSTER17')."""
        populations = cls.__SURVEY_MAP__.get(survey_name.upper(), [])
        return [p for p in cls if p.value in populations]

    @classmethod
    def surveys_for(cls, population: "Population") -> list[str]:
        """Retourne les enquêtes dans lesquelles une population est présente."""
        return [name for name, pops in cls.__SURVEY_MAP__.items() if population.value in pops]

    @classmethod
    def detect_from_text(cls, text: str) -> tuple["Population", str] | None:
        """Détecte la population correspondant à un texte normalisé."""

        text = normalize(text)

        # Mots-clés (patterns de détection en version minimale, aplatie et sans accents.)
        KEYWORDS = {
            cls.ALL: [
                "ensemble des francais",
                "tous les francais",
                "l'ensemble des francais",
                (
                    "concernant les personnalites politiques suivantes, pouvez "
                    "vous nous dire pour chacune d'entre elle si vous la soutenez, "
                    "si vous l'appreciez, si vous ne l'appreciez pas, si vous ne la "
                    "connaissez pas ou si vous n'avez pas d'avis sur elle ?"
                ),
            ],
            cls.LEFT: ["electeurs de gauche", "sympathisants de gauche", "electeurs de gauche et des ecologistes"],
            cls.MACRON: [
                "electeurs d'emmanuel macron",
                "electeurs de macron",
                "macronistes",
                "electeurs emmanuel macron 2022",
            ],
            cls.FARRIGHT: ["electeurs de marine le pen et d'eric zemmour", "electeurs d'extreme droite"],
            cls.ABSTENTIONISTS: ["abstentionnistes", "votes blancs et nuls", "non inscrits", "non-inscrits"],
            cls.JLMELENCHON: [
                "jean-luc melenchon",
                "melenchon 2022",
                "electeurs de jean-luc melenchon 2022",
            ],
            cls.MLPEN: [
                "marine le pen",
                "marine le pen 2022",
                "electeurs marine le pen 2022",
            ],
            cls.LFI: ["electeurs lfi", "electeurs lfi europeennes 2024", "electeurs lfi europeennes aux 2024"],
            cls.ECOLOGISTES: [
                "electeurs ecologistes",
                "les ecologistes europeennes",
                "electeurs les ecologistes europeennes 2024",
                "electeurs les ecologistes aux europeennes 2024",
            ],
            cls.PSPP: [
                "electeurs ps/pp aux europeennes 2024",
                "electeurs ps/pp europeennes 2024",
                "ps/pp aux europeennes 2024",
                "ps/pp",
            ],
            cls.RENAISSANCE: [
                "electeurs renaissance aux europeennes 2024",
                "electeurs renaissance",
                "renaissance europeennes 2024",
            ],
            cls.LR: ["electeurs lr aux europeennes 2024", "electeurs lr", "les lr", "lr europeennes 2024"],
            cls.RN: [
                "electeurs rn aux europeennes 2024",
                "electeurs rn",
                "les rn",
                "rassemblement national europeennes 2024",
                "rn europeennes 2024",
                "rassemblement national",
                "electeurs de rassemblement national",
            ],
            cls.RECONQUETE: [
                "electeurs reconquete aux europeennes 2024",
                "electeurs reconquete",
                "reconquete europeennes 2024",
            ],
        }

        for pop, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw.replace(" ", "") in text.replace(" ", ""):
                    pattern = re.sub(r"\s+", r"\\s*", kw)
                    if re.search(pattern, text):
                        return pop, pop.label

        return None
