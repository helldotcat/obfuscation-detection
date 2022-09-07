from collections import defaultdict, Counter
from functools import reduce
from typing import Optional, Mapping, List, Dict, Any, Iterable, Union
import numpy as np
import os
import string
import binascii

import attr


@attr.s(auto_attribs=True)
class AstNode:
    type: str
    name: Optional[str]
    value: Optional[str]
    raw: Optional[str]
    operator: Optional[str]
    alternate: bool
    finalizer: bool
    start: int
    end: int
    parent: Optional['AstNode']
    children: Optional[List['AstNode']]
    id: str = attr.ib(default=attr.Factory(lambda: binascii.hexlify(os.urandom(10)).decode()))

    def get_csv_line(self, file_hash: str) -> str:
        name = str(self.name).replace('"', '') if self.name else self.name
        value = str(self.value).replace('"', '') if self.value else self.value
        raw = str(self.raw).replace('"', '') if self.raw else self.raw
        operator = str(self.operator).replace('"', '') if self.operator else self.operator

        return ','.join(
            [
                f'"{file_hash}"',
                f'"{self.type}"'if self.type else '',
                f'"{name}"' if name else '',
                f'"{value}"' if value else '',
                f'"{operator}"' if operator else '',
                f'"{raw}"' if raw else '',
                f'"{self.id}"',
                f'"{self.parent.id}"' if self.parent else '',
            ]
        )


