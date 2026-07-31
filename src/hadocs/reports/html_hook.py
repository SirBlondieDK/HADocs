"""Backward-compatible external wrapper. Internal report generation does not use this module."""


def generate_html_dashboard(*args, **kwargs):
    from hadocs.reports.generator import generate_executive_dashboard
    return generate_executive_dashboard(*args, **kwargs)
