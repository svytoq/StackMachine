import json
from enum import Enum

class OpcodeParamType(str, Enum):
    CONST = "const"
    ADDR = "addr"
    UNDEFINED = "undefined"
    ADDR_REL = "addr_rel"


class OpcodeParam:
    def __init__(self, param_type: OpcodeParamType, value: any):
        self.param_type = param_type
        self.value = value

    def __str__(self):
        return f"({self.param_type}, {self.value})"

class OpcodeType(str, Enum):
    
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    EQ = "eq"
    MORE = "more"
    LESS = "less"
    DROP = "drop"
    SWAP = "swap"
    OVER = "over"
    DUP = "dup"
    EMIT = "emit"
    READ = "read"
    EI = "ei"
    DI = "di"

    LD = "ld"
    ST = "st"
    JMP = "jmp" 
    RPOP = "rpop"  # move from return stack to data stack
    POP = "pop"  # move from data stack to return stack
    JZ = "jz" 
    CALL = "call" 
    RET = "ret"
    PUSH = "push"
    HLT = "hlt"

    def __str__(self):
        return str(self.value)

class Opcode:
    def __init__(self, opcode_type: OpcodeType, params: list[OpcodeParam]):
        self.opcode_type = opcode_type
        self.params = params

class TermType(Enum):
    (
        ADD,
        SUB,
        MUL,
        DIV,
        MOD,
        EQ,
        MORE,
        LESS,
        DROP,
        SWAP,
        OVER,
        DUP,
        EMIT,
        READ,
        EI,
        DI,
        ST,
        LD,

        VARIABLE,
        ALLOT,
        IF,
        ELSE,
        THEN,
        DEF,
        RET,
        DO,
        LOOP,
        BEGIN,
        UNTIL,
        CALL,
        LOOP_I,
        DEF_INTR,
        STRING,
        ENTRYPOINT
        
    ) = range(34)

def writeCode(filename: str, code: list[dict]):
    
    with open(filename, "w", encoding="utf-8") as file:
        
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(source_path: str) -> list:
    with open(source_path, encoding="utf-8") as file:
        return json.loads(file.read())