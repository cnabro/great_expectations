import os
import time
from six import string_types

import pandas as pd

from .datasource import Datasource
from .filesystem_path_generator import SubdirPathGenerator
from .batch_generator import EmptyGenerator
from great_expectations.dataset.pandas_dataset import PandasDataset

from great_expectations.exceptions import BatchKwargsError


# class MemoryPandasDatasource(Datasource):
#     def __init__(self, name="default", data_context=None, generators=None):
#         if generators is None:
#             generators = {
#                 "default": {"type": "empty_generator"}
#             }
#         super(MemoryPandasDatasource, self).__init__(name, type_="memory_pandas",
#                                                      data_context=data_context,
#                                                      generators=generators)
#         self._build_generators()

#     def _get_generator_class(self, type_):
#         if type_ == "empty_generator":
#             return EmptyGenerator
#         else:
#             raise ValueError("Unrecognized BatchGenerator type %s" % type_)

#     def _get_data_asset(self, data_asset_name, batch_kwargs, expectations_config, **kwargs):
#         df = batch_kwargs.pop("df", None)
        
#         return PandasDataset(df,
#                              expectations_config=expectations_config,
#                              data_context=self._data_context,
#                              data_asset_name=data_asset_name,
#                              batch_kwargs=batch_kwargs)

#     def build_batch_kwargs(self, df, **kwargs):
#         return {
#             "df": df
#         }


class FilesystemPandasDatasource(Datasource):
    """
    A FilesystemPandasDatasource makes it easy to create, manage and validate expectations on
    Pandas dataframes.

    Use with the SubdirPathGenerator for simple cases.
    """

    def __init__(self, name="default", data_context=None, generators=None, **kwargs):
        if generators is None:
            # Provide a gentle way to build a datasource with a sane default,
            # including ability to specify the base_directory and reader_options
            base_directory = kwargs.pop("base_directory", "/data")
            reader_options = kwargs.pop("reader_options", {})
            generators = {
                "default": {
                    "type": "subdir_reader",
                    "base_directory": base_directory,
                    "reader_options": reader_options
                }
            }
        super(FilesystemPandasDatasource, self).__init__(name, type_="filesystem_pandas",
                                                         data_context=data_context,
                                                         generators=generators)
        self._build_generators()

    def _get_generator_class(self, type_):
        if type_ == "subdir_reader":
            return SubdirPathGenerator
        elif type_ == "memory":
            return EmptyGenerator
        else:
            raise ValueError("Unrecognized BatchGenerator type %s" % type_)

    def _get_data_asset(self, data_asset_name, batch_kwargs, expectations_config, **kwargs):
        batch_kwargs.update(kwargs)
        if "path" in batch_kwargs:
            path = batch_kwargs.pop("path") # We need to remove from the reader
            batch_kwargs.update(**kwargs)
            if path.endswith((".csv", ".tsv")):
                df = pd.read_csv(path, **batch_kwargs)
            elif path.endswith(".parquet"):
                df = pd.read_parquet(path, **batch_kwargs)
            elif path.endswith((".xls", ".xlsx")):
                df = pd.read_excel(path, **batch_kwargs)
            else:
                raise BatchKwargsError("Unrecognized path: no available reader.",
                                       batch_kwargs)
        elif "df" in batch_kwargs and isinstance(batch_kwargs["df"], (pd.DataFrame, pd.Series)):
            df = batch_kwargs.pop("df")  # We don't want to store the actual dataframe in kwargs
        else:
            raise BatchKwargsError("Invalid batch_kwargs: path or df is required for a PandasDatasource",
                                   batch_kwargs)

        return PandasDataset(df,
                             expectations_config=expectations_config,
                             data_context=self._data_context,
                             data_asset_name=data_asset_name,
                             batch_kwargs=batch_kwargs)

    def build_batch_kwargs(self, *args, **kwargs):
        if len(args) > 0:
            if isinstance(args[0], (pd.DataFrame, pd.Series)):
                kwargs.update({
                    "df": args[0],
                    "timestamp": time.time()
                })
            elif isinstance(args[0], string_types):
                kwargs.update({
                    "path": args[0],
                    "timestamp": time.time()
                })
        else:
            kwargs.update({
                "timestamp": time.time()
            })
        return kwargs
