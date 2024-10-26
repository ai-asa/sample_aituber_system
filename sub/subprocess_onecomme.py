def subprocess_onecomme(base_dir,queue_data):
    from src.onecomme.onecomme_adapter import OnecommeAdapter
    oc = OnecommeAdapter(base_dir)
    oc.run_websocket(queue_data)