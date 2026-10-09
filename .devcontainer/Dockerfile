{
  "name": "python-chess-assistant",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter"
      ]
    }
  },
  "postCreateCommand": "python -m pip install --upgrade pip && pip install -r requirements.txt",
  "remoteUser": "vscode"
}
