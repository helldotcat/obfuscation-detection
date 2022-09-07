import hashlib
import json
import subprocess
import tempfile
from typing import Dict, Any

from converter.tree import AstTree

CSV_HEADER = ','.join(['file_hash', 'type', 'name', 'value', 'operator', 'id', 'parent']) + '\n'


class AstToCsvConverter:
    def __init__(self):
        self.ast_json = None

        self.vertexes = []
        self.edges = []

        self.tree = None

        self.script = ''

    def parse(self, path: str) -> None:
        try:
            self.parse_acorn(path)
        except Exception:
            self.parse_acorn_module(path)

        with open(path, 'rb') as f:
            self.script = f.read().decode('utf-8')

    def parse_from_string(self, code: str) -> None:
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(code.encode('utf-8'))
            fp.flush()

            self.parse(fp.name)

    def parse_acorn(self, path: str):
        bash_command = f'acorn {path} --compact'
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, _ = process.communicate()

        self.ast_json = json.loads(output)

    def parse_acorn_module(self, path: str) -> None:
        bash_command = f'acorn {path} --compact --module'
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, _ = process.communicate()

        self.ast_json = json.loads(output)

    def load_json(self, path: str) -> None:
        with open(path, 'r') as f:
            self.ast_json = json.load(f)

    def convert(self) -> None:
        self.tree = AstTree(self.ast_json, self.script)

    def save_csv(self, path: str):
        file_hash = hashlib.sha256(path.encode()).hexdigest()

        with open(path, 'w') as f:
            f.writelines(CSV_HEADER)
            f.writelines(
                (vertex.get_csv_line(file_hash) + '\n' for vertex in self.tree.get_vertexes())
            )

    def save_features(self, path: str, indent=None):
        with open(path, 'w') as f:
            json.dump(self.tree.tree_features, f, indent=indent)

    def get_features(self) -> Dict[Any, Any]:
        return self.tree.tree_features
