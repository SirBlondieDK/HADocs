from src.hadocs.explorer.builder import build_explorer_data, build_search_index


def build_knowledge_search_index(model, graph=None) -> list[dict]:
    return build_search_index(build_explorer_data(model, graph))
