import abc
import os
import json


class GenericStaticABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def extract(self, kwargs):
        raise NotImplementedError

    def parser(self, **kwargs):
        if "input_value" not in kwargs:
            raise Exception("kwargs must have input_value key")
        input_value = kwargs.get("input_value")
        filters = kwargs.get("filters")
        input_value_imported = self.get_if_input_is_file_or_str(input_value)
        return_value = self.extract(
            **{
                "input_file": input_value_imported,
                "filters": filters,
            }
        )
        return self.validate_return_type(return_value)

    def get_if_input_is_file_or_str(self, input_value):
        if isinstance(input_value, list) or isinstance(input_value, dict):
            return input_value
        if type(input_value) is str and os.path.isfile(input_value):
            path = os.path.abspath(input_value)
            with open(path, "r") as file:
                load = json.load(file)
                if isinstance(load, list) or isinstance(load, dict):
                    return_value = []
                    for keys in load:
                        if type(load.get(keys, {})) == list:
                            return_value.extend(load.get(keys, []))
                        else:
                            return_value.append(load.get(keys, {}))
                return return_value
        else:
            return input_value

    def validate_return_type(self, return_value):
        if not isinstance(return_value, dict):
            raise Exception("Return from parser type must be a list")
        if return_value.get("file_paths") is None:
            raise Exception("Return from parser must have file_paths key")
        if return_value.get("metrics") is None:
            raise Exception("Return from parser must have metrics key")
        if return_value.get("values") is None:
            raise Exception("Return from parser must have values key")

        return return_value
