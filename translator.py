import sys
import shlex
from isa import Opcode, OpcodeParam, OpcodeParamType, OpcodeType, TermType, writeCode



class Term:
    def __init__(self, word_number: int, term_type: TermType | None, word: str):
        self.converted = False
        self.operand = None
        self.word_number = word_number
        self.term_type = term_type
        self.word = word

variables = {}
functions = {}
variable_current_address = 1024
string_current_address = 0

def symbols():
    return {"di", "ei", "dup", "+", "-", "*", "/", "mod", "emit", "read", "swap", "drop", "over", "=", ">", "<", "variable", "allot", 
            "!", "@", "if", "else", "then", ".", ":", ";", ":intr", "do", "loop", "begin", "until", "i"}


def word2terms(word: str) -> Term | None:
    return {
        "di": TermType.DI,
        "ei": TermType.EI,
        "dup": TermType.DUP,
        "+": TermType.ADD,
        "-": TermType.SUB,
        "*": TermType.MUL,
        "/": TermType.DIV,
        "mod": TermType.MOD,
        "emit": TermType.EMIT,
        "read": TermType.READ,
        "swap": TermType.SWAP,
        "drop": TermType.DROP,
        "over": TermType.OVER,
        "=": TermType.EQ,
        "<": TermType.LESS,
        ">": TermType.MORE,
        "variable": TermType.VARIABLE,
        "allot": TermType.ALLOT,
        "!": TermType.ST,
        "@": TermType.LD,
        "if": TermType.IF,
        "else": TermType.ELSE,
        "then": TermType.THEN,
        ".": TermType.EMIT,
        ":": TermType.DEF,
        ";": TermType.RET,
        ":intr": TermType.DEF_INTR,
        "do": TermType.DO,
        "loop": TermType.LOOP,
        "begin": TermType.BEGIN,
        "until": TermType.UNTIL,
        "i": TermType.LOOP_I,
    }.get(word)


def text2terms(text: str) -> list[Term]:

    text = text.replace("\n", " ")
    text = enumerate(shlex.split(text, posix=True), 1)
    
    terms = [Term(0, TermType.ENTRYPOINT, "")]

    for i, word in text:
        termType = word2terms(word)
        if word[:2] == ". ":
            word = f'."{word[2:]}"'
            termType = TermType.STRING
        terms.append(Term(i, termType, word))  
    return terms

def validateTerms(terms: list[Term]) -> list[Term] :
    terms = checkIfOperator(terms)
    terms = checkDoOperator(terms)
    terms = checkBeginOperator(terms)
    terms = checkFunktionOperator(terms)
    terms = checkVariableOperator(terms)
    terms = checkVarAndFunkCall(terms)

    for term in terms:
        print(term.word_number, term.term_type, term.word)
    print(variables)
    print(functions)
    return terms


def checkIfOperator(terms: list[Term])-> list[Term] :
    ifs = []
    for term in terms:
        if term.word == "if":
            ifs.append(term)
        if term.word == "else":
            ifs.append(term)
        if term.word == "then":    
            assert len(ifs) > 0, "the appearance of the THEN operator before IF in " +str(term.word_number)
            last_if = ifs.pop()
            if last_if.word == "else":
                last_else = last_if
                assert len(ifs) > 0, "the appearance of the ELSE operator before IF in " +str(term.word_number)
                last_if = ifs.pop()
                last_else.operand = term.word_number + 1
                last_if.operand = last_else.word_number + 1
            else:
                last_if.operand = term.word_number + 1
        
    assert len(ifs) == 0, "there is no corresponding operator for " + str(ifs[0].term_type) + " at " + str(ifs[0].word_number)
    
    return terms

def checkDoOperator(terms: list[Term]) -> list[Term] :
    deep = 0
    do = []
    for term in terms:
        if term.word == "do":
            deep += 1
            do.append(term.word_number)
        if term.word == "loop":
            deep -= 1
            assert deep >= 0, "There is no corresponding DO operator for the LOOP operator at" + str(term.word_number)
            term.operand = do.pop()
    assert deep == 0, "there is no corresponding operator for " + str(do[0].term_type) + " at " + str(do[0].word_number)
    
    return terms

def checkBeginOperator(terms: list[Term])-> list[Term] :
    deep = 0
    begin = []
    for term in terms:
        if term.word == "begin":
            deep += 1
            begin.append(term.word_number)
        if term.word == "until":
            deep -= 1
            assert deep >= 0, "There is no corresponding BEGIN operator for the UNTIL operator at" + str(term.word_number)
            term.operand = begin.pop()

    assert deep == 0, "there is no corresponding operator for " + str(begin[0].term_type) + " at " + str(begin[0].word_number)
    
    return terms

