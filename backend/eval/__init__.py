"""Offline eval harness for the tone engine — the measurement backbone.

You can't make a voice clone "better in every way" without a number that moves.
This package builds a capsule from each fixture persona IN MEMORY (no DB), runs
the real renderer + the real four-signal PFS scorer across registers, and prints
a scorecard — then sweeps generation settings to pick the best by that score.
"""
