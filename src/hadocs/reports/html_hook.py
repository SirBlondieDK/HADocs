"""Compatibility layer for older imports."""

from src.hadocs.reports.generator import generate_index


def generate_html_dashboard(out, project_name, executive, incidents, now):
    return generate_index(out, project_name, executive, incidents, now)