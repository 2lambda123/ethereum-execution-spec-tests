"""
Useful types for generating Ethereum tests.
"""
import json
from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, Union

from .code import Code, code_to_hex
from .common import AddrAA, TestPrivateKey


def hex_or_none(input: Union[int, None], default=None) -> Union[str, None]:
    """
    Converts an int to hex or returns a default (None).
    """
    if input is None:
        return default
    return hex(input)


def str_or_none(input: Any, default=None) -> Union[str, None]:
    """
    Converts a value to string or returns a default (None).
    """
    if input is None:
        return default
    return str(input)


def int_or_none(input: Any, default=None) -> Union[int, None]:
    """
    Converts a value to int or returns a default (None).
    """
    if input is None:
        return default
    return int(input, 0)


class Storage:
    """
    Definition of a storage in pre or post state of a test
    """

    data: Dict[int, int]

    @staticmethod
    def parse_key_value(input: Union[str, int]) -> int:
        """
        Parses a key or value to a valid int key for storage.
        """
        if type(input) is str:
            if input.startswith("0x"):
                return int(input, 16)
            else:
                return int(input)
        elif type(input) is int:
            return input

        raise Exception("invalid type for key/value of storage")

    @staticmethod
    def key_value_to_string(value: int) -> str:
        """
        Transforms a key or value into a 32-byte hex string.
        """
        return "0x" + value.to_bytes(32, "big").hex()

    def __init__(self, input: Dict[Union[str, int], Union[str, int]]):
        """
        Initializes the storage using a given mapping which can have
        keys and values either as string or int.
        Strings must be valid decimal or hexadecimal (starting with 0x)
        numbers.
        """
        self.data = {}
        for k in input:
            v = Storage.parse_key_value(input[k])
            k = Storage.parse_key_value(k)
            self.data[k] = v
        pass

    def __len__(self) -> int:
        """Returns number of elements in the storage"""
        return len(self.data)

    def __contains__(self, key: Union[str, int]) -> bool:
        """Checks for an item in the storage"""
        key = Storage.parse_key_value(key)
        return key in self.data

    def __getitem__(self, key: Union[str, int]) -> int:
        """Returns an item from the storage"""
        key = Storage.parse_key_value(key)
        if key not in self.data:
            raise KeyError()
        return self.data[key]

    def __setitem__(
        self, key: Union[str, int], value: Union[str, int]  # noqa: SC200
    ):
        """Sets an item in the storage"""
        self.data[Storage.parse_key_value(key)] = Storage.parse_key_value(
            value
        )

    def __delitem__(self, key: Union[str, int]):
        """Deletes an item from the storage"""
        del self.data[Storage.parse_key_value(key)]

    def to_dict(self) -> Mapping[str, str]:
        """
        Converts the storage into a string dict with appropriate 32-byte
        hex string formatting.
        """
        res = {}
        for k in self.data:
            res[Storage.key_value_to_string(k)] = Storage.key_value_to_string(
                self.data[k]
            )
        return res

    def contains(self, other: "Storage") -> bool:
        """
        Returns True if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        """
        for k in other.data:
            if k not in self.data:
                return False
            if self.data[k] != other.data[k]:
                return False
        return True

    def must_contain(self, other: "Storage"):
        """
        Succeeds only if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        Raises detailed exception when a difference is found.
        """
        for k in other.data:
            if k not in self.data:
                raise Exception(
                    "key {0} not found in storage".format(
                        Storage.key_value_to_string(k)
                    )
                )
            if self.data[k] != other.data[k]:
                raise Exception(
                    "incorrect value for key {0}: {1}!={2}".format(
                        Storage.key_value_to_string(k),
                        Storage.key_value_to_string(self.data[k]),
                        Storage.key_value_to_string(other.data[k]),
                    )
                )


