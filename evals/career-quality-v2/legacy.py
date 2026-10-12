"""Reuse frozen v1 dataset/measurement utilities without importing its grader."""
import importlib.util
from pathlib import Path

V1 = Path(__file__).resolve().parent.parent / 'career-quality-v1'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, V1 / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


audit = module('v1_dataset_audit', 'validate_dataset.py')
measurement = module('v1_measurement', 'measure.py')
