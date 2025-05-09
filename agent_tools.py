import glob
import pandas as pd
from typing import List, Dict
from io import StringIO
from smolagents import Tool, FinalAnswerTool as SmolFinalAnswerTool

class ListCSVFilesTool(Tool):
    name = "list_csv_files"
    description = "List all CSV files in the './dataset' directory."
    inputs = {}
    output_type = "array"

    def forward(self) -> List[str]:
        return glob.glob("./dataset/*.csv")

class DataframeOperationTool(Tool):
    name = "dataframe_operation"
    description = (
        "Perform various operations on a DataFrame. "
        "Supported operations: columns, head, groupby, describe, sample, info, shape, "
        "tail, nunique, value_counts, dtypes, isnull, notnull, sum, mean, median, min, max, std, var, corr."
    )
    inputs = {
        "operation": {
            "type": "string",
            "description": (
                "The operation to perform on the DataFrame. "
                "Supported: columns, head, tail, groupby, describe, sample, info, shape, nunique, value_counts, "
                "dtypes, isnull, notnull, sum, mean, median, min, max, std, var, corr."
            ),
        },
        "file_path": {"type": "string", "description": "The path to the CSV file."},
        "columns": {
            "type": "array",
            "description": "The columns to operate on (required for groupby and some stats).",
        },
    }
    output_type = "string"

    def forward(self, file_path: str, operation: str, columns) -> str:
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            op = operation.lower()
            if op == "columns":
                return ", ".join(df.columns)
            elif op == "head":
                return df.head().to_markdown(index=False)
            elif op == "tail":
                return df.tail().to_markdown(index=False)
            elif op == "groupby":
                if not columns:
                    return "Please specify columns for groupby."
                grouped_df = df.groupby(columns).size().reset_index(name="count")
                return grouped_df.to_markdown(index=False)
            elif op == "describe":
                return df.describe(include="all").to_markdown(index=False)
            elif op == "sample":
                n = min(10, len(df))
                return df.sample(n=n).to_markdown(index=False)
            elif op == "info":
                buf = StringIO()
                df.info(buf=buf)
                return buf.getvalue()
            elif op == "shape":
                return f"DataFrame shape: {df.shape}"
            elif op == "nunique":
                if columns:
                    return df[columns].nunique().to_markdown()
                return df.nunique().to_markdown()
            elif op == "value_counts":
                if not columns or len(columns) != 1:
                    return "Please specify a single column for value_counts."
                return df[columns[0]].value_counts().to_markdown()
            elif op == "dtypes":
                return df.dtypes.to_markdown()
            elif op == "isnull":
                return df.isnull().sum().to_markdown()
            elif op == "notnull":
                return df.notnull().sum().to_markdown()
            elif op in {"sum", "mean", "median", "min", "max", "std", "var"}:
                if columns:
                    result = getattr(df[columns], op)()
                else:
                    result = getattr(df, op)()
                return result.to_markdown()
            elif op == "corr":
                return df.corr(numeric_only=True).to_markdown()
            else:
                return f"Operation '{operation}' is not supported."
        except Exception as e:
            return f"Error performing operation: {e}"

class FilterDataFrameTool(Tool):
    name = "filter_dataframe"
    description = "Filter a DataFrame based on specific key-value pairs."
    inputs = {
        "file_path": {"type": "string", "description": "The path to the CSV file."},
        "filters": {
            "type": "object",
            "description": "A dictionary where keys are column names and values are lists of values to filter for.",
        },
    }
    output_type = "string"

    def forward(self, file_path: str, filters: Dict[str, List[str]]) -> str:
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            for column, values in filters.items():
                df = df[df[column].isin(values)]
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Error filtering DataFrame: {e}"

class FinalAnswerTool(SmolFinalAnswerTool):
    name = "final_answer"
    description = (
        "Return the final answer to the user's data analysis question in Markdown. "
        "Format the response clearly for data analysis, using bold for key findings, "
        "italic for important notes, and bullet points or tables for lists or summaries. "
        "Include concise explanations and highlight actionable insights if possible."
    )
    inputs = {
        "answer": {
            "type": "string",
            "description": (
                "A well-formatted data analysis answer in Markdown. Use bold for main results, "
                "italic for notes, bullet points for lists, and tables for tabular data. "
                "Summarize findings and provide clear, actionable insights."
            ),
        },
    }
    output_type = "string"

    def forward(self, answer: str) -> str:
        return answer
