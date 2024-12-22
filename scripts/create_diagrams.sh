#!/bin/bash

echo "Create Mermaid Charts..."
pyreverse -o mmd toggl_api -d docs/static/mermaid/ --color-palette="#77AADD.#99DDFF"

echo "Creating Project Structure..."
tree toggl_api --gitignore -I __pycache__ >docs/api-guide/project_structure.txt

echo "Done!"
