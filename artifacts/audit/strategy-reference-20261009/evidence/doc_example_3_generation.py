from strategy_reference import (
    compile_strategy, generate_program, mutate_first_compression, program_digest,
)

parent = generate_program(seed=20261009)
child = mutate_first_compression(parent, factor=1.2)
parent_code = compile_strategy(parent)
child_code = compile_strategy(child)
assert program_digest(parent_code) != program_digest(child_code)
