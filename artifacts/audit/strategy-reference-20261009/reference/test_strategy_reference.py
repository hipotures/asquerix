"""CPU-only tests for strategy encoding and finite control flow, not geometry."""
import math
import random
import struct
import unittest
from dataclasses import replace

from strategy_reference import (
    Action, Fuel, If, Instruction, MAGIC, MAX_CODE, Op, Predicate, Repeat,
    Selector, Seq, compile_strategy, decode, dry_run_control, encode,
    example_strategy, generate_program, mutate_first_compression, program_digest, verify,
)


class StrategyReferenceTests(unittest.TestCase):
    def test_example_roundtrip(self):
        code = compile_strategy(example_strategy())
        self.assertEqual(decode(encode(code)), code)
        self.assertEqual(len(encode(code)), 12 + 32 * len(code))

    def test_example_true_branch(self):
        actions, status = dry_run_control(compile_strategy(example_strategy()), lambda _: True)
        self.assertEqual(actions.count(Op.COMPRESS), 4)
        self.assertEqual(actions.count(Op.EXPAND), 3)
        self.assertEqual(status, "HALTED")

    def test_example_false_branch(self):
        actions, status = dry_run_control(compile_strategy(example_strategy()), lambda _: False)
        self.assertEqual(actions, [Op.COMPRESS])
        self.assertEqual(status, "HALTED")

    def test_empty_strategy_halts(self):
        self.assertEqual(dry_run_control(compile_strategy(Seq(())), lambda _: False), ([], "HALTED"))

    def test_forward_jump_only(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.JUMP, i1=0), Instruction(Op.HALT)))

    def test_out_of_bounds_jump(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.JUMP, i1=2), Instruction(Op.HALT)))

    def test_missing_halt(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.RESTORE_BEST),))

    def test_unknown_opcode(self):
        payload = MAGIC + struct.pack("<I", 1) + struct.pack("<4I4f", 33, 0, 0, 0, 0, 0, 0, 0)
        with self.assertRaises(ValueError):
            decode(payload)

    def test_unknown_predicate(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.IF_FALSE, i0=999, i1=1), Instruction(Op.HALT)))

    def test_unknown_selector(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.ROTATE, i0=999, i1=1, i2=64, a=0.1), Instruction(Op.HALT)))

    def test_reserved_operands(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.HALT, c=1),))

    def test_nonfinite_parameters(self):
        for value in (math.nan, math.inf, -math.inf, 1e300):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify((Instruction(Op.EXPAND, a=value), Instruction(Op.HALT)))

    def test_bool_is_not_a_budget(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.RELAX, i0=True), Instruction(Op.HALT)))

    def test_float32_underflow_rejected(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.EXPAND, a=1e-100), Instruction(Op.HALT)))

    def test_move_valid_and_invalid(self):
        verify((Instruction(Op.MOVE, i0=int(Selector.ALL), i2=32, a=0.1), Instruction(Op.HALT)))
        with self.assertRaises(ValueError):
            verify((Instruction(Op.MOVE, i2=32), Instruction(Op.HALT)))

    def test_all_selector_forbids_count(self):
        with self.assertRaises(ValueError):
            verify((Instruction(Op.ROTATE, i0=0, i1=1, i2=32, a=0.1), Instruction(Op.HALT)))

    def test_size_checked_before_unrolling(self):
        node = Seq((Action(Instruction(Op.EXPAND, a=0.02)),))
        for _ in range(3):
            node = Seq((Repeat(8, node),))
        with self.assertRaises(ValueError):
            compile_strategy(node)

    def test_deep_sequences_rejected(self):
        node = Seq(())
        for _ in range(20):
            node = Seq((node,))
        with self.assertRaises(ValueError):
            compile_strategy(node)

    def test_raw_control_node_rejected(self):
        with self.assertRaises(ValueError):
            compile_strategy(Seq((Action(Instruction(Op.JUMP, i1=2)),)))

    def test_repeat_count_limit(self):
        with self.assertRaises(ValueError):
            compile_strategy(Seq((Repeat(9, Seq(())),)))

    def test_dispatch_limit(self):
        _, status = dry_run_control(compile_strategy(example_strategy()), lambda _: True, dispatch_limit=2)
        self.assertEqual(status, "DISPATCH_BUDGET")

    def test_predicate_result_type(self):
        with self.assertRaises(ValueError):
            dry_run_control(compile_strategy(example_strategy()), lambda _: 1)

    def test_fuel_no_refund_on_failed_reservation(self):
        fuel = Fuel(10)
        self.assertTrue(fuel.charge(7))
        self.assertFalse(fuel.charge(4))
        self.assertEqual((fuel.remaining, fuel.spent), (3, 7))
        self.assertTrue(fuel.charge(3))
        self.assertEqual((fuel.remaining, fuel.spent), (0, 10))

    def test_fuel_bad_costs(self):
        for value in (0, -1, True, 0.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Fuel(10).charge(value)

    def test_invalid_binary_sizes(self):
        for payload in (b"", MAGIC, MAGIC + struct.pack("<I", 2**32-1)):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                decode(payload)

    def test_trailing_bytes_rejected(self):
        with self.assertRaises(ValueError):
            decode(encode(compile_strategy(Seq(()))) + b"garbage")

    def test_canonical_hash_ignores_float_precision_beyond_f32(self):
        x = 0.02
        y = struct.unpack("<f", struct.pack("<f", x))[0]
        a = compile_strategy(Seq((Action(Instruction(Op.EXPAND, a=x)),)))
        b = compile_strategy(Seq((Action(Instruction(Op.EXPAND, a=y)),)))
        self.assertEqual(program_digest(a), program_digest(b))

    def test_last_possible_program_size(self):
        code = compile_strategy(Seq(tuple(Action(Instruction(Op.RESTORE_BEST)) for _ in range(MAX_CODE-1))))
        self.assertEqual(len(code), MAX_CODE)
        with self.assertRaises(ValueError):
            compile_strategy(Seq(tuple(Action(Instruction(Op.RESTORE_BEST)) for _ in range(MAX_CODE))))

    def test_statically_unrolled_programs_terminate(self):
        rng = random.Random(20261009)
        for _ in range(500):
            reps = rng.randint(1, 8)
            primitive = Action(Instruction(Op.ROTATE, i0=int(Selector.RANDOM_K),
                                           i1=rng.randint(1, 8), i2=64, a=rng.uniform(0.01, 0.3)))
            body = Seq((If(Predicate.LAST_FAILED,
                           Seq((primitive,)),
                           Seq((Action(Instruction(Op.RELAX, i0=32)),))),))
            code = compile_strategy(Seq((Repeat(reps, body),)))
            self.assertEqual(decode(encode(code)), code)
            decisions = iter(bool(rng.getrandbits(1)) for _ in range(reps))
            actions, status = dry_run_control(code, lambda _: next(decisions))
            self.assertEqual(len(actions), reps)
            self.assertEqual(status, "HALTED")


    def test_generator_and_mutation_are_bounded_and_reproducible(self):
        for seed in range(100):
            program = generate_program(seed)
            self.assertEqual(program, generate_program(seed))
            child = mutate_first_compression(program, 1.2)
            code = compile_strategy(child)
            self.assertEqual(decode(encode(code)), code)
            self.assertEqual(dry_run_control(code, lambda _: True)[1], "HALTED")

    def test_mutation_rejects_bad_factor(self):
        for factor in (True, -1, 0, math.nan, math.inf):
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                mutate_first_compression(example_strategy(), factor)


if __name__ == "__main__":
    unittest.main(verbosity=2)