def checkFunktionOperator(terms: list[Term]) -> list[Term] :
    deep = 0 
    flag = False
    functions_indexes = []
    for term in terms:
        if flag :
            assert term.word not in functions or not term.term_type is None, "exception funktion operator"
            flag = False
            functions[term.word] = term.word_number + 1
            term.converted = True
        if term.word == ":":
            assert term.word_number + 1 < len(terms), "Missed function name" + str(term.word_number)
            assert len(functions_indexes) == 0, "Unclosed function at " + str(term.word_number)
            assert term.word not in functions, "Duplicate function-name at " + str(term.word_number)
            deep += 1
            flag = True
            functions_indexes.append(term.word_number)
        if term.word == ";":
            assert len(functions_indexes) >=1, "RET out of function at word #" + str(term.word_number)
            deep -= 1
            termBack = terms[functions_indexes.pop()]
            termBack.operand = term.word_number + 1
        assert deep >= 0, "exception funktion operator"
    assert deep == 0, "Unclosed function at " + str(functions_indexes[0])
    
    return terms

def checkVariableOperator(terms: list[Term]) -> list[Term] :
    global variable_current_address
    flag = False
    for term in terms:
        if flag:
            assert term.term_type is None, "exception variable operator"
            assert term.word[0].isalpha(), "exception variable operator"
            assert term.word not in variables, "exception variable operator"
            flag = False
            variables[term.word] = variable_current_address
            variable_current_address += 1
            term.converted = True
            if term.word_number + 2 < len(terms) and terms[term.word_number + 2].term_type is TermType.ALLOT:
                terms[term.word_number + 1].converted = True
                size = int(terms[term.word_number + 1].word)
                if (size > 1 and size < 100):
                    variable_current_address += size
                else:
                    assert True, "Incorrect size"
        if term.word == "variable":
            assert term.word_number + 1 < len(terms), "missed variable name at " + str(term.word_number)
            flag = True

    return terms

        

def checkVarAndFunkCall(terms: list[Term]) -> list[Term] :
    for term in terms:
        if term.term_type is None and not term.converted:
            if term.word in variables.keys():
                term.word = str(variables[term.word])
        if term.term_type is None and not term.converted:
            if term.word in functions.keys():
                term.operand = functions[term.word]
                term.term_type = TermType.CALL
                term.word = "call"
    return terms    

    
def fixLiteralTerm(term: Term) -> list[Opcode]:
    global string_current_address
    if term.converted:
        opcodes = []
    elif term.term_type is not TermType.STRING:
        opcodes = [Opcode(OpcodeType.PUSH, [OpcodeParam(OpcodeParamType.CONST, term.word)])]
    else:
        opcodes = []
    return opcodes