@dataclass(kw_only=True)
class Account:
    """
    State associated with an address.
    """

    nonce: Optional[int] = None
    balance: Optional[int] = None
    code: Optional[Union[bytes, str, Code]] = None
    storage: Optional[
        Union[Storage, Dict[Union[str, int], Union[str, int]]]
    ] = None

    def __post_init__(self) -> None:
        """Automatically init account members"""
        if self.storage is not None and type(self.storage) is dict:
            self.storage = Storage(self.storage)

    def check_alloc(self: "Account", account: str, alloc: dict):
        """
        Checks the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if self.nonce is not None:
            if "nonce" not in alloc:
                raise Exception(f"nonce not found for account {account}")
            nonce = int(alloc["nonce"], 16)
            if self.nonce != nonce:
                raise Exception(
                    f"unexpected nonce value found for account {account}: "
                    + f"{nonce}, expected {self.nonce}"
                )
        if self.balance is not None:
            if "balance" not in alloc:
                raise Exception(f"balance not found for account {account}")
            balance = int(alloc["balance"], 16)
            if self.balance != balance:
                raise Exception(
                    f"unexpected balance value found for account {account}: "
                    + f"{balance}, expected {self.balance}"
                )
        if self.code is not None:
            if "code" not in alloc:
                raise Exception(f"code not found for account {account}")
            expected_code = code_to_hex(self.code)
            if expected_code != alloc["code"]:
                actual_code = alloc["code"]
                raise Exception(
                    f"unexpected code found for account {account}: "
                    + f"{actual_code}, expected {expected_code}"
                )
        if self.storage is not None:
            if "storage" not in alloc:
                raise Exception(f"storage not found for account {account}")
            assert type(self.storage) is Storage
            Storage(alloc["storage"]).must_contain(self.storage)

    @classmethod
    def with_code(cls: Type, code: Union[bytes, str, Code]) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=1, code=code)


ACCOUNT_DEFAULTS = Account(nonce=0, balance=0, code=bytes(), storage={})


@dataclass(kw_only=True)
class Environment:
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    coinbase: str = "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"
    gas_limit: int = 100000000000000000
    number: int = 1
    timestamp: int = 1000
    difficulty: Optional[int] = None
    prev_randao: Optional[int] = None
    block_hashes: Dict[int, str] = field(default_factory=dict)
    base_fee: Optional[int] = None
    parent_difficulty: Optional[int] = None
    parent_timestamp: Optional[int] = None
    parent_base_fee: Optional[int] = None
    parent_gas_used: Optional[int] = None
    parent_gas_limit: Optional[int] = None
    parent_ommers_hash: Optional[str] = None

    @staticmethod
    def from_parent_header(parent: "FixtureHeader") -> "Environment":
        """
        Instantiates a new environment with the provided header as parent.
        """
        return Environment(
            parent_difficulty=parent.difficulty,
            parent_timestamp=parent.timestamp,
            parent_base_fee=parent.base_fee,
            parent_gas_used=parent.gas_used,
            parent_gas_limit=parent.gas_limit,
            parent_ommers_hash=parent.ommers_hash,
            block_hashes={
                parent.number: parent.hash
                if parent.hash is not None
                else "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            },
        )

    def parent_hash(self) -> str:
        """
        Obtjains the latest hash according to the highest block number in
        `block_hashes`.
        """
        if len(self.block_hashes) == 0:
            return "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        last_index = max(self.block_hashes.keys())
        return self.block_hashes[last_index]

    def apply_new_parent(self, new_parent: "FixtureHeader") -> "Environment":
        """
        Applies a header as parent to a copy of this environment.
        """
        new_environment = copy(self)
        new_environment.parent_difficulty = new_parent.difficulty
        new_environment.parent_timestamp = new_parent.timestamp
        new_environment.parent_base_fee = new_parent.base_fee
        new_environment.parent_gas_used = new_parent.gas_used
        new_environment.parent_gas_limit = new_parent.gas_limit
        new_environment.parent_ommers_hash = new_parent.ommers_hash
        new_environment.block_hashes[new_parent.number] = (
            new_parent.hash
            if new_parent.hash is not None
            else "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        )
        return new_environment


@dataclass(kw_only=True)
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

    ty: Optional[int] = None
    """
    Transaction type value.
    """
    chain_id: int = 1
    nonce: int = 0
    to: Optional[str] = AddrAA
    value: int = 0
    data: Union[bytes, str, Code] = bytes()
    gas_limit: int = 21000
    access_list: Optional[List[Tuple[str, List[str]]]] = None

    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None

    signature: Optional[Tuple[str, str, str]] = None
    secret_key: Optional[str] = None
    protected: bool = True
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Ensures the transaction has no conflicting properties.
        """
        if (
            self.gas_price is not None
            and self.max_fee_per_gas is not None
            and self.max_priority_fee_per_gas is not None
        ):
            raise Exception(
                "only one type of fee payment field can be used in a single tx"
            )

        if (
            self.gas_price is None
            and self.max_fee_per_gas is None
            and self.max_priority_fee_per_gas is None
        ):
            self.gas_price = 10

        if self.signature is not None and self.secret_key is not None:
            raise Exception("can't define both 'signature' and 'private_key'")

        if self.signature is None and self.secret_key is None:
            self.secret_key = TestPrivateKey

        if self.ty is None:
            # Try to deduce transaction type from included fields
            if self.max_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0


