import importlib
import math
import pandas as pd
from genericparser.accept_plugins import ACCEPT_PLUGINS
from src.cli.commands.aaaaaa.github import ParserGithub


class GenericParser:
    file_path_configuration = ACCEPT_PLUGINS
    df = None

    def __init__(self, file_path_configuration=None):
        self.file_path = file_path_configuration or self.file_path_configuration

    def parse(self, **kwargs):
        input_value = kwargs.get("input_value")
        type_input = kwargs.get("type_input")
        filters = kwargs.get("filters")
        accepted_types = self.get_accepted_types()
        if type_input not in accepted_types:
            raise Exception("Type not accepted by parser")

        path_plugin = self.get_path_plugin(type_input)
        return_from_plugin = self.call_plugin(path_plugin, input_value, filters)

        if isinstance(return_from_plugin, pd.DataFrame):
            self.df = return_from_plugin
        else:
            self.df = self.get_df_from_parser(return_from_plugin)

        print(self.df)

        return self.transform_df_to_python_dict(self.df)

    def get_df_from_parser(self, dict_input: dict):
        df = pd.DataFrame(dict_input)
        df_pivot = df.pivot(index="metrics", columns="file_paths", values="values")
        return df_pivot

    def get_accepted_types(self):
        return ACCEPT_PLUGINS.keys()

    def get_path_plugin(self, type_input):
        return ACCEPT_PLUGINS.get(type_input)

    def call_plugin(self, path_plugin, file_input, filters):
        # plugin = importlib.import_module(path_plugin)
        object = ParserGithub()
        return object.parser(**{"input_value": file_input, "filters": filters})

    def transform_df_to_python_dict(self, pandas_dataframe: pd.DataFrame):
        returned_dict = {}
        pandas_dataframe.replace(math.nan, None, inplace=True)
        for column in pandas_dataframe.columns:
            returned_dict[column] = []
            for index, value in pandas_dataframe[column].items():
                (
                    returned_dict[column].append({"metric": index, "value": value})
                    if value is not None
                    else None
                )
        return returned_dict
