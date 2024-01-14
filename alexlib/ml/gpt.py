from dataclasses import dataclass, field
import logging as log

from pandas import DataFrame

from alexlib.core import chkenv
from alexlib.config import DotEnv
from alexlib.db import Table, Connection

if __name__ == "__main__":
    schema = "gpt"
    config = DotEnv()
    c = Connection.from_context("LOCAL")
    log.info(schema)


@dataclass
class Message:
    message_id: int
    message_seq: int
    role: str
    content: str
    spiciness: float
    is_input: bool
    is_return: bool

    @property
    def record(self) -> dict:
        return {x: getattr(self, x) for x in self.__dict__ if x[0] != "_"}

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


@dataclass
class Messages:
    lst: list[Message] = field(default_factory=list)
    context: str = "LOCAL"
    schema: str = "gpt"
    table: str = "messages"
    id_col: str = "message_id"

    @property
    def nmsgs(self) -> int:
        return len(self.lst)

    @property
    def rng(self) -> range:
        return range(self.nmsgs)

    def update_attr(self, attr: str, vals: list) -> None:
        [setattr(msg, attr, vals[i]) for i, msg in enumerate(self.lst)]

    def get_update_ids_vals(self, last_id: int) -> list[str]:
        return [i + last_id + 1 for i in range(len(self.lst))]

    def update_ids(self, last_id: int):
        ids = self.get_update_ids_vals(last_id)
        self.update_attr("message_id", ids)
        return self

    @property
    def record_list(self) -> list[dict]:
        return [x.record for x in self.lst]

    @property
    def df(self) -> DataFrame:
        return DataFrame.from_records([x.record for x in self.lst])

    @property
    def tbl(self) -> Table:
        return Table.from_db(self.context, self.schema, self.table)

    @classmethod
    def from_list(
        cls,
        lst: list[dict],
        is_input: bool = False,
        is_return: bool = False,
        spiciness: float = -1.0,
    ):
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
    ):
        lst = df.to_dict(orient="records")
        return cls.from_list(
            lst,
            is_input=is_input,
            is_return=is_return,
        )

    @classmethod
    def from_db(
        cls,
        context: str = "LOCAL",
        schema: str = "gpt",
        table: str = "messages",
    ):
        tbl = Table.from_db(context, schema, table)
        df = tbl.get_df()
        return cls.from_df(df)


@dataclass
class Completion:
    id: int
    obj: object
    temperature: float
    return_message: Message
    """
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
    """


@dataclass
class Experiment:
    id: int
    model: str = chkenv("OPENAI_MODEL")
    endpoint: str = chkenv("OPENAI_API_ENDPOINT")
    input_messages: list[Message] = field(default_factory=list)
    completions: list[Message] = field(default_factory=list)


if __name__ == "__main__":
    df = c.get_table("gpt", "messages")
    print(df)