class AstTree:
    def __init__(self, ast_json: Mapping, script: str) -> None:
        self.root = None
        self.script = script

        self.tree_features = {
            'nodes': defaultdict(int),
            'node_pairs': defaultdict(int),
            'names': defaultdict(int),
            'values': defaultdict(int),
            'raw': defaultdict(int),
            'operators': defaultdict(int),
            'keywords': defaultdict(int),
            'entropy': defaultdict(float),
            'ratios': dict(),
        }

        self._build(ast_json)
        self._collect_tree_features()

        del self.tree_features['names']
        del self.tree_features['values']
        del self.tree_features['raw']
        del self.tree_features['operators']
        del self.tree_features['keywords']

    def _build(self, data: Mapping, parent: Optional[AstNode] = None) -> None:
        try:
            node = AstNode(
                type=data.get('type'),
                name=data['name'] if 'name' in data else None,
                value=data['value'] if 'value' in data and not isinstance(data['value'], dict) else None,
                raw=data['raw'] if 'raw' in data and not isinstance(data['raw'], dict) else None,
                operator=data['operator'] if 'operator' in data else None,
                alternate=True if isinstance(data.get('alternate'), dict) else False,
                finalizer=True if isinstance(data.get('finalizer'), dict) else False,
                start=data['start'],
                end=data['end'],
                parent=parent,
                children=[]
            )
        except KeyError as e:
            return

        if parent is None:
            self.root = node
        else:
            parent.children.append(node)

        self._collect_node_features(node)

        for key, value in data.items():

            if isinstance(value, dict):
                self._build(value, node)

            elif isinstance(value, list):
                for elem in value:
                    if isinstance(elem, dict):
                        self._build(elem, node)

    def get_vertexes(self, node: Optional[AstNode] = None) -> List[AstNode]:
        if node is None:
            node = self.root

        vertexes = [node]
        for child in node.children:
            vertexes.extend(self.get_vertexes(child))

        return vertexes

    def get_edges(self, node: Optional[AstNode] = None) -> List[AstNode]:
        if node is None:
            node = self.root
            vertexes = []
        else:
            vertexes = [(node.parent, node)]

        for child in node.children:
            vertexes.extend(self.get_edges(child))

        return vertexes

    def _collect_node_features(self, node: AstNode) -> None:
        if node.name is not None:
            self.tree_features['names'][node.name] += 1

        if node.value is not None:
            self.tree_features['values'][node.value] += 1

        if node.raw is not None:
            self.tree_features['raw'][node.raw] += 1

        if node.operator is not None:
            self.tree_features['operators'][node.operator] += 1

        if node.alternate:
            self.tree_features['keywords']['else'] += 1

        if node.finalizer:
            self.tree_features['keywords']['finally'] += 1

        self.tree_features['nodes'][node.type] += 1

        if node.parent is not None:
            self.tree_features['node_pairs'][f'{node.parent.type}->{node.type}'] += 1

    def _collect_tree_features(self):
        self.tree_features['entropy']['generic'] = self._calculate_entropy(self.script)
        self.tree_features['entropy']['names'] = self._calculate_entropy(self.names_string)
        self.tree_features['entropy']['values'] = self._calculate_entropy(self.values_string)

        self.tree_features['ratios'] = CharsRatioCounter('chars_').calculate_ratios(self.script)
        self.tree_features['ratios'].update(
            CharsRatioCounter('chars_values_').calculate_ratios(self.values_string)
        )

        self.tree_features['ratios'].update(
            CharsRatioCounter('chars_names_').calculate_ratios(self.names_string)
        )

        self.tree_features['ratios'].update(
            ValuesRatioCounter('values_').calculate_ratios(self.tree_features['values'])
        )

        self.tree_features['ratios'].update(
            ReservedNamesPredicateCounter('reserved_names_').calculate_ratios(self.tree_features['names'])
        )

        self.tree_features['ratios'].update(
            RawRatioCounter('raw_').calculate_ratios(self.tree_features['raw'])
        )

        self.tree_features['ratios'].update(
            OperatorsRatioCounter('operators_').calculate_ratios(self.tree_features['operators'])
        )

        self.tree_features['ratios'].update(
            KeywordsRatioCounter('keywords_').calculate_ratios(
                self.tree_features['keywords'],
                normalizator=sum(v for v in self.tree_features['nodes'].values())
            )
        )

        self.tree_features['ratios'].update(
            QuantilesCounter.calc_length_quantiles(
                sequence=self.convert_dict_to_list(self.tree_features['names']),
                prefix='names_'
            )
        )

        self.tree_features['ratios'].update(
            QuantilesCounter.calc_length_quantiles(
                sequence=self.convert_dict_to_list(self.tree_features['values']),
                prefix='values_'
            )
        )

    @staticmethod
    def convert_dict_to_list(d: Dict[str, int]) -> List[str]:
        data_list = [[k] * v for k, v in d.items() if isinstance(k, str)]

        if len(data_list) < 1:
            return []

        try:
            return reduce(
                lambda x, y: x + y,
                data_list,
            )
        except Exception as e:
            print(d)
            return []

    @property
    def names_string(self):
        return ''.join(
                [k * v for k, v in self.tree_features['names'].items() if isinstance(k, str)]
            )

    @property
    def values_string(self):
        return ''.join(
            [k * v for k, v in self.tree_features['values'].items() if isinstance(k, str)]
        )

    @staticmethod
    def _calculate_entropy(string_: str):
        value, counts = np.unique([c for c in string_], return_counts=True)
        norm_counts = counts / counts.sum()
        return -(norm_counts * np.log2(norm_counts)).sum()


class BasePredicateCounter:
    def calculate_ratios(self, values: Union[Dict[str, int], str], normalizator: Optional[int] = None) -> dict:
        if normalizator is None:
            normalizator = len(values) if isinstance(values, str) else sum(v for v in values.values())

        classes_sum = sum(
            (self._get_classes(v) for v in values)
            if isinstance(values, str)
            else (self._get_classes(k, multiplicator=v) for k, v in values.items()),
            Counter()
        )

        # normalize
        classes_sum = {
            k: v / normalizator for k, v in classes_sum.items()
        }

        classes_sum.update(
            {
                k: 0 for k, _ in self.classes_and_predicates if k not in classes_sum
            }
        )

        return classes_sum

    def _get_classes(self, value: str, multiplicator: int = 1) -> Counter:
        classes = Counter()

        for class_, predicate in self.classes_and_predicates:
            if predicate(value):
                classes.update([class_] * multiplicator)

        return classes


