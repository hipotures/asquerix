from strategy_reference import Fuel

fuel = Fuel(1000)
if fuel.charge(228):
    # Perform a bounded square-profile unit of work in the real engine.
    pass
else:
    # Move to finalization; do not retry this reservation forever.
    pass