@dataclass(kw_only=True)
class Header:
    """
    Header type used to describe block header properties in test specs.
    """

    coinbase: Optional[str] = None
    parent_hash: Optional[str] = None
    ommers_hash: Optional[str] = None
    state_root: Optional[str] = None
    transactions_root: Optional[str] = None
    receipt_root: Optional[str] = None
    bloom: Optional[str] = None
    difficulty: Optional[int] = None
    number: Optional[int] = None
    gas_limit: Optional[int] = None
    gas_used: Optional[int] = None
    timestamp: Optional[int] = None
    extra_data: Optional[str] = None
    mix_digest: Optional[str] = None
    nonce: Optional[str] = None
    base_fee: Optional[int] = None
    hash: Optional[str] = None


@dataclass(kw_only=True)
class FixtureHeader:
    """
    Representation of an Ethereum header within a test Fixture.
    """

    coinbase: str
    parent_hash: str
    ommers_hash: str
    state_root: str
    transactions_root: str
    receipt_root: str
    bloom: str
    difficulty: int
    number: int
    gas_limit: int
    gas_used: int
    timestamp: int
    extra_data: str
    mix_digest: str
    nonce: str
    base_fee: Optional[int] = None
    hash: Optional[str] = None

    @staticmethod
    def from_dict(source: Dict[str, str]) -> "FixtureHeader":
        """
        Creates a FixedHeader object from a Dict.
        """
        ommers_hash = source.get("sha3Uncles")
        if ommers_hash is None:
            ommers_hash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"  # noqa: E501
        return FixtureHeader(
            parent_hash=source["parentHash"],
            ommers_hash=ommers_hash,
            coinbase=source["miner"],
            state_root=source["stateRoot"],
            transactions_root=source["transactionsRoot"],
            receipt_root=source["receiptsRoot"],
            bloom=source["logsBloom"],
            extra_data=source["extraData"],
            mix_digest=source["mixHash"],
            nonce=source["nonce"],
            hash=source.get("hash"),
            # Numbers
            difficulty=int(source["difficulty"], 0),
            number=int(source["number"], 0),
            gas_limit=int(source["gasLimit"], 0),
            gas_used=int(source["gasUsed"], 0),
            timestamp=int(source["timestamp"], 0),
            base_fee=int_or_none(source.get("baseFeePerGas")),
        )

    def to_geth_dict(self) -> Mapping[str, Any]:
        """
        Outputs a dict that can be marshalled to JSON and ingested by geth.
        """
        header = {
            "parentHash": self.parent_hash,
            "sha3Uncles": self.ommers_hash,
            "miner": self.coinbase,
            "stateRoot": self.state_root,
            "transactionsRoot": self.transactions_root,
            "receiptsRoot": self.receipt_root,
            "logsBloom": self.bloom,
            "difficulty": hex(self.difficulty),
            "number": hex(self.number),
            "gasLimit": hex(self.gas_limit),
            "gasUsed": hex(self.gas_used),
            "timestamp": hex(self.timestamp),
            "extraData": self.extra_data
            if len(self.extra_data) != 0
            else "0x",  # noqa: E501
            "mixHash": self.mix_digest,
            "nonce": self.nonce,
        }
        if self.base_fee is not None:
            header["baseFeePerGas"] = hex(self.base_fee)
        return header

    def join(self, modifier: Header) -> "FixtureHeader":
        """
        Produces a fixture header copy with the set values from the modifier.
        """
        new_fixture_header = copy(self)
        for header_field in self.__dataclass_fields__:
            value = getattr(modifier, header_field)
            if value is not None:
                setattr(new_fixture_header, header_field, value)
        return new_fixture_header