class ValuesRatioCounter(BasePredicateCounter):
    def __init__(self, prefix: str):
        self.classes_and_predicates = [
            (f'{prefix}true', lambda x: x is True),
            (f'{prefix}false', lambda x: x is False),
            (f'{prefix}numeric', lambda x: isinstance(x, (int,  float))),
            (f'{prefix}string', lambda x: isinstance(x, str)),
            (f'{prefix}newlines', lambda x: isinstance(x, str) and '\n' in x),
        ]


class CharsRatioCounter(BasePredicateCounter):
    def __init__(self, prefix: str) -> None:
        self.classes_and_predicates = [
            (f'{prefix}digits', lambda x: x in string.digits),

            (f'{prefix}ascii_uppercase', lambda x: x in string.ascii_uppercase),
            (f'{prefix}ascii_lowercase', lambda x: x in string.ascii_lowercase),
            (f'{prefix}ascii_letters', lambda x: x in string.ascii_letters),

            (f'{prefix}whitespaces', lambda x: x in string.whitespace),
            (f'{prefix}newlines', lambda x: x == '\n'),
            (f'{prefix}backslash', lambda x: x == '\\'),

            (f'{prefix}another', lambda x: x not in string.ascii_lowercase + string.ascii_uppercase + string.digits),
        ]


class ReservedNamesPredicateCounter(BasePredicateCounter):
    # http://ra.ethz.ch/CDstore/www2008/airweb.cse.lehigh.edu/2007/papers/paper_115.pdf

    def __init__(self, prefix: str) -> None:
        self.classes_and_predicates = [
            (f'{prefix}toString', lambda x: x == 'toString'),
            (f'{prefix}eval', lambda x: x == 'eval'),
            (f'{prefix}escape', lambda x: x == 'escape'),
            (f'{prefix}unescape', lambda x: x == 'unescape'),
            (f'{prefix}fromCharCode', lambda x: x == 'fromCharCode'),
            (f'{prefix}charCodeAt', lambda x: x == 'charCodeAt'),
            (f'{prefix}charAt', lambda x: x == 'charAt'),
            (f'{prefix}indexOf', lambda x: x == 'indexOf'),
            (f'{prefix}valueOf', lambda x: x == 'valueOf'),
            (f'{prefix}undefined', lambda x: x == 'undefined'),
        ]


class RawRatioCounter(BasePredicateCounter):
    def __init__(self, prefix: str) -> None:
        self.classes_and_predicates = [
            (f'{prefix}null', lambda x: x == 'null'),
        ]


class OperatorsRatioCounter(BasePredicateCounter):
    def __init__(self, prefix: str) -> None:
        self.classes_and_predicates = [
            (f'{prefix}instanceof', lambda x: x == 'instanceof'),
            (f'{prefix}typeof', lambda x: x == 'typeof'),
        ]


class KeywordsRatioCounter(BasePredicateCounter):
    def __init__(self, prefix: str) -> None:
        self.classes_and_predicates = [
            (f'{prefix}else', lambda x: x == 'else'),
            (f'{prefix}finally', lambda x: x == 'finally'),
        ]


class QuantilesCounter:
    @staticmethod
    def calc_length_quantiles(sequence: List[str], prefix: str):
        if len(sequence) < 1:
            sequence = ['']

        sorted_lengths = sorted([len(s) for s in sequence])
        quantiles = list(range(0, 100, 5))

        quantiles_indexes = list(
            int(i / 100 * len(sorted_lengths)) for i in quantiles
        ) + [
            max(len(sorted_lengths) - 1, 0)
        ]

        return {f'{prefix}quantile_{q}': sorted_lengths[i] for q, i in zip(quantiles + [100], quantiles_indexes)}
