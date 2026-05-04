from app.main import app

for route in app.routes:
    path = getattr(route, 'path', 'N/A')
    name = getattr(route, 'name', 'N/A')
    methods = getattr(route, 'methods', 'N/A')
    print(f"Path: {path}, Name: {name}, Methods: {methods}")
