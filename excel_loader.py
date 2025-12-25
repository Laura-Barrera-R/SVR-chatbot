import pandas as pd
from excel_queries import QUERY_FUNCTIONS

class ExcelAnalyzer:
    def __init__(self, path):
        self.df = pd.read_excel(path)

    def schema(self):
        return "\n".join(
            f"{c} | {self.df[c].dtype} | nulls={self.df[c].isna().sum()} | unique={self.df[c].nunique()}"
            for c in self.df.columns
        )

    def sample(self):
        return self.df.head(5).to_string()

    def run_query(self, query_name, **kwargs):
        # Ejecuta una consulta registrada en excel_queries.py
        if query_name not in QUERY_FUNCTIONS:
            raise ValueError(f"Consulta no soportada: {query_name}")
        return QUERY_FUNCTIONS[query_name](self.df, **kwargs)