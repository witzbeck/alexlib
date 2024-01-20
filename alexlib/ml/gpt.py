"""GPT classes"""
from dataclasses import dataclass, field

# from openai import OpenAI
from pandas import DataFrame

from alexlib.core import chkenv
from alexlib.db import Connection, Table


@dataclass
class Message:
    """A message"""

    message_id: int
    message_seq: int
    role: str
    content: str
    spiciness: float
    is_input: bool
    is_return: bool

    @property
    def record(self) -> dict:
        """Returns a dict of the message"""
        return {x: getattr(self, x) for x in self.__dict__ if x[0] != "_"}

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        """Creates a Message from a dict"""
        return cls(**d)


@dataclass
class Messages:
    """A list of messages"""

    lst: list[Message] = field(default_factory=list)
    context: str = "LOCAL"
    schema: str = "gpt"
    table: str = "messages"
    id_col: str = "message_id"

    @property
    def nmsgs(self) -> int:
        """Returns the number of messages"""
        return len(self.lst)

    @property
    def rng(self) -> range:
        """Returns a range of message ids"""
        return range(self.nmsgs)

    def update_attr(self, attr: str, vals: list) -> None:
        """Updates an attribute of the messages"""
        return [setattr(msg, attr, vals[i]) for i, msg in enumerate(self.lst)]

    def get_update_ids_vals(self, last_id: int) -> list[str]:
        """Returns a list of message ids"""
        return [i + last_id + 1 for i in range(len(self.lst))]

    def update_ids(self, last_id: int) -> "Messages":
        """Updates the message ids"""
        ids = self.get_update_ids_vals(last_id)
        self.update_attr("message_id", ids)
        return self

    @property
    def record_list(self) -> list[dict]:
        """Returns a list of dicts of the messages"""
        return [x.record for x in self.lst]

    @property
    def df(self) -> DataFrame:
        """Returns a DataFrame of the messages"""
        return DataFrame.from_records([x.record for x in self.lst])

    @property
    def tbl(self) -> Table:
        """Returns the table object"""
        return Table.from_db(self.context, self.schema, self.table)

    @classmethod
    def from_list(
        cls,
        lst: list[dict],
        is_input: bool = False,
        is_return: bool = False,
        spiciness: float = -1.0,
    ) -> "Messages":
        """Creates a Messages object from a list of dicts"""

        def msg_from_dict(d: dict, i: int):
            d["message_id"] = 0
            d["message_seq"] = i
            d["spiciness"] = spiciness
            d["is_input"] = is_input
            d["is_return"] = is_return
            msg = Message.from_dict(d)
            return msg

        rng = range(len(lst))
        msgs = [msg_from_dict(lst[i], i) for i in rng]
        return cls(lst=msgs)

    @classmethod
    def from_df(
        cls,
        df: DataFrame,
        is_input: bool = False,
        is_return: bool = False,
    ) -> "Messages":
        """Creates a Messages object from a DataFrame"""
        lst = df.to_dict(orient="records")
        return cls.from_list(
            lst,
            is_input=is_input,
            is_return=is_return,
        )

    @classmethod
    def from_db(
        cls,
        cnxn: Connection,
        schema: str = "gpt",
        table: str = "messages",
    ) -> "Messages":
        """Creates a Messages object from a database table"""
        tbl = Table.from_db(cnxn, schema, table)
        return cls.from_df(tbl.df)


@dataclass
class Completion:
    """A completion"""

    id: int
    obj: object
    temperature: float
    return_message: Message
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop: list[str]
    best_of: int
    n: int
    logprobs: int
    echo: bool
    stream: bool
    logit_bias: dict[str, float]
    return_prompt: bool
    return_metadata: bool
    return_sequences: bool
    return_logprobs: bool
    return_tokens: bool
    return_full_text: bool
    prompt: str
    engine: str
    max_rerank: int
    n_best_size: int


@dataclass
class Experiment:
    """An experiment""" ""

    id: int
    model: str = chkenv("OPENAI_MODEL")
    endpoint: str = chkenv("OPENAI_API_ENDPOINT")
    input_messages: list[Message] = field(default_factory=list)
    completions: list[Message] = field(default_factory=list)
