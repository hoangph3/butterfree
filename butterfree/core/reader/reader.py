"""Reader entity."""

from abc import ABC, abstractmethod
from functools import reduce


class Reader(ABC):
    """Abstract base class for Readers."""

    def __init__(self, id):
        """Instantiate Reader with the required parameters.

        :param id: unique string id for register the reader as a view on the metastore
        :param client: client object from butterfree.core.client module
        :param transformations: list os methods that will be applied over the dataframe
        after the raw data is extracted
        """
        self.id = id
        self.transformations = []

    def with_(self, transformer, *args, **kwargs):
        """Define a new transformation for the Reader.

        All the transformations are used when the method consume is called.
        :param transformer: method that receives a Spark dataframe and output a
        Spark dataframe
        :param args: args for the method
        :param kwargs: kwargs for the method
        :return: new Reader object with new parameters
        """
        new_transformation = {
            "transformer": transformer,
            "args": args if args else (),
            "kwargs": kwargs if kwargs else {},
        }
        self.transformations.append(new_transformation)
        return self

    def _apply_transformations(self, df):
        """Apply all the transformations defined over a passed Spark dataframe.

        :param df: Spark dataframe to be pre-processed
        :return: Spark dataframe
        """
        return reduce(
            lambda result_df, transformation: transformation["transformer"](
                result_df, *transformation["args"], **transformation["kwargs"]
            ),
            self.transformations,
            df,
        )

    @abstractmethod
    def consume(self, client):
        """Extract data from reader using the consume_options defined in the build.

        :return: Spark dataframe
        """

    def build(self, client):
        """Register the reader in the Spark metastore.

        Create a temporary view in Spark metastore referencing the data extracted from
        the defined Reader, using the consume method
        :return: None
        """
        self._apply_transformations(self.consume(client)).createOrReplaceTempView(
            self.id
        )