@dataclass(kw_only=True)
class Block(Header):
    """
    Block type used to describe block properties in test specs
    """

    rlp: Optional[str] = None
    """
    If set, blockchain test will skip generating the block using
    `evm_block_builder`, and will pass this value directly to the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    rlp_modifier: Optional[Header] = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the  `evm_transition_tool`.
    """
    exception: Optional[str] = None
    """
    If set, the block is expected to be rejected by the client.
    """
    txs: Optional[List[Transaction]] = None
    """
    List of transactions included in the block.
    """
    ommers: Optional[List[Header]] = None
    """
    List of ommer headers included in the block.
    """

    def set_environment(self, env: Environment) -> Environment:
        """
        Creates a copy of the environment with the characteristics of this
        specific block.
        """
        new_env = copy(env)

        """
        Values that need to be set in the environment and are `None` for
        this block need to be set to their defaults.
        """
        environment_default = Environment()
        new_env.difficulty = self.difficulty
        new_env.coinbase = (
            self.coinbase
            if self.coinbase is not None
            else environment_default.coinbase
        )
        new_env.gas_limit = (
            self.gas_limit
            if self.gas_limit is not None
            else environment_default.gas_limit
        )
        new_env.base_fee = self.base_fee

        """
        These values are required, but they depend on the previous environment,
        so they can be calculated here.
        """
        if self.number is not None:
            new_env.number = self.number
        else:
            # calculate the next block number for the environment
            if len(new_env.block_hashes) == 0:
                new_env.number = 0
            else:
                new_env.number = max(new_env.block_hashes.keys()) + 1

        if self.timestamp is not None:
            new_env.timestamp = self.timestamp
        else:
            assert new_env.parent_timestamp is not None
            new_env.timestamp = new_env.parent_timestamp + 12

        return new_env

    def copy_with_rlp(self, rlp) -> "Block":
        """
        Creates a copy of the block and adds the specified RLP.
        """
        new_block = deepcopy(self)
        new_block.rlp = rlp
        return new_block


@dataclass(kw_only=True)
class FixtureBlock:
    """
    Representation of an Ethereum block within a test Fixture.
    """

    rlp: str
    block_header: Optional[FixtureHeader] = None
    expected_exception: Optional[str] = None


