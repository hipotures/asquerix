import math
from strategy_reference import (
    Action, If, Instruction, Op, Predicate, Repeat, Selector, Seq,
    compile_strategy, encode, program_digest,
)

compress = Action(Instruction(Op.COMPRESS, i0=32, i1=128, a=0.02))
escape = Seq((
    Action(Instruction(Op.EXPAND, a=0.02)),
    Action(Instruction(
        Op.ROTATE,
        i0=int(Selector.RANDOM_K),
        i1=3,
        i2=64,
        a=math.radians(8),
    )),
    compress,
))

program = Seq((
    compress,
    Repeat(3, Seq((If(Predicate.COMPRESSION_STALLED, escape),))),
))

code = compile_strategy(program)
payload = encode(code)
print(program_digest(code))
