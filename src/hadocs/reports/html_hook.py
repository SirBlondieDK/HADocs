"""Backward compatibility wrapper for older HADocs imports.

This file must not import generator.py at module load time.
"""


def generate_html_dashboard(*args, **kwargs):
    from src.hadocs.reports.generator import generate_index

    return generate_index(*args, **kwargs)