@dataclass(kw_only=True)
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[FixtureBlock]
    genesis: FixtureHeader
    head: str
    fork: str
    pre_state: Mapping[str, Account]
    post_state: Optional[Mapping[str, Account]]
    seal_engine: str


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for `ethereum_test` types.
    """

    def default(self, obj):
        """
        Enocdes types defined in this module using basic python facilities.
        """
        if isinstance(obj, Storage):
            return obj.to_dict()
        elif isinstance(obj, Account):
            account = {
                "nonce": hex_or_none(obj.nonce, hex(ACCOUNT_DEFAULTS.nonce)),
                "balance": hex_or_none(
                    obj.balance, hex(ACCOUNT_DEFAULTS.balance)
                ),
                "code": code_to_hex(obj.code),
                "storage": json.loads(json.dumps(obj.storage, cls=JSONEncoder))
                if obj.storage is not None
                else {},
            }
            return account
        elif isinstance(obj, Transaction):
            tx = {
                "type": hex(obj.ty),
                "chainId": hex(obj.chain_id),
                "nonce": hex(obj.nonce),
                "gasPrice": hex_or_none(obj.gas_price),
                "maxPriorityFeePerGas": hex_or_none(
                    obj.max_priority_fee_per_gas
                ),
                "maxFeePerGas": hex_or_none(obj.max_fee_per_gas),
                "gas": hex(obj.gas_limit),
                "value": hex(obj.value),
                "input": code_to_hex(obj.data),
                "to": obj.to,
                "accessList": obj.access_list,
                "protected": obj.protected,
                "secretKey": obj.secret_key,
            }

            if obj.signature is None:
                tx["v"] = hex(0x0)
                tx["r"] = hex(0x0)
                tx["s"] = hex(0x0)
            else:
                tx["v"] = obj.signature[0]
                tx["r"] = obj.signature[1]
                tx["s"] = obj.signature[2]

            return {k: v for (k, v) in tx.items() if v is not None}
        elif isinstance(obj, Environment):
            env = {
                "currentCoinbase": obj.coinbase,
                "currentGasLimit": str_or_none(obj.gas_limit),
                "currentNumber": str_or_none(obj.number),
                "currentTimestamp": str_or_none(obj.timestamp),
                "currentRandom": str_or_none(obj.prev_randao),
                "currentDifficulty": str_or_none(obj.difficulty),
                "parentDifficulty": str_or_none(obj.parent_difficulty),
                "parentBaseFee": str_or_none(obj.parent_base_fee),
                "parentGasUsed": str_or_none(obj.parent_gas_used),
                "parentGasLimit": str_or_none(obj.parent_gas_limit),
                "parentTimstamp": str_or_none(obj.parent_timestamp),
                "blockHashes": {
                    str(k): v for (k, v) in obj.block_hashes.items()
                },
                "ommers": [],
                "parentUncleHash": obj.parent_ommers_hash,
                "currentBaseFee": str_or_none(obj.base_fee),
            }

            return {k: v for (k, v) in env.items() if v is not None}
        elif isinstance(obj, FixtureHeader):
            header = {
                "parentHash": obj.parent_hash,
                "uncleHash": obj.ommers_hash,
                "coinbase": obj.coinbase,
                "stateRoot": obj.state_root,
                "transactionsTrie": obj.transactions_root,
                "receiptTrie": obj.receipt_root,
                "bloom": obj.bloom,
                "difficulty": hex(obj.difficulty),
                "number": hex(obj.number),
                "gasLimit": hex(obj.gas_limit),
                "gasUsed": hex(obj.gas_used),
                "timestamp": hex(obj.timestamp),
                "extraData": obj.extra_data
                if len(obj.extra_data) != 0
                else "0x",  # noqa: E501
                "mixHash": obj.mix_digest,
                "nonce": obj.nonce,
            }
            if obj.base_fee is not None:
                header["baseFeePerGas"] = hex(obj.base_fee)
            if obj.hash is not None:
                header["hash"] = obj.hash
            return header
        elif isinstance(obj, FixtureBlock):
            b = {
                "rlp": obj.rlp,
            }
            if obj.block_header is not None:
                b["blockHeader"] = json.loads(
                    json.dumps(obj.block_header, cls=JSONEncoder)
                )
            return b
        elif isinstance(obj, Fixture):
            f = {
                "_info": {},
                "blocks": [
                    json.loads(json.dumps(b, cls=JSONEncoder))
                    for b in obj.blocks
                ],
                "genesisBlockHeader": self.default(obj.genesis),
                "lastblockhash": obj.head,
                "network": obj.fork,
                "pre": json.loads(json.dumps(obj.pre_state, cls=JSONEncoder)),
                "postState": json.loads(
                    json.dumps(obj.post_state, cls=JSONEncoder)
                ),
                "sealEngine": obj.seal_engine,
            }
            if f["postState"] is None:
                del f["postState"]
            return f
        else:
            return super().default(obj)
