from src.hadocs.collectors.homeassistant import build_indexes, collect_all
from src.hadocs.reports.generator import generate_all
from src.hadocs.utils.config import load_config


def main(log=print):
    cfg = load_config()
    data = collect_all(cfg, log=log)
    idx = build_indexes(data)
    generate_all(data, idx, cfg, log=log)


if __name__ == "__main__":
    main()
