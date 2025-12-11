import logging
import pandas as pd
from core.settings.logger import setup_logging

setup_logging()
logger = logging.getLogger("app")


class Cluster17AnomalyDetector:

    def __init(self, df: pd.DataFrame) -> None:

        if not isinstance(df, pd.DataFrame):
            logger.error("Le paramètre 'df' doit être un objet pandas.DataFrame")
            raise TypeError("Le paramètre 'df' doit être un objet pandas.DataFrame")
        if df.empty:
            logger.error("Le paramètre 'df' doit être un objet pandas.DataFrame")
            raise TypeError("Le paramètre 'df' doit être un objet pandas.DataFrame")

        self.df: pd.DataFrame = df.copy()