def term2opcodes(term: Term) -> list[Opcode]:
    opcodes = {
        TermType.DI: [Opcode(OpcodeType.DI, [])],
        TermType.EI: [Opcode(OpcodeType.EI, [])],
        TermType.DUP: [Opcode(OpcodeType.DUP, [])],
        TermType.ADD: [Opcode(OpcodeType.ADD, [])],
        TermType.SUB: [Opcode(OpcodeType.SUB, [])],
        TermType.MUL: [Opcode(OpcodeType.MUL, [])],
        TermType.DIV: [Opcode(OpcodeType.DIV, [])],
        TermType.MOD: [Opcode(OpcodeType.MOD, [])],
        TermType.EMIT: [Opcode(OpcodeType.EMIT, [])],
        TermType.SWAP: [Opcode(OpcodeType.SWAP, [])],
        TermType.DROP: [Opcode(OpcodeType.DROP, [])],
        TermType.OVER: [Opcode(OpcodeType.OVER, [])],
        TermType.EQ: [Opcode(OpcodeType.EQ, [])],
        TermType.LESS: [Opcode(OpcodeType.LESS, [])],
        TermType.MORE: [Opcode(OpcodeType.MORE, [])],
        TermType.READ: [Opcode(OpcodeType.READ, [])],
        TermType.VARIABLE: [],
        TermType.ALLOT: [],
        TermType.ST: [Opcode(OpcodeType.ST, [])],
        TermType.LD: [Opcode(OpcodeType.LD, [])],
        TermType.IF: [Opcode(OpcodeType.JZ, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
        TermType.ELSE: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
        TermType.THEN: [],
        TermType.DEF: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
        TermType.RET: [Opcode(OpcodeType.RET, [])],
        TermType.DEF_INTR: [],
        TermType.DO: [
            Opcode(OpcodeType.DI, []),
            Opcode(OpcodeType.POP, []),  # R(i)
            Opcode(OpcodeType.POP, []),  # R(i, n)
            Opcode(OpcodeType.EI, []),
        ],
        TermType.LOOP: [
            Opcode(OpcodeType.DI, []),
            Opcode(OpcodeType.RPOP, []),  # (n)
            Opcode(OpcodeType.RPOP, []),  # (n, i)
            Opcode(OpcodeType.PUSH, [OpcodeParam(OpcodeParamType.CONST, 1)]),  # (n, i, 1)
            Opcode(OpcodeType.ADD, []),  # (n, i + 1)
            Opcode(OpcodeType.OVER, []),  # (n, i + 1, n)
            Opcode(OpcodeType.OVER, []),  # (n, i + 1, n, i + 1)
            Opcode(OpcodeType.LESS, []),  # (n, i + 1, n > i + 1 [i + 1 < n])
            Opcode(OpcodeType.JZ, [OpcodeParam(OpcodeParamType.UNDEFINED, None)]),  # (n, i + 1)
            Opcode(OpcodeType.DROP, []),  # (n)
            Opcode(OpcodeType.DROP, []),  # ()
            Opcode(OpcodeType.EI, []),
        ],
        TermType.BEGIN: [],
        TermType.UNTIL: [Opcode(OpcodeType.JZ, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
        TermType.LOOP_I: [
            Opcode(OpcodeType.DI, []),
            Opcode(OpcodeType.RPOP, []),
            Opcode(OpcodeType.RPOP, []),
            Opcode(OpcodeType.OVER, []),
            Opcode(OpcodeType.OVER, []),
            Opcode(OpcodeType.POP, []),
            Opcode(OpcodeType.POP, []),
            Opcode(OpcodeType.SWAP, []),
            Opcode(OpcodeType.DROP, []),
            Opcode(OpcodeType.EI, []),
        ],
        TermType.CALL: [Opcode(OpcodeType.CALL, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
        TermType.ENTRYPOINT: [Opcode(OpcodeType.JMP, [OpcodeParam(OpcodeParamType.UNDEFINED, None)])],
    }.get(term.term_type)

    if term.operand and opcodes is not None:
        for opcode in opcodes:
            for param_num, param in enumerate(opcode.params):
                if param.param_type is OpcodeParamType.UNDEFINED:
                    opcode.params[param_num].param_type = OpcodeParamType.ADDR
                    opcode.params[param_num].value = term.operand

    if opcodes is None:
        return fixLiteralTerm(term)

    return opcodes


def fixAddressesInOpcodes(term_opcodes: list[list[Opcode]]) -> list[Opcode]:
    result_opcodes = []
    pref_sum = [0]
    for term_num, opcodes in enumerate(term_opcodes):
        term_opcode_cnt = len(opcodes)
        pref_sum.append(pref_sum[term_num] + term_opcode_cnt)
    for term_opcode in list(filter(lambda x: x is not None, term_opcodes)):
        for opcode in term_opcode:
            for param_num, param in enumerate(opcode.params):
                if param.param_type is OpcodeParamType.ADDR:
                    opcode.params[param_num].value = pref_sum[param.value]
                    opcode.params[param_num].param_type = OpcodeParamType.CONST
                if param.param_type is OpcodeParamType.ADDR_REL:
                    opcode.params[param_num].value = len(result_opcodes) + opcode.params[param_num].value
                    opcode.params[param_num].param_type = OpcodeParamType.CONST
            result_opcodes.append(opcode)
    return result_opcodes


def fixInterruptFunction(terms: list[Term]) -> list[Term]:
    is_interrupt = False
    interrupt_ret = 1
    terms_interrupt_proc = []
    terms_not_interrupt_proc = []
    for term in terms[1:]:
        if term.term_type is TermType.DEF_INTR:
            is_interrupt = True
        if term.term_type is TermType.RET:
            if is_interrupt:
                terms_interrupt_proc.append(term)
                interrupt_ret = len(terms_interrupt_proc) + 1
            else:
                terms_not_interrupt_proc.append(term)
            is_interrupt = False

        if is_interrupt:
            terms_interrupt_proc.append(term)
        elif not is_interrupt and term.term_type is not TermType.RET:
            terms_not_interrupt_proc.append(term)

    terms[0].operand = interrupt_ret
    return [*[terms[0]], *terms_interrupt_proc, *terms_not_interrupt_proc]


def terms2opcodes(terms: list[Term]) -> list[Opcode]:
    terms = fixInterruptFunction(terms)
    opcodes = list(map(term2opcodes, terms))
    opcodes = fixAddressesInOpcodes(opcodes)
    return [*opcodes, Opcode(OpcodeType.HLT, [])]

def translate(source_code: str) -> list[dict]:    
    terms = text2terms(source_code)
    validatedTerms = validateTerms(terms)
    opcodes = terms2opcodes(validatedTerms)
    commands = []
    for index, opcode in enumerate(opcodes):
        command = {
            "index": index,
            "command": opcode.opcode_type,
        }
        if len(opcode.params):
            command["arg"] = int(opcode.params[0].value)
        commands.append(command)
    return commands


def main(source, target):
    global variables, functions, variable_current_address, string_current_address 

    variables = {}
    functions = {}
    variable_current_address = 1024
    string_current_address = 0
    
    with open(source, encoding="utf-8") as f:
        source = f.read()
    
    code = translate(source)
    writeCode(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)



