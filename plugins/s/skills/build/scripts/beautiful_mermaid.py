# ---------------------------------------------------------------------------
# VENDORED THIRD-PARTY SOURCE — do not edit by hand.
#
# Upstream:  https://github.com/Orbiter/beautiful-mermaid-py
# File:      beautiful_mermaid.py
# Commit:    d5daa97c8e3f146a50e9eb93e7d666ead5b3debb (2026-02-07)
# Retrieved: 2026-09-04
# License:   MIT (Copyright (c) 2026 Luki Labs; a port of
#            https://github.com/lukilabs/beautiful-mermaid)
#
# Pinned to the reviewed snapshot above rather than tracking upstream: the
# engine carries this renderer's bugs, so it changes only by a deliberate
# re-vendor. The module is stdlib-only (dataclasses, typing, argparse, re),
# which is what lets `render.py` import it without breaking the engine's
# stdlib-only constitution.
#
# Everything below this block is the upstream file, vendored verbatim.
# ---------------------------------------------------------------------------
#!/usr/bin/env python3
"""Pure Python Mermaid -> ASCII/Unicode renderer.

Vibe-Ported from the TypeScript ASCII renderer from
https://github.com/lukilabs/beautiful-mermaid/tree/main/src/ascii
MIT License
Copyright (c) 2026 Luki Labs

Supports:
- Flowcharts / stateDiagram-v2 (grid + A* pathfinding)
- sequenceDiagram
- classDiagram
- erDiagram
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Iterable
import argparse

# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class GridCoord:
    x: int
    y: int


@dataclass(frozen=True)
class DrawingCoord:
    x: int
    y: int


@dataclass(frozen=True)
class Direction:
    x: int
    y: int


Up = Direction(1, 0)
Down = Direction(1, 2)
Left = Direction(0, 1)
Right = Direction(2, 1)
UpperRight = Direction(2, 0)
UpperLeft = Direction(0, 0)
LowerRight = Direction(2, 2)
LowerLeft = Direction(0, 2)
Middle = Direction(1, 1)

ALL_DIRECTIONS = [
    Up, Down, Left, Right, UpperRight, UpperLeft, LowerRight, LowerLeft, Middle
]

Canvas = List[List[str]]


@dataclass
class AsciiStyleClass:
    name: str
    styles: Dict[str, str]


EMPTY_STYLE = AsciiStyleClass(name="", styles={})


@dataclass
class AsciiNode:
    name: str
    displayLabel: str
    index: int
    gridCoord: Optional[GridCoord] = None
    drawingCoord: Optional[DrawingCoord] = None
    drawing: Optional[Canvas] = None
    drawn: bool = False
    styleClassName: str = ""
    styleClass: AsciiStyleClass = field(default_factory=lambda: EMPTY_STYLE)


@dataclass
class AsciiEdge:
    from_node: AsciiNode
    to_node: AsciiNode
    text: str
    path: List[GridCoord] = field(default_factory=list)
    labelLine: List[GridCoord] = field(default_factory=list)
    startDir: Direction = Direction(0, 0)
    endDir: Direction = Direction(0, 0)


@dataclass
class AsciiSubgraph:
    name: str
    nodes: List[AsciiNode]
    parent: Optional["AsciiSubgraph"]
    children: List["AsciiSubgraph"]
    direction: Optional[str] = None
    minX: int = 0
    minY: int = 0
    maxX: int = 0
    maxY: int = 0


@dataclass
class AsciiConfig:
    useAscii: bool
    paddingX: int
    paddingY: int
    boxBorderPadding: int
    graphDirection: str  # 'LR' | 'TD'


@dataclass
class AsciiGraph:
    nodes: List[AsciiNode]
    edges: List[AsciiEdge]
    canvas: Canvas
    grid: Dict[str, AsciiNode]
    columnWidth: Dict[int, int]
    rowHeight: Dict[int, int]
    subgraphs: List[AsciiSubgraph]
    config: AsciiConfig
    offsetX: int = 0
    offsetY: int = 0


# Mermaid parsed types

@dataclass
class MermaidNode:
    id: str
    label: str
    shape: str


@dataclass
class MermaidEdge:
    source: str
    target: str
    label: Optional[str]
    style: str
    hasArrowStart: bool
    hasArrowEnd: bool


@dataclass
class MermaidSubgraph:
    id: str
    label: str
    nodeIds: List[str]
    children: List["MermaidSubgraph"]
    direction: Optional[str] = None


@dataclass
class MermaidGraph:
    direction: str
    nodes: Dict[str, MermaidNode]
    edges: List[MermaidEdge]
    subgraphs: List[MermaidSubgraph]
    classDefs: Dict[str, Dict[str, str]]
    classAssignments: Dict[str, str]
    nodeStyles: Dict[str, Dict[str, str]]


# Sequence types

@dataclass
class Actor:
    id: str
    label: str
    type: str


@dataclass
class Message:
    from_id: str
    to_id: str
    label: str
    lineStyle: str
    arrowHead: str
    activate: bool = False
    deactivate: bool = False


@dataclass
class BlockDivider:
    index: int
    label: str


@dataclass
class Block:
    type: str
    label: str
    startIndex: int
    endIndex: int
    dividers: List[BlockDivider]


@dataclass
class Note:
    actorIds: List[str]
    text: str
    position: str
    afterIndex: int


@dataclass
class SequenceDiagram:
    actors: List[Actor]
    messages: List[Message]
    blocks: List[Block]
    notes: List[Note]


# Class diagram types

@dataclass
class ClassMember:
    visibility: str
    name: str
    type: Optional[str] = None
    isStatic: bool = False
    isAbstract: bool = False


@dataclass
class ClassNode:
    id: str
    label: str
    annotation: Optional[str] = None
    attributes: List[ClassMember] = field(default_factory=list)
    methods: List[ClassMember] = field(default_factory=list)


@dataclass
class ClassRelationship:
    from_id: str
    to_id: str
    type: str
    markerAt: str
    label: Optional[str] = None
    fromCardinality: Optional[str] = None
    toCardinality: Optional[str] = None


@dataclass
class ClassNamespace:
    name: str
    classIds: List[str]


@dataclass
class ClassDiagram:
    classes: List[ClassNode]
    relationships: List[ClassRelationship]
    namespaces: List[ClassNamespace]


# ER types

@dataclass
class ErAttribute:
    type: str
    name: str
    keys: List[str]
    comment: Optional[str] = None


@dataclass
class ErEntity:
    id: str
    label: str
    attributes: List[ErAttribute]


@dataclass
class ErRelationship:
    entity1: str
    entity2: str
    cardinality1: str
    cardinality2: str
    label: str
    identifying: bool


@dataclass
class ErDiagram:
    entities: List[ErEntity]
    relationships: List[ErRelationship]


# =============================================================================
# Coordinate helpers
# =============================================================================

def grid_coord_equals(a: GridCoord, b: GridCoord) -> bool:
    return a.x == b.x and a.y == b.y


def drawing_coord_equals(a: DrawingCoord, b: DrawingCoord) -> bool:
    return a.x == b.x and a.y == b.y


def grid_coord_direction(c: GridCoord, d: Direction) -> GridCoord:
    return GridCoord(c.x + d.x, c.y + d.y)


def grid_key(c: GridCoord) -> str:
    return f"{c.x},{c.y}"


# =============================================================================
# Canvas
# =============================================================================

def mk_canvas(x: int, y: int) -> Canvas:
    canvas: Canvas = []
    for _ in range(x + 1):
        canvas.append([" "] * (y + 1))
    return canvas


def get_canvas_size(canvas: Canvas) -> Tuple[int, int]:
    return (len(canvas) - 1, (len(canvas[0]) if canvas else 1) - 1)


def copy_canvas(source: Canvas) -> Canvas:
    max_x, max_y = get_canvas_size(source)
    return mk_canvas(max_x, max_y)


def increase_size(canvas: Canvas, new_x: int, new_y: int) -> Canvas:
    curr_x, curr_y = get_canvas_size(canvas)
    target_x = max(new_x, curr_x)
    target_y = max(new_y, curr_y)
    grown = mk_canvas(target_x, target_y)
    for x in range(len(grown)):
        for y in range(len(grown[0])):
            if x < len(canvas) and y < len(canvas[0]):
                grown[x][y] = canvas[x][y]
    canvas[:] = grown
    return canvas


JUNCTION_CHARS = {
    '─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '╴', '╵', '╶', '╷',
}


def is_junction_char(c: str) -> bool:
    return c in JUNCTION_CHARS


JUNCTION_MAP: Dict[str, Dict[str, str]] = {
    '─': { '│': '┼', '┌': '┬', '┐': '┬', '└': '┴', '┘': '┴', '├': '┼', '┤': '┼', '┬': '┬', '┴': '┴' },
    '│': { '─': '┼', '┌': '├', '┐': '┤', '└': '├', '┘': '┤', '├': '├', '┤': '┤', '┬': '┼', '┴': '┼' },
    '┌': { '─': '┬', '│': '├', '┐': '┬', '└': '├', '┘': '┼', '├': '├', '┤': '┼', '┬': '┬', '┴': '┼' },
    '┐': { '─': '┬', '│': '┤', '┌': '┬', '└': '┼', '┘': '┤', '├': '┼', '┤': '┤', '┬': '┬', '┴': '┼' },
    '└': { '─': '┴', '│': '├', '┌': '├', '┐': '┼', '┘': '┴', '├': '├', '┤': '┼', '┬': '┼', '┴': '┴' },
    '┘': { '─': '┴', '│': '┤', '┌': '┼', '┐': '┤', '└': '┴', '├': '┼', '┤': '┤', '┬': '┼', '┴': '┴' },
    '├': { '─': '┼', '│': '├', '┌': '├', '┐': '┼', '└': '├', '┘': '┼', '┤': '┼', '┬': '┼', '┴': '┼' },
    '┤': { '─': '┼', '│': '┤', '┌': '┼', '┐': '┤', '└': '┼', '┘': '┤', '├': '┼', '┬': '┼', '┴': '┼' },
    '┬': { '─': '┬', '│': '┼', '┌': '┬', '┐': '┬', '└': '┼', '┘': '┼', '├': '┼', '┤': '┼', '┴': '┼' },
    '┴': { '─': '┴', '│': '┼', '┌': '┼', '┐': '┼', '└': '┴', '┘': '┴', '├': '┼', '┤': '┼', '┬': '┼' },
}


def merge_junctions(c1: str, c2: str) -> str:
    return JUNCTION_MAP.get(c1, {}).get(c2, c1)


def merge_canvases(base: Canvas, offset: DrawingCoord, use_ascii: bool, *overlays: Canvas) -> Canvas:
    max_x, max_y = get_canvas_size(base)
    for overlay in overlays:
        ox, oy = get_canvas_size(overlay)
        max_x = max(max_x, ox + offset.x)
        max_y = max(max_y, oy + offset.y)

    merged = mk_canvas(max_x, max_y)

    for x in range(max_x + 1):
        for y in range(max_y + 1):
            if x < len(base) and y < len(base[0]):
                merged[x][y] = base[x][y]

    for overlay in overlays:
        for x in range(len(overlay)):
            for y in range(len(overlay[0])):
                c = overlay[x][y]
                if c != ' ':
                    mx = x + offset.x
                    my = y + offset.y
                    current = merged[mx][my]
                    if not use_ascii and is_junction_char(c) and is_junction_char(current):
                        merged[mx][my] = merge_junctions(current, c)
                    else:
                        merged[mx][my] = c

    return merged


def canvas_to_string(canvas: Canvas) -> str:
    max_x, max_y = get_canvas_size(canvas)
    min_x = max_x + 1
    min_y = max_y + 1
    used_max_x = -1
    used_max_y = -1

    for x in range(max_x + 1):
        for y in range(max_y + 1):
            if canvas[x][y] != ' ':
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                used_max_x = max(used_max_x, x)
                used_max_y = max(used_max_y, y)

    if used_max_x < 0 or used_max_y < 0:
        return ''

    lines: List[str] = []
    for y in range(min_y, used_max_y + 1):
        line = ''.join(canvas[x][y] for x in range(min_x, used_max_x + 1))
        lines.append(line.rstrip())
    return '\n'.join(lines)


VERTICAL_FLIP_MAP = {
    '▲': '▼', '▼': '▲',
    '◤': '◣', '◣': '◤',
    '◥': '◢', '◢': '◥',
    '^': 'v', 'v': '^',
    '┌': '└', '└': '┌',
    '┐': '┘', '┘': '┐',
    '┬': '┴', '┴': '┬',
    '╵': '╷', '╷': '╵',
}


def flip_canvas_vertically(canvas: Canvas) -> Canvas:
    for col in canvas:
        col.reverse()
    for col in canvas:
        for y in range(len(col)):
            flipped = VERTICAL_FLIP_MAP.get(col[y])
            if flipped:
                col[y] = flipped
    return canvas


def draw_text(canvas: Canvas, start: DrawingCoord, text: str) -> None:
    increase_size(canvas, start.x + len(text), start.y)
    for i, ch in enumerate(text):
        canvas[start.x + i][start.y] = ch


def set_canvas_size_to_grid(canvas: Canvas, column_width: Dict[int, int], row_height: Dict[int, int]) -> None:
    max_x = 0
    max_y = 0
    for w in column_width.values():
        max_x += w
    for h in row_height.values():
        max_y += h
    increase_size(canvas, max_x, max_y)


# =============================================================================
# Parser: flowchart + state diagram
# =============================================================================

import re


ARROW_REGEX = re.compile(r'^(<)?(-->|-.->|==>|---|-\.-|===)(?:\|([^|]*)\|)?')

NODE_PATTERNS = [
    (re.compile(r'^([\w-]+)\(\(\((.+?)\)\)\)'), 'doublecircle'),
    (re.compile(r'^([\w-]+)\(\[(.+?)\]\)'), 'stadium'),
    (re.compile(r'^([\w-]+)\(\((.+?)\)\)'), 'circle'),
    (re.compile(r'^([\w-]+)\[\[(.+?)\]\]'), 'subroutine'),
    (re.compile(r'^([\w-]+)\[\((.+?)\)\]'), 'cylinder'),
    (re.compile(r'^([\w-]+)\[\/(.+?)\\\]'), 'trapezoid'),
    (re.compile(r'^([\w-]+)\[\\(.+?)\/\]'), 'trapezoid-alt'),
    (re.compile(r'^([\w-]+)>(.+?)\]'), 'asymmetric'),
    (re.compile(r'^([\w-]+)\{\{(.+?)\}\}'), 'hexagon'),
    (re.compile(r'^([\w-]+)\[(.+?)\]'), 'rectangle'),
    (re.compile(r'^([\w-]+)\((.+?)\)'), 'rounded'),
    (re.compile(r'^([\w-]+)\{(.+?)\}'), 'diamond'),
]

BARE_NODE_REGEX = re.compile(r'^([\w-]+)')
CLASS_SHORTHAND_REGEX = re.compile(r'^:::([\w][\w-]*)')


def parse_mermaid(text: str) -> MermaidGraph:
    lines = [l.strip() for l in re.split(r'[\n;]', text) if l.strip() and not l.strip().startswith('%%')]
    if not lines:
        raise ValueError("Empty mermaid diagram")

    header = lines[0]
    if re.match(r'^stateDiagram(-v2)?\s*$', header, re.I):
        return parse_state_diagram(lines)
    return parse_flowchart(lines)


def parse_flowchart(lines: List[str]) -> MermaidGraph:
    m = re.match(r'^(?:graph|flowchart)\s+(TD|TB|LR|BT|RL)\s*$', lines[0], re.I)
    if not m:
        raise ValueError(f"Invalid mermaid header: \"{lines[0]}\". Expected 'graph TD', 'flowchart LR', 'stateDiagram-v2', etc.")
    direction = m.group(1).upper()
    graph = MermaidGraph(
        direction=direction,
        nodes={},
        edges=[],
        subgraphs=[],
        classDefs={},
        classAssignments={},
        nodeStyles={},
    )

    subgraph_stack: List[MermaidSubgraph] = []

    for line in lines[1:]:
        class_def = re.match(r'^classDef\s+(\w+)\s+(.+)$', line)
        if class_def:
            name = class_def.group(1)
            props = parse_style_props(class_def.group(2))
            graph.classDefs[name] = props
            continue

        class_assign = re.match(r'^class\s+([\w,-]+)\s+(\w+)$', line)
        if class_assign:
            node_ids = [s.strip() for s in class_assign.group(1).split(',')]
            class_name = class_assign.group(2)
            for nid in node_ids:
                graph.classAssignments[nid] = class_name
            continue

        style_match = re.match(r'^style\s+([\w,-]+)\s+(.+)$', line)
        if style_match:
            node_ids = [s.strip() for s in style_match.group(1).split(',')]
            props = parse_style_props(style_match.group(2))
            for nid in node_ids:
                existing = graph.nodeStyles.get(nid, {})
                existing.update(props)
                graph.nodeStyles[nid] = existing
            continue

        dir_match = re.match(r'^direction\s+(TD|TB|LR|BT|RL)\s*$', line, re.I)
        if dir_match and subgraph_stack:
            subgraph_stack[-1].direction = dir_match.group(1).upper()
            continue

        subgraph_match = re.match(r'^subgraph\s+(.+)$', line)
        if subgraph_match:
            rest = subgraph_match.group(1).strip()
            bracket = re.match(r'^([\w-]+)\s*\[(.+)\]$', rest)
            if bracket:
                sg_id = bracket.group(1)
                label = bracket.group(2)
            else:
                label = rest
                sg_id = re.sub(r'[^\w]', '', re.sub(r'\s+', '_', rest))
            sg = MermaidSubgraph(id=sg_id, label=label, nodeIds=[], children=[])
            subgraph_stack.append(sg)
            continue

        if line == 'end':
            completed = subgraph_stack.pop() if subgraph_stack else None
            if completed:
                if subgraph_stack:
                    subgraph_stack[-1].children.append(completed)
                else:
                    graph.subgraphs.append(completed)
            continue

        parse_edge_line(line, graph, subgraph_stack)

    return graph


def parse_state_diagram(lines: List[str]) -> MermaidGraph:
    graph = MermaidGraph(
        direction='TD',
        nodes={},
        edges=[],
        subgraphs=[],
        classDefs={},
        classAssignments={},
        nodeStyles={},
    )
    composite_stack: List[MermaidSubgraph] = []
    start_count = 0
    end_count = 0

    for line in lines[1:]:
        dir_match = re.match(r'^direction\s+(TD|TB|LR|BT|RL)\s*$', line, re.I)
        if dir_match:
            if composite_stack:
                composite_stack[-1].direction = dir_match.group(1).upper()
            else:
                graph.direction = dir_match.group(1).upper()
            continue

        comp_match = re.match(r'^state\s+(?:"([^"]+)"\s+as\s+)?(\w+)\s*\{$', line)
        if comp_match:
            label = comp_match.group(1) or comp_match.group(2)
            sg_id = comp_match.group(2)
            sg = MermaidSubgraph(id=sg_id, label=label, nodeIds=[], children=[])
            composite_stack.append(sg)
            continue

        if line == '}':
            completed = composite_stack.pop() if composite_stack else None
            if completed:
                if composite_stack:
                    composite_stack[-1].children.append(completed)
                else:
                    graph.subgraphs.append(completed)
            continue

        alias_match = re.match(r'^state\s+"([^"]+)"\s+as\s+(\w+)\s*$', line)
        if alias_match:
            label = alias_match.group(1)
            sid = alias_match.group(2)
            register_state_node(graph, composite_stack, MermaidNode(id=sid, label=label, shape='rounded'))
            continue

        trans_match = re.match(r'^(\[\*\]|[\w-]+)\s*(-->)\s*(\[\*\]|[\w-]+)(?:\s*:\s*(.+))?$', line)
        if trans_match:
            source_id = trans_match.group(1)
            target_id = trans_match.group(3)
            edge_label = (trans_match.group(4) or '').strip() or None

            if source_id == '[*]':
                start_count += 1
                source_id = f"_start{start_count if start_count > 1 else ''}"
                register_state_node(graph, composite_stack, MermaidNode(id=source_id, label='', shape='state-start'))
            else:
                ensure_state_node(graph, composite_stack, source_id)

            if target_id == '[*]':
                end_count += 1
                target_id = f"_end{end_count if end_count > 1 else ''}"
                register_state_node(graph, composite_stack, MermaidNode(id=target_id, label='', shape='state-end'))
            else:
                ensure_state_node(graph, composite_stack, target_id)

            graph.edges.append(MermaidEdge(
                source=source_id,
                target=target_id,
                label=edge_label,
                style='solid',
                hasArrowStart=False,
                hasArrowEnd=True,
            ))
            continue

        desc_match = re.match(r'^([\w-]+)\s*:\s*(.+)$', line)
        if desc_match:
            sid = desc_match.group(1)
            label = desc_match.group(2).strip()
            register_state_node(graph, composite_stack, MermaidNode(id=sid, label=label, shape='rounded'))
            continue

    return graph


def register_state_node(graph: MermaidGraph, stack: List[MermaidSubgraph], node: MermaidNode) -> None:
    if node.id not in graph.nodes:
        graph.nodes[node.id] = node
    if stack:
        if node.id.startswith(('_start', '_end')):
            return
        current = stack[-1]
        if node.id not in current.nodeIds:
            current.nodeIds.append(node.id)


def ensure_state_node(graph: MermaidGraph, stack: List[MermaidSubgraph], node_id: str) -> None:
    if node_id not in graph.nodes:
        register_state_node(graph, stack, MermaidNode(id=node_id, label=node_id, shape='rounded'))
    else:
        if stack:
            if node_id.startswith(('_start', '_end')):
                return
            current = stack[-1]
            if node_id not in current.nodeIds:
                current.nodeIds.append(node_id)


def parse_style_props(props_str: str) -> Dict[str, str]:
    props: Dict[str, str] = {}
    for pair in props_str.split(','):
        colon = pair.find(':')
        if colon > 0:
            key = pair[:colon].strip()
            val = pair[colon + 1:].strip()
            if key and val:
                props[key] = val
    return props


def arrow_style_from_op(op: str) -> str:
    if op == '-.->' or op == '-.-':
        return 'dotted'
    if op == '==>' or op == '===':
        return 'thick'
    return 'solid'


def parse_edge_line(line: str, graph: MermaidGraph, subgraph_stack: List[MermaidSubgraph]) -> None:
    remaining = line.strip()
    first_group = consume_node_group(remaining, graph, subgraph_stack)
    if not first_group or not first_group['ids']:
        return

    remaining = first_group['remaining'].strip()
    prev_group_ids = first_group['ids']

    while remaining:
        m = ARROW_REGEX.match(remaining)
        if not m:
            break

        has_arrow_start = bool(m.group(1))
        arrow_op = m.group(2)
        edge_label = (m.group(3) or '').strip() or None
        remaining = remaining[len(m.group(0)):].strip()

        style = arrow_style_from_op(arrow_op)
        has_arrow_end = arrow_op.endswith('>')

        next_group = consume_node_group(remaining, graph, subgraph_stack)
        if not next_group or not next_group['ids']:
            break

        remaining = next_group['remaining'].strip()

        for src in prev_group_ids:
            for tgt in next_group['ids']:
                graph.edges.append(MermaidEdge(
                    source=src,
                    target=tgt,
                    label=edge_label,
                    style=style,
                    hasArrowStart=has_arrow_start,
                    hasArrowEnd=has_arrow_end,
                ))

        prev_group_ids = next_group['ids']


def consume_node_group(text: str, graph: MermaidGraph, subgraph_stack: List[MermaidSubgraph]) -> Optional[Dict[str, object]]:
    first = consume_node(text, graph, subgraph_stack)
    if not first:
        return None

    ids = [first['id']]
    remaining = first['remaining'].strip()

    while remaining.startswith('&'):
        remaining = remaining[1:].strip()
        nxt = consume_node(remaining, graph, subgraph_stack)
        if not nxt:
            break
        ids.append(nxt['id'])
        remaining = nxt['remaining'].strip()

    return {'ids': ids, 'remaining': remaining}


def consume_node(text: str, graph: MermaidGraph, subgraph_stack: List[MermaidSubgraph]) -> Optional[Dict[str, object]]:
    node_id: Optional[str] = None
    remaining = text

    for regex, shape in NODE_PATTERNS:
        m = regex.match(text)
        if m:
            node_id = m.group(1)
            label = m.group(2)
            register_node(graph, subgraph_stack, MermaidNode(id=node_id, label=label, shape=shape))
            remaining = text[len(m.group(0)):]  # type: ignore[index]
            break

    if node_id is None:
        m = BARE_NODE_REGEX.match(text)
        if m:
            node_id = m.group(1)
            if node_id not in graph.nodes:
                register_node(graph, subgraph_stack, MermaidNode(id=node_id, label=node_id, shape='rectangle'))
            else:
                track_in_subgraph(subgraph_stack, node_id)
            remaining = text[len(m.group(0)):]

    if node_id is None:
        return None

    class_match = CLASS_SHORTHAND_REGEX.match(remaining)
    if class_match:
        graph.classAssignments[node_id] = class_match.group(1)
        remaining = remaining[len(class_match.group(0)):]  # type: ignore[index]

    return {'id': node_id, 'remaining': remaining}


def register_node(graph: MermaidGraph, subgraph_stack: List[MermaidSubgraph], node: MermaidNode) -> None:
    if node.id not in graph.nodes:
        graph.nodes[node.id] = node
    track_in_subgraph(subgraph_stack, node.id)


def track_in_subgraph(subgraph_stack: List[MermaidSubgraph], node_id: str) -> None:
    if subgraph_stack:
        current = subgraph_stack[-1]
        if node_id not in current.nodeIds:
            current.nodeIds.append(node_id)


# =============================================================================
# Parser: sequence
# =============================================================================

def parse_sequence_diagram(lines: List[str]) -> SequenceDiagram:
    diagram = SequenceDiagram(actors=[], messages=[], blocks=[], notes=[])
    actor_ids: set[str] = set()
    block_stack: List[Dict[str, object]] = []

    for line in lines[1:]:
        actor_match = re.match(r'^(participant|actor)\s+(\S+?)(?:\s+as\s+(.+))?$', line)
        if actor_match:
            typ = actor_match.group(1)
            aid = actor_match.group(2)
            label = actor_match.group(3).strip() if actor_match.group(3) else aid
            if aid not in actor_ids:
                actor_ids.add(aid)
                diagram.actors.append(Actor(id=aid, label=label, type=typ))
            continue

        note_match = re.match(r'^Note\s+(left of|right of|over)\s+([^:]+):\s*(.+)$', line, re.I)
        if note_match:
            pos_str = note_match.group(1).lower()
            actors_str = note_match.group(2).strip()
            text = note_match.group(3).strip()
            note_actor_ids = [s.strip() for s in actors_str.split(',')]
            for aid in note_actor_ids:
                ensure_actor(diagram, actor_ids, aid)
            position = 'over'
            if pos_str == 'left of':
                position = 'left'
            elif pos_str == 'right of':
                position = 'right'
            diagram.notes.append(Note(
                actorIds=note_actor_ids,
                text=text,
                position=position,
                afterIndex=len(diagram.messages) - 1,
            ))
            continue

        block_match = re.match(r'^(loop|alt|opt|par|critical|break|rect)\s*(.*)$', line)
        if block_match:
            block_type = block_match.group(1)
            label = (block_match.group(2) or '').strip()
            block_stack.append({
                'type': block_type,
                'label': label,
                'startIndex': len(diagram.messages),
                'dividers': [],
            })
            continue

        divider_match = re.match(r'^(else|and)\s*(.*)$', line)
        if divider_match and block_stack:
            label = (divider_match.group(2) or '').strip()
            block_stack[-1]['dividers'].append(BlockDivider(index=len(diagram.messages), label=label))
            continue

        if line == 'end' and block_stack:
            completed = block_stack.pop()
            diagram.blocks.append(Block(
                type=completed['type'],
                label=completed['label'],
                startIndex=completed['startIndex'],
                endIndex=max(len(diagram.messages) - 1, completed['startIndex']),
                dividers=completed['dividers'],
            ))
            continue

        msg_match = re.match(r'^(\S+?)\s*(--?>?>|--?[)x]|--?>>|--?>)\s*([+-]?)(\S+?)\s*:\s*(.+)$', line)
        if msg_match:
            frm = msg_match.group(1)
            arrow = msg_match.group(2)
            activation_mark = msg_match.group(3)
            to = msg_match.group(4)
            label = msg_match.group(5).strip()

            ensure_actor(diagram, actor_ids, frm)
            ensure_actor(diagram, actor_ids, to)

            line_style = 'dashed' if arrow.startswith('--') else 'solid'
            arrow_head = 'filled' if ('>>' in arrow or 'x' in arrow) else 'open'

            msg = Message(from_id=frm, to_id=to, label=label, lineStyle=line_style, arrowHead=arrow_head)
            if activation_mark == '+':
                msg.activate = True
            if activation_mark == '-':
                msg.deactivate = True
            diagram.messages.append(msg)
            continue

        simple_msg = re.match(r'^(\S+?)\s*(->>|-->>|-\)|--\)|-x|--x|->|-->)\s*([+-]?)(\S+?)\s*:\s*(.+)$', line)
        if simple_msg:
            frm = simple_msg.group(1)
            arrow = simple_msg.group(2)
            activation_mark = simple_msg.group(3)
            to = simple_msg.group(4)
            label = simple_msg.group(5).strip()

            ensure_actor(diagram, actor_ids, frm)
            ensure_actor(diagram, actor_ids, to)

            line_style = 'dashed' if arrow.startswith('--') else 'solid'
            arrow_head = 'filled' if ('>>' in arrow or 'x' in arrow) else 'open'
            msg = Message(from_id=frm, to_id=to, label=label, lineStyle=line_style, arrowHead=arrow_head)
            if activation_mark == '+':
                msg.activate = True
            if activation_mark == '-':
                msg.deactivate = True
            diagram.messages.append(msg)
            continue

    return diagram


def ensure_actor(diagram: SequenceDiagram, actor_ids: set[str], actor_id: str) -> None:
    if actor_id not in actor_ids:
        actor_ids.add(actor_id)
        diagram.actors.append(Actor(id=actor_id, label=actor_id, type='participant'))


# =============================================================================
# Parser: class diagram
# =============================================================================

def parse_class_diagram(lines: List[str]) -> ClassDiagram:
    diagram = ClassDiagram(classes=[], relationships=[], namespaces=[])
    class_map: Dict[str, ClassNode] = {}
    current_namespace: Optional[ClassNamespace] = None
    current_class: Optional[ClassNode] = None
    brace_depth = 0

    for line in lines[1:]:
        if current_class and brace_depth > 0:
            if line == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    current_class = None
                continue

            annot_match = re.match(r'^<<(\w+)>>$', line)
            if annot_match:
                current_class.annotation = annot_match.group(1)
                continue

            member = parse_class_member(line)
            if member:
                if member['isMethod']:
                    current_class.methods.append(member['member'])
                else:
                    current_class.attributes.append(member['member'])
            continue

        ns_match = re.match(r'^namespace\s+(\S+)\s*\{$', line)
        if ns_match:
            current_namespace = ClassNamespace(name=ns_match.group(1), classIds=[])
            continue

        if line == '}' and current_namespace:
            diagram.namespaces.append(current_namespace)
            current_namespace = None
            continue

        class_block = re.match(r'^class\s+(\S+?)(?:\s*~(\w+)~)?\s*\{$', line)
        if class_block:
            cid = class_block.group(1)
            generic = class_block.group(2)
            cls = ensure_class(class_map, cid)
            if generic:
                cls.label = f"{cid}<{generic}>"
            current_class = cls
            brace_depth = 1
            if current_namespace:
                current_namespace.classIds.append(cid)
            continue

        class_only = re.match(r'^class\s+(\S+?)(?:\s*~(\w+)~)?\s*$', line)
        if class_only:
            cid = class_only.group(1)
            generic = class_only.group(2)
            cls = ensure_class(class_map, cid)
            if generic:
                cls.label = f"{cid}<{generic}>"
            if current_namespace:
                current_namespace.classIds.append(cid)
            continue

        inline_annot = re.match(r'^class\s+(\S+?)\s*\{\s*<<(\w+)>>\s*\}$', line)
        if inline_annot:
            cls = ensure_class(class_map, inline_annot.group(1))
            cls.annotation = inline_annot.group(2)
            continue

        inline_attr = re.match(r'^(\S+?)\s*:\s*(.+)$', line)
        if inline_attr:
            rest = inline_attr.group(2)
            if not re.search(r'<\|--|--|\*--|o--|-->|\.\.>|\.\.\|>', rest):
                cls = ensure_class(class_map, inline_attr.group(1))
                member = parse_class_member(rest)
                if member:
                    if member['isMethod']:
                        cls.methods.append(member['member'])
                    else:
                        cls.attributes.append(member['member'])
                continue

        rel = parse_class_relationship(line)
        if rel:
            ensure_class(class_map, rel.from_id)
            ensure_class(class_map, rel.to_id)
            diagram.relationships.append(rel)
            continue

    diagram.classes = list(class_map.values())
    return diagram


def ensure_class(class_map: Dict[str, ClassNode], cid: str) -> ClassNode:
    if cid not in class_map:
        class_map[cid] = ClassNode(id=cid, label=cid, attributes=[], methods=[])
    return class_map[cid]


def parse_class_member(line: str) -> Optional[Dict[str, object]]:
    trimmed = line.strip().rstrip(';')
    if not trimmed:
        return None

    visibility = ''
    rest = trimmed
    if re.match(r'^[+\-#~]', rest):
        visibility = rest[0]
        rest = rest[1:].strip()

    method_match = re.match(r'^(.+?)\(([^)]*)\)(?:\s*(.+))?$', rest)
    if method_match:
        name = method_match.group(1).strip()
        typ = (method_match.group(3) or '').strip() or None
        is_static = name.endswith('$') or '$' in rest
        is_abstract = name.endswith('*') or '*' in rest
        member = ClassMember(
            visibility=visibility,
            name=name.replace('$', '').replace('*', ''),
            type=typ,
            isStatic=is_static,
            isAbstract=is_abstract,
        )
        return {'member': member, 'isMethod': True}

    parts = rest.split()
    if len(parts) >= 2:
        name = parts[0]
        typ = ' '.join(parts[1:])
    else:
        name = parts[0] if parts else rest
        typ = None

    is_static = name.endswith('$')
    is_abstract = name.endswith('*')
    member = ClassMember(
        visibility=visibility,
        name=name.replace('$', '').replace('*', '').rstrip(':'),
        type=typ,
        isStatic=is_static,
        isAbstract=is_abstract,
    )
    return {'member': member, 'isMethod': False}


def parse_class_relationship(line: str) -> Optional[ClassRelationship]:
    match = re.match(
        r'^(\S+?)\s+(?:"([^"]*?)"\s+)?(<\|--|<\|\.\.|\*--|o--|-->|--\*|--o|--|>\s*|\.\.>|\.\.\|>|--)\s+(?:"([^"]*?)"\s+)?(\S+?)(?:\s*:\s*(.+))?$',
        line
    )
    if not match:
        return None

    from_id = match.group(1)
    from_card = match.group(2) or None
    arrow = match.group(3).strip()
    to_card = match.group(4) or None
    to_id = match.group(5)
    label = (match.group(6) or '').strip() or None

    parsed = parse_class_arrow(arrow)
    if not parsed:
        return None

    return ClassRelationship(
        from_id=from_id,
        to_id=to_id,
        type=parsed['type'],
        markerAt=parsed['markerAt'],
        label=label,
        fromCardinality=from_card,
        toCardinality=to_card,
    )


def parse_class_arrow(arrow: str) -> Optional[Dict[str, str]]:
    if arrow == '<|--':
        return {'type': 'inheritance', 'markerAt': 'from'}
    if arrow == '<|..':
        return {'type': 'realization', 'markerAt': 'from'}
    if arrow == '*--':
        return {'type': 'composition', 'markerAt': 'from'}
    if arrow == '--*':
        return {'type': 'composition', 'markerAt': 'to'}
    if arrow == 'o--':
        return {'type': 'aggregation', 'markerAt': 'from'}
    if arrow == '--o':
        return {'type': 'aggregation', 'markerAt': 'to'}
    if arrow == '-->':
        return {'type': 'association', 'markerAt': 'to'}
    if arrow == '..>':
        return {'type': 'dependency', 'markerAt': 'to'}
    if arrow == '..|>':
        return {'type': 'realization', 'markerAt': 'to'}
    if arrow == '--':
        return {'type': 'association', 'markerAt': 'to'}
    return None


# =============================================================================
# Parser: ER diagram
# =============================================================================

def parse_er_diagram(lines: List[str]) -> ErDiagram:
    diagram = ErDiagram(entities=[], relationships=[])
    entity_map: Dict[str, ErEntity] = {}
    current_entity: Optional[ErEntity] = None

    for line in lines[1:]:
        if current_entity:
            if line == '}':
                current_entity = None
                continue
            attr = parse_er_attribute(line)
            if attr:
                current_entity.attributes.append(attr)
            continue

        entity_block = re.match(r'^(\S+)\s*\{$', line)
        if entity_block:
            eid = entity_block.group(1)
            entity = ensure_entity(entity_map, eid)
            current_entity = entity
            continue

        rel = parse_er_relationship_line(line)
        if rel:
            ensure_entity(entity_map, rel.entity1)
            ensure_entity(entity_map, rel.entity2)
            diagram.relationships.append(rel)
            continue

    diagram.entities = list(entity_map.values())
    return diagram


def ensure_entity(entity_map: Dict[str, ErEntity], eid: str) -> ErEntity:
    if eid not in entity_map:
        entity_map[eid] = ErEntity(id=eid, label=eid, attributes=[])
    return entity_map[eid]


def parse_er_attribute(line: str) -> Optional[ErAttribute]:
    m = re.match(r'^(\S+)\s+(\S+)(?:\s+(.+))?$', line)
    if not m:
        return None
    typ = m.group(1)
    name = m.group(2)
    rest = (m.group(3) or '').strip()

    keys: List[str] = []
    comment: Optional[str] = None
    comment_match = re.search(r'"([^"]*)"', rest)
    if comment_match:
        comment = comment_match.group(1)

    rest_wo_comment = re.sub(r'"[^"]*"', '', rest).strip()
    for part in rest_wo_comment.split():
        upper = part.upper()
        if upper in ('PK', 'FK', 'UK'):
            keys.append(upper)

    return ErAttribute(type=typ, name=name, keys=keys, comment=comment)


def parse_er_relationship_line(line: str) -> Optional[ErRelationship]:
    m = re.match(r'^(\S+)\s+([|o}{]+(?:--|\.\.)[|o}{]+)\s+(\S+)\s*:\s*(.+)$', line)
    if not m:
        return None
    entity1 = m.group(1)
    card_str = m.group(2)
    entity2 = m.group(3)
    label = m.group(4).strip()

    line_match = re.match(r'^([|o}{]+)(--|\.\.?)([|o}{]+)$', card_str)
    if not line_match:
        return None
    left_str = line_match.group(1)
    line_style = line_match.group(2)
    right_str = line_match.group(3)

    card1 = parse_cardinality(left_str)
    card2 = parse_cardinality(right_str)
    identifying = (line_style == '--')

    if not card1 or not card2:
        return None

    return ErRelationship(
        entity1=entity1,
        entity2=entity2,
        cardinality1=card1,
        cardinality2=card2,
        label=label,
        identifying=identifying,
    )


def parse_cardinality(s: str) -> Optional[str]:
    sorted_str = ''.join(sorted(s))
    if sorted_str == '||':
        return 'one'
    if sorted_str == 'o|':
        return 'zero-one'
    if sorted_str in ('|}', '{|'):
        return 'many'
    if sorted_str in ('{o', 'o{'):
        return 'zero-many'
    return None


# =============================================================================
# Converter: MermaidGraph -> AsciiGraph
# =============================================================================

def convert_to_ascii_graph(parsed: MermaidGraph, config: AsciiConfig) -> AsciiGraph:
    node_map: Dict[str, AsciiNode] = {}
    index = 0

    for node_id, m_node in parsed.nodes.items():
        ascii_node = AsciiNode(
            name=node_id,
            displayLabel=m_node.label,
            index=index,
            gridCoord=None,
            drawingCoord=None,
            drawing=None,
            drawn=False,
            styleClassName='',
            styleClass=EMPTY_STYLE,
        )
        node_map[node_id] = ascii_node
        index += 1

    nodes = list(node_map.values())

    edges: List[AsciiEdge] = []
    for m_edge in parsed.edges:
        from_node = node_map.get(m_edge.source)
        to_node = node_map.get(m_edge.target)
        if not from_node or not to_node:
            continue
        edges.append(AsciiEdge(
            from_node=from_node,
            to_node=to_node,
            text=m_edge.label or '',
            path=[],
            labelLine=[],
            startDir=Direction(0, 0),
            endDir=Direction(0, 0),
        ))

    subgraphs: List[AsciiSubgraph] = []
    for msg in parsed.subgraphs:
        convert_subgraph(msg, None, node_map, subgraphs)

    deduplicate_subgraph_nodes(parsed.subgraphs, subgraphs, node_map)

    for node_id, class_name in parsed.classAssignments.items():
        node = node_map.get(node_id)
        class_def = parsed.classDefs.get(class_name)
        if node and class_def:
            node.styleClassName = class_name
            node.styleClass = AsciiStyleClass(name=class_name, styles=class_def)

    return AsciiGraph(
        nodes=nodes,
        edges=edges,
        canvas=mk_canvas(0, 0),
        grid={},
        columnWidth={},
        rowHeight={},
        subgraphs=subgraphs,
        config=config,
        offsetX=0,
        offsetY=0,
    )


def convert_subgraph(m_sg: MermaidSubgraph, parent: Optional[AsciiSubgraph], node_map: Dict[str, AsciiNode], all_sgs: List[AsciiSubgraph]) -> AsciiSubgraph:
    sg = AsciiSubgraph(
        name=m_sg.label,
        nodes=[],
        parent=parent,
        children=[],
        direction=m_sg.direction,
        minX=0,
        minY=0,
        maxX=0,
        maxY=0,
    )
    for node_id in m_sg.nodeIds:
        node = node_map.get(node_id)
        if node:
            sg.nodes.append(node)

    all_sgs.append(sg)

    for child_m in m_sg.children:
        child = convert_subgraph(child_m, sg, node_map, all_sgs)
        sg.children.append(child)
        for child_node in child.nodes:
            if child_node not in sg.nodes:
                sg.nodes.append(child_node)

    return sg


def deduplicate_subgraph_nodes(mermaid_sgs: List[MermaidSubgraph], ascii_sgs: List[AsciiSubgraph], node_map: Dict[str, AsciiNode]) -> None:
    sg_map: Dict[int, AsciiSubgraph] = {}
    build_sg_map(mermaid_sgs, ascii_sgs, sg_map)

    node_owner: Dict[str, AsciiSubgraph] = {}

    def claim_nodes(m_sg: MermaidSubgraph) -> None:
        ascii_sg = sg_map.get(id(m_sg))
        if not ascii_sg:
            return
        for child in m_sg.children:
            claim_nodes(child)
        for node_id in m_sg.nodeIds:
            if node_id not in node_owner:
                node_owner[node_id] = ascii_sg

    for m_sg in mermaid_sgs:
        claim_nodes(m_sg)

    for ascii_sg in ascii_sgs:
        filtered: List[AsciiNode] = []
        for node in ascii_sg.nodes:
            node_id = None
            for nid, n in node_map.items():
                if n is node:
                    node_id = nid
                    break
            if not node_id:
                continue
            owner = node_owner.get(node_id)
            if not owner:
                filtered.append(node)
                continue
            if is_ancestor_or_self(ascii_sg, owner):
                filtered.append(node)
        ascii_sg.nodes = filtered


def is_ancestor_or_self(candidate: AsciiSubgraph, target: AsciiSubgraph) -> bool:
    current: Optional[AsciiSubgraph] = target
    while current is not None:
        if current is candidate:
            return True
        current = current.parent
    return False


def build_sg_map(m_sgs: List[MermaidSubgraph], a_sgs: List[AsciiSubgraph], result: Dict[int, AsciiSubgraph]) -> None:
    flat_mermaid: List[MermaidSubgraph] = []

    def flatten(sgs: List[MermaidSubgraph]) -> None:
        for sg in sgs:
            flat_mermaid.append(sg)
            flatten(sg.children)

    flatten(m_sgs)

    for i in range(min(len(flat_mermaid), len(a_sgs))):
        result[id(flat_mermaid[i])] = a_sgs[i]


# =============================================================================
# Pathfinder (A*)
# =============================================================================

@dataclass(order=True)
class PQItem:
    priority: int
    coord: GridCoord = field(compare=False)


class MinHeap:
    def __init__(self) -> None:
        self.items: List[PQItem] = []

    def __len__(self) -> int:
        return len(self.items)

    def push(self, item: PQItem) -> None:
        self.items.append(item)
        self._bubble_up(len(self.items) - 1)

    def pop(self) -> Optional[PQItem]:
        if not self.items:
            return None
        top = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            self._sink_down(0)
        return top

    def _bubble_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) >> 1
            if self.items[i].priority < self.items[parent].priority:
                self.items[i], self.items[parent] = self.items[parent], self.items[i]
                i = parent
            else:
                break

    def _sink_down(self, i: int) -> None:
        n = len(self.items)
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2
            if left < n and self.items[left].priority < self.items[smallest].priority:
                smallest = left
            if right < n and self.items[right].priority < self.items[smallest].priority:
                smallest = right
            if smallest != i:
                self.items[i], self.items[smallest] = self.items[smallest], self.items[i]
                i = smallest
            else:
                break


def heuristic(a: GridCoord, b: GridCoord) -> int:
    abs_x = abs(a.x - b.x)
    abs_y = abs(a.y - b.y)
    if abs_x == 0 or abs_y == 0:
        return abs_x + abs_y
    return abs_x + abs_y + 1


MOVE_DIRS = [GridCoord(1, 0), GridCoord(-1, 0), GridCoord(0, 1), GridCoord(0, -1)]


def is_free_in_grid(grid: Dict[str, AsciiNode], c: GridCoord) -> bool:
    if c.x < 0 or c.y < 0:
        return False
    return grid_key(c) not in grid


def get_path(grid: Dict[str, AsciiNode], frm: GridCoord, to: GridCoord) -> Optional[List[GridCoord]]:
    # Bound A* search space so impossible routes terminate quickly.
    dist = abs(frm.x - to.x) + abs(frm.y - to.y)
    margin = max(12, dist * 2)
    min_x = max(0, min(frm.x, to.x) - margin)
    max_x = max(frm.x, to.x) + margin
    min_y = max(0, min(frm.y, to.y) - margin)
    max_y = max(frm.y, to.y) + margin
    max_visited = 30000

    pq = MinHeap()
    pq.push(PQItem(priority=0, coord=frm))

    cost_so_far: Dict[str, int] = {grid_key(frm): 0}
    came_from: Dict[str, Optional[GridCoord]] = {grid_key(frm): None}
    visited = 0

    while len(pq) > 0:
        visited += 1
        if visited > max_visited:
            return None

        current = pq.pop().coord  # type: ignore[union-attr]
        if grid_coord_equals(current, to):
            path: List[GridCoord] = []
            c: Optional[GridCoord] = current
            while c is not None:
                path.insert(0, c)
                c = came_from.get(grid_key(c))
            return path

        current_cost = cost_so_far[grid_key(current)]

        for d in MOVE_DIRS:
            nxt = GridCoord(current.x + d.x, current.y + d.y)
            if nxt.x < min_x or nxt.x > max_x or nxt.y < min_y or nxt.y > max_y:
                continue
            if (not is_free_in_grid(grid, nxt)) and (not grid_coord_equals(nxt, to)):
                continue
            new_cost = current_cost + 1
            key = grid_key(nxt)
            existing = cost_so_far.get(key)
            if existing is None or new_cost < existing:
                cost_so_far[key] = new_cost
                priority = new_cost + heuristic(nxt, to)
                pq.push(PQItem(priority=priority, coord=nxt))
                came_from[key] = current

    return None


def merge_path(path: List[GridCoord]) -> List[GridCoord]:
    if len(path) <= 2:
        return path
    to_remove: set[int] = set()
    step0 = path[0]
    step1 = path[1]
    for idx in range(2, len(path)):
        step2 = path[idx]
        prev_dx = step1.x - step0.x
        prev_dy = step1.y - step0.y
        dx = step2.x - step1.x
        dy = step2.y - step1.y
        if prev_dx == dx and prev_dy == dy:
            to_remove.add(idx - 1)
        step0 = step1
        step1 = step2
    return [p for i, p in enumerate(path) if i not in to_remove]


# =============================================================================
# Edge routing
# =============================================================================

def dir_equals(a: Direction, b: Direction) -> bool:
    return a.x == b.x and a.y == b.y


def get_opposite(d: Direction) -> Direction:
    if dir_equals(d, Up):
        return Down
    if dir_equals(d, Down):
        return Up
    if dir_equals(d, Left):
        return Right
    if dir_equals(d, Right):
        return Left
    if dir_equals(d, UpperRight):
        return LowerLeft
    if dir_equals(d, UpperLeft):
        return LowerRight
    if dir_equals(d, LowerRight):
        return UpperLeft
    if dir_equals(d, LowerLeft):
        return UpperRight
    return Middle


def determine_direction(frm: GridCoord | DrawingCoord, to: GridCoord | DrawingCoord) -> Direction:
    if frm.x == to.x:
        return Down if frm.y < to.y else Up
    if frm.y == to.y:
        return Right if frm.x < to.x else Left
    if frm.x < to.x:
        return LowerRight if frm.y < to.y else UpperRight
    return LowerLeft if frm.y < to.y else UpperLeft


def self_reference_direction(graph_direction: str) -> Tuple[Direction, Direction, Direction, Direction]:
    if graph_direction == 'LR':
        return (Right, Down, Down, Right)
    return (Down, Right, Right, Down)


def determine_start_and_end_dir(edge: AsciiEdge, graph_direction: str) -> Tuple[Direction, Direction, Direction, Direction]:
    if edge.from_node is edge.to_node:
        return self_reference_direction(graph_direction)

    d = determine_direction(edge.from_node.gridCoord, edge.to_node.gridCoord)  # type: ignore[arg-type]

    is_backwards = (
        (graph_direction == 'LR' and (dir_equals(d, Left) or dir_equals(d, UpperLeft) or dir_equals(d, LowerLeft)))
        or (graph_direction == 'TD' and (dir_equals(d, Up) or dir_equals(d, UpperLeft) or dir_equals(d, UpperRight)))
    )

    if dir_equals(d, LowerRight):
        if graph_direction == 'LR':
            preferred_dir, preferred_opp = Down, Left
            alt_dir, alt_opp = Right, Up
        else:
            preferred_dir, preferred_opp = Right, Up
            alt_dir, alt_opp = Down, Left
    elif dir_equals(d, UpperRight):
        if graph_direction == 'LR':
            preferred_dir, preferred_opp = Up, Left
            alt_dir, alt_opp = Right, Down
        else:
            preferred_dir, preferred_opp = Right, Down
            alt_dir, alt_opp = Up, Left
    elif dir_equals(d, LowerLeft):
        if graph_direction == 'LR':
            preferred_dir, preferred_opp = Down, Down
            alt_dir, alt_opp = Left, Up
        else:
            preferred_dir, preferred_opp = Left, Up
            alt_dir, alt_opp = Down, Right
    elif dir_equals(d, UpperLeft):
        if graph_direction == 'LR':
            preferred_dir, preferred_opp = Down, Down
            alt_dir, alt_opp = Left, Down
        else:
            preferred_dir, preferred_opp = Right, Right
            alt_dir, alt_opp = Up, Right
    elif is_backwards:
        if graph_direction == 'LR' and dir_equals(d, Left):
            preferred_dir, preferred_opp = Down, Down
            alt_dir, alt_opp = Left, Right
        elif graph_direction == 'TD' and dir_equals(d, Up):
            preferred_dir, preferred_opp = Right, Right
            alt_dir, alt_opp = Up, Down
        else:
            preferred_dir = d
            preferred_opp = get_opposite(d)
            alt_dir = d
            alt_opp = get_opposite(d)
    else:
        preferred_dir = d
        preferred_opp = get_opposite(d)
        alt_dir = d
        alt_opp = get_opposite(d)

    return preferred_dir, preferred_opp, alt_dir, alt_opp


def determine_path(graph: AsciiGraph, edge: AsciiEdge) -> None:
    pref_dir, pref_opp, alt_dir, alt_opp = determine_start_and_end_dir(edge, graph.config.graphDirection)
    from_is_pseudo = edge.from_node.name.startswith(('_start', '_end')) and edge.from_node.displayLabel == ''
    to_is_pseudo = edge.to_node.name.startswith(('_start', '_end')) and edge.to_node.displayLabel == ''

    def unique_dirs(items: List[Direction]) -> List[Direction]:
        out: List[Direction] = []
        for d in items:
            if not any(dir_equals(d, e) for e in out):
                out.append(d)
        return out

    def fanout_start_dirs() -> List[Direction]:
        outgoing = [e for e in graph.edges if e.from_node is edge.from_node and e.to_node.gridCoord is not None]
        if from_is_pseudo:
            return unique_dirs([pref_dir, alt_dir, Down, Right, Left, Up])
        if len(outgoing) <= 1:
            return unique_dirs([pref_dir, alt_dir, Down, Right, Left, Up])

        if graph.config.graphDirection == 'TD':
            ordered = sorted(outgoing, key=lambda e: (e.to_node.gridCoord.x, e.to_node.gridCoord.y))
            idx = ordered.index(edge)
            if len(ordered) == 2:
                fanout = [Down, Right]
            else:
                fanout = [Down, Left, Right]
                if idx >= len(fanout):
                    idx = len(fanout) - 1
            primary = fanout[idx if len(ordered) > 2 else idx]
            return unique_dirs([primary, pref_dir, alt_dir, Down, Left, Right, Up])

        ordered = sorted(outgoing, key=lambda e: (e.to_node.gridCoord.y, e.to_node.gridCoord.x))
        idx = ordered.index(edge)
        if len(ordered) == 2:
            fanout = [Up, Down]
        else:
            fanout = [Up, Right, Down]
            if idx >= len(fanout):
                idx = len(fanout) - 1
        primary = fanout[idx if len(ordered) > 2 else idx]
        return unique_dirs([primary, pref_dir, alt_dir, Right, Up, Down, Left])

    def fanin_end_dirs() -> List[Direction]:
        incoming = [e for e in graph.edges if e.to_node is edge.to_node and e.from_node.gridCoord is not None]
        if to_is_pseudo:
            return unique_dirs([pref_opp, alt_opp, Up, Left, Right, Down])
        if len(incoming) <= 1:
            return unique_dirs([pref_opp, alt_opp, Up, Left, Right, Down])

        if graph.config.graphDirection == 'TD':
            ordered = sorted(incoming, key=lambda e: (e.from_node.gridCoord.x, e.from_node.gridCoord.y))
            idx = ordered.index(edge)
            if len(ordered) == 2:
                fanin = [Left, Right]
            else:
                fanin = [Left, Up, Right]
                if idx >= len(fanin):
                    idx = len(fanin) - 1
            primary = fanin[idx if len(ordered) > 2 else idx]
            return unique_dirs([primary, pref_opp, alt_opp, Up, Left, Right, Down])

        ordered = sorted(incoming, key=lambda e: (e.from_node.gridCoord.y, e.from_node.gridCoord.x))
        idx = ordered.index(edge)
        if len(ordered) == 2:
            fanin = [Up, Down]
        else:
            fanin = [Up, Left, Down]
            if idx >= len(fanin):
                idx = len(fanin) - 1
        primary = fanin[idx if len(ordered) > 2 else idx]
        return unique_dirs([primary, pref_opp, alt_opp, Left, Up, Down, Right])

    def path_keys(path: List[GridCoord]) -> set[str]:
        if len(path) <= 2:
            return set()
        return {grid_key(p) for p in path[1:-1]}

    def overlap_penalty(candidate: List[GridCoord], sdir: Direction) -> int:
        me = path_keys(candidate)
        if not me:
            return 0
        penalty = 0
        # Prefer fan-out direction consistent with target side.
        if graph.config.graphDirection == 'TD':
            dx = edge.to_node.gridCoord.x - edge.from_node.gridCoord.x
            if dx > 0 and dir_equals(sdir, Left):
                penalty += 50
            elif dx < 0 and dir_equals(sdir, Right):
                penalty += 50
            elif dx == 0 and not dir_equals(sdir, Down):
                penalty += 10
        else:
            dy = edge.to_node.gridCoord.y - edge.from_node.gridCoord.y
            if dy > 0 and dir_equals(sdir, Up):
                penalty += 50
            elif dy < 0 and dir_equals(sdir, Down):
                penalty += 50
            elif dy == 0 and not dir_equals(sdir, Right):
                penalty += 10

        for other in graph.edges:
            if other is edge or not other.path:
                continue
            inter = me & path_keys(other.path)
            if inter:
                penalty += 100 * len(inter)
            # Strongly discourage using the same start side for sibling fan-out.
            if other.from_node is edge.from_node and dir_equals(other.startDir, sdir):
                penalty += 20

            # Avoid building a knot near the source by sharing early trunk cells.
            if other.from_node is edge.from_node and len(candidate) > 2 and len(other.path) > 2:
                minear = {grid_key(p) for p in candidate[:3]}
                otherear = {grid_key(p) for p in other.path[:3]}
                trunk = minear & otherear
                if trunk:
                    penalty += 60 * len(trunk)
        return penalty

    def bend_count(path: List[GridCoord]) -> int:
        if len(path) < 3:
            return 0
        bends = 0
        prev = determine_direction(path[0], path[1])
        for i in range(2, len(path)):
            cur = determine_direction(path[i - 1], path[i])
            if not dir_equals(cur, prev):
                bends += 1
            prev = cur
        return bends

    start_dirs = fanout_start_dirs()
    end_dirs = fanin_end_dirs()

    candidates: List[Tuple[int, int, Direction, Direction, List[GridCoord]]] = []
    fallback_candidates: List[Tuple[int, int, Direction, Direction, List[GridCoord]]] = []
    seen: set[Tuple[str, str, str]] = set()
    for sdir in start_dirs:
        for edir in end_dirs:
            frm = grid_coord_direction(edge.from_node.gridCoord, sdir)
            to = grid_coord_direction(edge.to_node.gridCoord, edir)
            p = get_path(graph.grid, frm, to)
            if p is None:
                continue
            merged = merge_path(p)
            key = (f"{sdir.x}:{sdir.y}", f"{edir.x}:{edir.y}", ",".join(grid_key(x) for x in merged))
            if key in seen:
                continue
            seen.add(key)
            scored = (overlap_penalty(merged, sdir), len(merged), sdir, edir, merged)
            if len(merged) >= 2:
                candidates.append(scored)
            else:
                fallback_candidates.append(scored)

    if not candidates:
        if fallback_candidates:
            fallback_candidates.sort(key=lambda x: (x[0], x[1]))
            _, _, sdir, edir, best = fallback_candidates[0]
            if len(best) == 1:
                # Last resort: create a tiny dogleg to avoid a zero-length rendered edge.
                p0 = best[0]
                dirs = [sdir, edir, Down, Right, Left, Up]
                for d in dirs:
                    n = GridCoord(p0.x + d.x, p0.y + d.y)
                    if n.x < 0 or n.y < 0:
                        continue
                    if is_free_in_grid(graph.grid, n):
                        best = [p0, n, p0]
                        break
            edge.startDir = sdir
            edge.endDir = edir
            edge.path = best
            return
        edge.startDir = alt_dir
        edge.endDir = alt_opp
        edge.path = []
        return

    candidates.sort(key=lambda x: (x[0], bend_count(x[4]), x[1]))
    _, _, sdir, edir, best = candidates[0]
    edge.startDir = sdir
    edge.endDir = edir
    edge.path = best


def determine_label_line(graph: AsciiGraph, edge: AsciiEdge) -> None:
    if not edge.text:
        return

    len_label = len(edge.text)
    prev_step = edge.path[0]
    largest_line = [prev_step, edge.path[1]]
    largest_line_size = 0

    for i in range(1, len(edge.path)):
        step = edge.path[i]
        line = [prev_step, step]
        line_width = calculate_line_width(graph, line)

        if line_width >= len_label:
            largest_line = line
            break
        elif line_width > largest_line_size:
            largest_line_size = line_width
            largest_line = line
        prev_step = step

    min_x = min(largest_line[0].x, largest_line[1].x)
    max_x = max(largest_line[0].x, largest_line[1].x)
    middle_x = min_x + (max_x - min_x) // 2

    current = graph.columnWidth.get(middle_x, 0)
    graph.columnWidth[middle_x] = max(current, len_label + 2)

    edge.labelLine = [largest_line[0], largest_line[1]]


def calculate_line_width(graph: AsciiGraph, line: List[GridCoord]) -> int:
    total = 0
    start_x = min(line[0].x, line[1].x)
    end_x = max(line[0].x, line[1].x)
    for x in range(start_x, end_x + 1):
        total += graph.columnWidth.get(x, 0)
    return total


# =============================================================================
# Grid layout
# =============================================================================

def grid_to_drawing_coord(graph: AsciiGraph, c: GridCoord, d: Optional[Direction] = None) -> DrawingCoord:
    target = GridCoord(c.x + d.x, c.y + d.y) if d else c

    x = 0
    for col in range(target.x):
        x += graph.columnWidth.get(col, 0)

    y = 0
    for row in range(target.y):
        y += graph.rowHeight.get(row, 0)

    col_w = graph.columnWidth.get(target.x, 0)
    row_h = graph.rowHeight.get(target.y, 0)
    return DrawingCoord(
        x=x + (col_w // 2) + graph.offsetX,
        y=y + (row_h // 2) + graph.offsetY,
    )


def line_to_drawing(graph: AsciiGraph, line: List[GridCoord]) -> List[DrawingCoord]:
    return [grid_to_drawing_coord(graph, c) for c in line]


def reserve_spot_in_grid(graph: AsciiGraph, node: AsciiNode, requested: GridCoord) -> GridCoord:
    is_pseudo = node.name.startswith(('_start', '_end')) and node.displayLabel == ''
    footprint = [(0, 0)] if is_pseudo else [(dx, dy) for dx in range(3) for dy in range(3)]

    def can_place(at: GridCoord) -> bool:
        for dx, dy in footprint:
            key = grid_key(GridCoord(at.x + dx, at.y + dy))
            if key in graph.grid:
                return False
        return True

    if not can_place(requested):
        if graph.config.graphDirection == 'LR':
            return reserve_spot_in_grid(graph, node, GridCoord(requested.x, requested.y + 4))
        return reserve_spot_in_grid(graph, node, GridCoord(requested.x + 4, requested.y))

    for dx, dy in footprint:
        reserved = GridCoord(requested.x + dx, requested.y + dy)
        graph.grid[grid_key(reserved)] = node

    node.gridCoord = requested
    return requested


def has_incoming_edge_from_outside_subgraph(graph: AsciiGraph, node: AsciiNode) -> bool:
    node_sg = get_node_subgraph(graph, node)
    if not node_sg:
        return False

    has_external = False
    for edge in graph.edges:
        if edge.to_node is node:
            source_sg = get_node_subgraph(graph, edge.from_node)
            if source_sg is not node_sg:
                has_external = True
                break
    if not has_external:
        return False

    for other in node_sg.nodes:
        if other is node or not other.gridCoord:
            continue
        other_has_external = False
        for edge in graph.edges:
            if edge.to_node is other:
                source_sg = get_node_subgraph(graph, edge.from_node)
                if source_sg is not node_sg:
                    other_has_external = True
                    break
        if other_has_external and other.gridCoord.y < node.gridCoord.y:
            return False

    return True


def set_column_width(graph: AsciiGraph, node: AsciiNode) -> None:
    gc = node.gridCoord
    padding = graph.config.boxBorderPadding
    col_widths = [1, 2 * padding + len(node.displayLabel), 1]
    row_heights = [1, 1 + 2 * padding, 1]

    for idx, w in enumerate(col_widths):
        x_coord = gc.x + idx
        current = graph.columnWidth.get(x_coord, 0)
        graph.columnWidth[x_coord] = max(current, w)

    for idx, h in enumerate(row_heights):
        y_coord = gc.y + idx
        current = graph.rowHeight.get(y_coord, 0)
        graph.rowHeight[y_coord] = max(current, h)

    if gc.x > 0:
        current = graph.columnWidth.get(gc.x - 1, 0)
        graph.columnWidth[gc.x - 1] = max(current, graph.config.paddingX)

    if gc.y > 0:
        base_padding = graph.config.paddingY
        if has_incoming_edge_from_outside_subgraph(graph, node):
            base_padding += 4
        current = graph.rowHeight.get(gc.y - 1, 0)
        graph.rowHeight[gc.y - 1] = max(current, base_padding)


def increase_grid_size_for_path(graph: AsciiGraph, path: List[GridCoord]) -> None:
    # Keep path-only spacer rows/cols present but compact.
    path_pad_x = max(1, (graph.config.paddingX + 1) // 3)
    path_pad_y = max(1, graph.config.paddingY // 3)
    for c in path:
        if c.x not in graph.columnWidth:
            graph.columnWidth[c.x] = path_pad_x
        if c.y not in graph.rowHeight:
            graph.rowHeight[c.y] = path_pad_y


def is_node_in_any_subgraph(graph: AsciiGraph, node: AsciiNode) -> bool:
    return any(node in sg.nodes for sg in graph.subgraphs)


def get_node_subgraph(graph: AsciiGraph, node: AsciiNode) -> Optional[AsciiSubgraph]:
    best: Optional[AsciiSubgraph] = None
    best_depth = -1
    for sg in graph.subgraphs:
        if node in sg.nodes:
            depth = 0
            cur = sg.parent
            while cur is not None:
                depth += 1
                cur = cur.parent
            if depth > best_depth:
                best_depth = depth
                best = sg
    return best


def calculate_subgraph_bounding_box(graph: AsciiGraph, sg: AsciiSubgraph) -> None:
    if not sg.nodes:
        return
    min_x = 1_000_000
    min_y = 1_000_000
    max_x = -1_000_000
    max_y = -1_000_000

    for child in sg.children:
        calculate_subgraph_bounding_box(graph, child)
        if child.nodes:
            min_x = min(min_x, child.minX)
            min_y = min(min_y, child.minY)
            max_x = max(max_x, child.maxX)
            max_y = max(max_y, child.maxY)

    for node in sg.nodes:
        if node.name.startswith(('_start', '_end')) and node.displayLabel == '':
            continue
        if not node.drawingCoord or not node.drawing:
            continue
        node_min_x = node.drawingCoord.x
        node_min_y = node.drawingCoord.y
        node_max_x = node_min_x + len(node.drawing) - 1
        node_max_y = node_min_y + len(node.drawing[0]) - 1
        min_x = min(min_x, node_min_x)
        min_y = min(min_y, node_min_y)
        max_x = max(max_x, node_max_x)
        max_y = max(max_y, node_max_y)

    # Composite/state groups looked too loose with larger margins.
    subgraph_padding = 1
    subgraph_label_space = 1
    sg.minX = min_x - subgraph_padding
    sg.minY = min_y - subgraph_padding - subgraph_label_space
    sg.maxX = max_x + subgraph_padding
    sg.maxY = max_y + subgraph_padding


def ensure_subgraph_spacing(graph: AsciiGraph) -> None:
    min_spacing = 1
    root_sgs = [sg for sg in graph.subgraphs if sg.parent is None and sg.nodes]

    for i in range(len(root_sgs)):
        for j in range(i + 1, len(root_sgs)):
            sg1 = root_sgs[i]
            sg2 = root_sgs[j]

            if sg1.minX < sg2.maxX and sg1.maxX > sg2.minX:
                if sg1.maxY >= sg2.minY - min_spacing and sg1.minY < sg2.minY:
                    sg2.minY = sg1.maxY + min_spacing + 1
                elif sg2.maxY >= sg1.minY - min_spacing and sg2.minY < sg1.minY:
                    sg1.minY = sg2.maxY + min_spacing + 1

            if sg1.minY < sg2.maxY and sg1.maxY > sg2.minY:
                if sg1.maxX >= sg2.minX - min_spacing and sg1.minX < sg2.minX:
                    sg2.minX = sg1.maxX + min_spacing + 1
                elif sg2.maxX >= sg1.minX - min_spacing and sg2.minX < sg1.minX:
                    sg1.minX = sg2.maxX + min_spacing + 1


def calculate_subgraph_bounding_boxes(graph: AsciiGraph) -> None:
    for sg in graph.subgraphs:
        calculate_subgraph_bounding_box(graph, sg)
    ensure_subgraph_spacing(graph)


def offset_drawing_for_subgraphs(graph: AsciiGraph) -> None:
    if not graph.subgraphs:
        return
    min_x = 0
    min_y = 0
    for sg in graph.subgraphs:
        min_x = min(min_x, sg.minX)
        min_y = min(min_y, sg.minY)
    offset_x = -min_x
    offset_y = -min_y
    if offset_x == 0 and offset_y == 0:
        return
    graph.offsetX = offset_x
    graph.offsetY = offset_y
    for sg in graph.subgraphs:
        sg.minX += offset_x
        sg.minY += offset_y
        sg.maxX += offset_x
        sg.maxY += offset_y
    for node in graph.nodes:
        if node.drawingCoord:
            node.drawingCoord = DrawingCoord(node.drawingCoord.x + offset_x, node.drawingCoord.y + offset_y)


def create_mapping(graph: AsciiGraph) -> None:
    dirn = graph.config.graphDirection
    highest_position_per_level = [0] * 100
    # Reserve one leading lane so pseudo start/end markers can sit before roots.
    highest_position_per_level[0] = 4

    def is_pseudo_state_node(node: AsciiNode) -> bool:
        return node.name.startswith(('_start', '_end')) and node.displayLabel == ''

    def effective_dir_for_nodes(a: AsciiNode, b: AsciiNode) -> str:
        a_sg = get_node_subgraph(graph, a)
        b_sg = get_node_subgraph(graph, b)
        if a_sg and b_sg and a_sg is b_sg and a_sg.direction:
            return 'LR' if a_sg.direction in ('LR', 'RL') else 'TD'
        return dirn

    nodes_found: set[str] = set()
    root_nodes: List[AsciiNode] = []

    for node in graph.nodes:
        if is_pseudo_state_node(node):
            # Pseudo state markers should not influence root discovery.
            continue
        if node.name not in nodes_found:
            root_nodes.append(node)
        nodes_found.add(node.name)
        for child in get_children(graph, node):
            if not is_pseudo_state_node(child):
                nodes_found.add(child.name)

    has_external_roots = False
    has_subgraph_roots_with_edges = False
    for node in root_nodes:
        if is_node_in_any_subgraph(graph, node):
            if get_children(graph, node):
                has_subgraph_roots_with_edges = True
        else:
            has_external_roots = True
    should_separate = (has_external_roots and has_subgraph_roots_with_edges)

    if should_separate:
        external_roots = [n for n in root_nodes if not is_node_in_any_subgraph(graph, n)]
        subgraph_roots = [n for n in root_nodes if is_node_in_any_subgraph(graph, n)]
    else:
        external_roots = root_nodes
        subgraph_roots = []

    for node in external_roots:
        requested = GridCoord(0, highest_position_per_level[0]) if dirn == 'LR' else GridCoord(highest_position_per_level[0], 4)
        reserve_spot_in_grid(graph, graph.nodes[node.index], requested)
        highest_position_per_level[0] += 4

    if should_separate and subgraph_roots:
        subgraph_level = 4 if dirn == 'LR' else 10
        for node in subgraph_roots:
            requested = GridCoord(subgraph_level, highest_position_per_level[subgraph_level]) if dirn == 'LR' else GridCoord(highest_position_per_level[subgraph_level], subgraph_level)
            reserve_spot_in_grid(graph, graph.nodes[node.index], requested)
            highest_position_per_level[subgraph_level] += 4

    # Expand parent -> child placement until no additional nodes can be placed.
    for _ in range(len(graph.nodes) + 2):
        changed = False
        for node in graph.nodes:
            if node.gridCoord is None:
                continue
            gc = node.gridCoord
            for child in get_children(graph, node):
                if child.gridCoord is not None:
                    continue
                effective_dir = effective_dir_for_nodes(node, child)
                child_level = gc.x + 4 if effective_dir == 'LR' else gc.y + 4
                base_position = gc.y if effective_dir == 'LR' else gc.x
                highest_position = max(highest_position_per_level[child_level], base_position)
                requested = GridCoord(child_level, highest_position) if effective_dir == 'LR' else GridCoord(highest_position, child_level)
                reserve_spot_in_grid(graph, graph.nodes[child.index], requested)
                highest_position_per_level[child_level] = highest_position + 4
                changed = True
        if not changed:
            break

    # Place pseudo state markers close to connected nodes instead of as global roots.
    for _ in range(len(graph.nodes) + 2):
        changed = False
        for node in graph.nodes:
            if node.gridCoord is not None or not is_pseudo_state_node(node):
                continue

            outgoing = [e.to_node for e in graph.edges if e.from_node is node and e.to_node.gridCoord is not None]
            incoming = [e.from_node for e in graph.edges if e.to_node is node and e.from_node.gridCoord is not None]
            anchor = outgoing[0] if outgoing else (incoming[0] if incoming else None)
            if anchor is None:
                continue

            eff_dir = effective_dir_for_nodes(node, anchor)
            if node.name.startswith('_start') and outgoing:
                if eff_dir == 'LR':
                    requested = GridCoord(max(0, anchor.gridCoord.x - 2), anchor.gridCoord.y)
                else:
                    requested = GridCoord(anchor.gridCoord.x, max(0, anchor.gridCoord.y - 2))
            elif node.name.startswith('_end') and incoming:
                if eff_dir == 'LR':
                    requested = GridCoord(anchor.gridCoord.x + 2, anchor.gridCoord.y)
                else:
                    requested = GridCoord(anchor.gridCoord.x, anchor.gridCoord.y + 2)
            else:
                if eff_dir == 'LR':
                    requested = GridCoord(max(0, anchor.gridCoord.x - 2), anchor.gridCoord.y)
                else:
                    requested = GridCoord(anchor.gridCoord.x, max(0, anchor.gridCoord.y - 2))

            reserve_spot_in_grid(graph, graph.nodes[node.index], requested)
            changed = True
        if not changed:
            break

    # Fallback for any remaining unplaced nodes (isolated/cyclic leftovers).
    for node in graph.nodes:
        if node.gridCoord is not None:
            continue
        requested = GridCoord(0, highest_position_per_level[0]) if dirn == 'LR' else GridCoord(highest_position_per_level[0], 4)
        reserve_spot_in_grid(graph, graph.nodes[node.index], requested)
        highest_position_per_level[0] += 4

    for node in graph.nodes:
        set_column_width(graph, node)

    # Route edges, then reroute with global context to reduce crossings/overlaps.
    for edge in graph.edges:
        determine_path(graph, edge)
    for _ in range(2):
        for edge in graph.edges:
            determine_path(graph, edge)

    for edge in graph.edges:
        increase_grid_size_for_path(graph, edge.path)
        determine_label_line(graph, edge)

    for node in graph.nodes:
        node.drawingCoord = grid_to_drawing_coord(graph, node.gridCoord)
        node.drawing = draw_box(node, graph)

    set_canvas_size_to_grid(graph.canvas, graph.columnWidth, graph.rowHeight)
    calculate_subgraph_bounding_boxes(graph)
    offset_drawing_for_subgraphs(graph)


def get_edges_from_node(graph: AsciiGraph, node: AsciiNode) -> List[AsciiEdge]:
    return [e for e in graph.edges if e.from_node.name == node.name]


def get_children(graph: AsciiGraph, node: AsciiNode) -> List[AsciiNode]:
    return [e.to_node for e in get_edges_from_node(graph, node)]


# =============================================================================
# Draw
# =============================================================================

def draw_box(node: AsciiNode, graph: AsciiGraph) -> Canvas:
    gc = node.gridCoord
    use_ascii = graph.config.useAscii

    w = 0
    for i in range(2):
        w += graph.columnWidth.get(gc.x + i, 0)
    h = 0
    for i in range(2):
        h += graph.rowHeight.get(gc.y + i, 0)

    frm = DrawingCoord(0, 0)
    to = DrawingCoord(w, h)
    box = mk_canvas(max(frm.x, to.x), max(frm.y, to.y))

    is_pseudo = node.name.startswith(('_start', '_end')) and node.displayLabel == ''

    if is_pseudo:
        dot = mk_canvas(0, 0)
        dot[0][0] = '*' if use_ascii else '●'
        return dot

    if not use_ascii:
        for x in range(frm.x + 1, to.x):
            box[x][frm.y] = '─'
            box[x][to.y] = '─'
        for y in range(frm.y + 1, to.y):
            box[frm.x][y] = '│'
            box[to.x][y] = '│'
        box[frm.x][frm.y] = '┌'
        box[to.x][frm.y] = '┐'
        box[frm.x][to.y] = '└'
        box[to.x][to.y] = '┘'
    else:
        for x in range(frm.x + 1, to.x):
            box[x][frm.y] = '-'
            box[x][to.y] = '-'
        for y in range(frm.y + 1, to.y):
            box[frm.x][y] = '|'
            box[to.x][y] = '|'
        box[frm.x][frm.y] = '+'
        box[to.x][frm.y] = '+'
        box[frm.x][to.y] = '+'
        box[to.x][to.y] = '+'

    label = node.displayLabel
    text_y = frm.y + (h // 2)
    text_x = frm.x + (w // 2) - ((len(label) + 1) // 2) + 1
    for i, ch in enumerate(label):
        box[text_x + i][text_y] = ch

    return box


def draw_multi_box(sections: List[List[str]], use_ascii: bool, padding: int = 1) -> Canvas:
    max_text = 0
    for section in sections:
        for line in section:
            max_text = max(max_text, len(line))
    inner_width = max_text + 2 * padding
    box_width = inner_width + 2

    total_lines = 0
    for section in sections:
        total_lines += max(len(section), 1)
    num_dividers = len(sections) - 1
    box_height = total_lines + num_dividers + 2

    hline = '-' if use_ascii else '─'
    vline = '|' if use_ascii else '│'
    tl = '+' if use_ascii else '┌'
    tr = '+' if use_ascii else '┐'
    bl = '+' if use_ascii else '└'
    br = '+' if use_ascii else '┘'
    div_l = '+' if use_ascii else '├'
    div_r = '+' if use_ascii else '┤'

    canvas = mk_canvas(box_width - 1, box_height - 1)

    canvas[0][0] = tl
    for x in range(1, box_width - 1):
        canvas[x][0] = hline
    canvas[box_width - 1][0] = tr

    canvas[0][box_height - 1] = bl
    for x in range(1, box_width - 1):
        canvas[x][box_height - 1] = hline
    canvas[box_width - 1][box_height - 1] = br

    for y in range(1, box_height - 1):
        canvas[0][y] = vline
        canvas[box_width - 1][y] = vline

    row = 1
    for s_idx, section in enumerate(sections):
        lines = section if section else ['']
        for line in lines:
            start_x = 1 + padding
            for i, ch in enumerate(line):
                canvas[start_x + i][row] = ch
            row += 1
        if s_idx < len(sections) - 1:
            canvas[0][row] = div_l
            for x in range(1, box_width - 1):
                canvas[x][row] = hline
            canvas[box_width - 1][row] = div_r
            row += 1

    return canvas


def draw_line(canvas: Canvas, frm: DrawingCoord, to: DrawingCoord, offset_from: int, offset_to: int, use_ascii: bool) -> List[DrawingCoord]:
    dirn = determine_direction(frm, to)
    drawn: List[DrawingCoord] = []

    h_char = '-' if use_ascii else '─'
    v_char = '|' if use_ascii else '│'
    bslash = '\\' if use_ascii else '╲'
    fslash = '/' if use_ascii else '╱'

    if dir_equals(dirn, Up):
        for y in range(frm.y - offset_from, to.y - offset_to - 1, -1):
            drawn.append(DrawingCoord(frm.x, y))
            canvas[frm.x][y] = v_char
    elif dir_equals(dirn, Down):
        for y in range(frm.y + offset_from, to.y + offset_to + 1):
            drawn.append(DrawingCoord(frm.x, y))
            canvas[frm.x][y] = v_char
    elif dir_equals(dirn, Left):
        for x in range(frm.x - offset_from, to.x - offset_to - 1, -1):
            drawn.append(DrawingCoord(x, frm.y))
            canvas[x][frm.y] = h_char
    elif dir_equals(dirn, Right):
        for x in range(frm.x + offset_from, to.x + offset_to + 1):
            drawn.append(DrawingCoord(x, frm.y))
            canvas[x][frm.y] = h_char
    elif dir_equals(dirn, UpperLeft):
        x = frm.x
        y = frm.y - offset_from
        while x >= to.x - offset_to and y >= to.y - offset_to:
            drawn.append(DrawingCoord(x, y))
            canvas[x][y] = bslash
            x -= 1
            y -= 1
    elif dir_equals(dirn, UpperRight):
        x = frm.x
        y = frm.y - offset_from
        while x <= to.x + offset_to and y >= to.y - offset_to:
            drawn.append(DrawingCoord(x, y))
            canvas[x][y] = fslash
            x += 1
            y -= 1
    elif dir_equals(dirn, LowerLeft):
        x = frm.x
        y = frm.y + offset_from
        while x >= to.x - offset_to and y <= to.y + offset_to:
            drawn.append(DrawingCoord(x, y))
            canvas[x][y] = fslash
            x -= 1
            y += 1
    elif dir_equals(dirn, LowerRight):
        x = frm.x
        y = frm.y + offset_from
        while x <= to.x + offset_to and y <= to.y + offset_to:
            drawn.append(DrawingCoord(x, y))
            canvas[x][y] = bslash
            x += 1
            y += 1

    return drawn


def draw_arrow(graph: AsciiGraph, edge: AsciiEdge) -> Tuple[Canvas, Canvas, Canvas, Canvas, Canvas]:
    if not edge.path:
        empty = copy_canvas(graph.canvas)
        return empty, empty, empty, empty, empty

    label_canvas = draw_arrow_label(graph, edge)
    path_canvas, lines_drawn, line_dirs = draw_path(graph, edge, edge.path)
    if not lines_drawn or not line_dirs:
        empty = copy_canvas(graph.canvas)
        return path_canvas, empty, empty, empty, label_canvas
    from_is_pseudo = edge.from_node.name.startswith(('_start', '_end')) and edge.from_node.displayLabel == ''
    from_out_degree = len(get_edges_from_node(graph, edge.from_node))
    # Junction marks on dense fan-out nodes quickly turn into unreadable knots.
    if from_is_pseudo or from_out_degree > 1:
        box_start_canvas = copy_canvas(graph.canvas)
    else:
        box_start_canvas = draw_box_start(graph, edge.path, lines_drawn[0])
    arrow_head_canvas = draw_arrow_head(graph, lines_drawn[-1], line_dirs[-1])
    corners_canvas = draw_corners(graph, edge.path)

    return path_canvas, box_start_canvas, arrow_head_canvas, corners_canvas, label_canvas


def draw_path(graph: AsciiGraph, edge: AsciiEdge, path: List[GridCoord]) -> Tuple[Canvas, List[List[DrawingCoord]], List[Direction]]:
    canvas = copy_canvas(graph.canvas)
    previous = path[0]
    lines_drawn: List[List[DrawingCoord]] = []
    line_dirs: List[Direction] = []

    def border_coord(node: AsciiNode, side: Direction, lane: DrawingCoord) -> DrawingCoord:
        left = node.drawingCoord.x
        top = node.drawingCoord.y
        width = len(node.drawing)
        height = len(node.drawing[0])
        cx = left + width // 2
        cy = top + height // 2
        if dir_equals(side, Left):
            return DrawingCoord(left, lane.y)
        if dir_equals(side, Right):
            return DrawingCoord(left + width - 1, lane.y)
        if dir_equals(side, Up):
            return DrawingCoord(lane.x, top)
        if dir_equals(side, Down):
            return DrawingCoord(lane.x, top + height - 1)
        return DrawingCoord(cx, cy)

    for i in range(1, len(path)):
        next_coord = path[i]
        prev_dc = grid_to_drawing_coord(graph, previous)
        next_dc = grid_to_drawing_coord(graph, next_coord)
        if drawing_coord_equals(prev_dc, next_dc):
            previous = next_coord
            continue
        dirn = determine_direction(previous, next_coord)

        is_first = (i == 1)
        is_last = (i == len(path) - 1)

        if is_first:
            node = graph.grid.get(grid_key(previous))
            if node and node.drawingCoord and node.drawing:
                prev_dc = border_coord(node, dirn, prev_dc)
        if is_last:
            node = graph.grid.get(grid_key(next_coord))
            if node and node.drawingCoord and node.drawing:
                next_dc = border_coord(node, get_opposite(dirn), next_dc)

        offset_from = 0 if is_first else 1
        offset_to = 0 if is_last else -1
        segment = draw_line(canvas, prev_dc, next_dc, offset_from, offset_to, graph.config.useAscii)
        if not segment:
            segment.append(prev_dc)
        lines_drawn.append(segment)
        line_dirs.append(dirn)
        previous = next_coord

    return canvas, lines_drawn, line_dirs


def draw_box_start(graph: AsciiGraph, path: List[GridCoord], first_line: List[DrawingCoord]) -> Canvas:
    canvas = copy_canvas(graph.canvas)
    if graph.config.useAscii:
        return canvas

    frm = first_line[0]
    dirn = determine_direction(path[0], path[1])

    if dir_equals(dirn, Up):
        canvas[frm.x][frm.y] = '┴'
    elif dir_equals(dirn, Down):
        canvas[frm.x][frm.y] = '┬'
    elif dir_equals(dirn, Left):
        canvas[frm.x][frm.y] = '┤'
    elif dir_equals(dirn, Right):
        canvas[frm.x][frm.y] = '├'

    return canvas


def draw_arrow_head(graph: AsciiGraph, last_line: List[DrawingCoord], fallback_dir: Direction) -> Canvas:
    canvas = copy_canvas(graph.canvas)
    if not last_line:
        return canvas

    frm = last_line[0]
    last_pos = last_line[-1]
    dirn = determine_direction(frm, last_pos)
    if len(last_line) == 1 or dir_equals(dirn, Middle):
        dirn = fallback_dir

    if not graph.config.useAscii:
        if dir_equals(dirn, Up):
            ch = '▲'
        elif dir_equals(dirn, Down):
            ch = '▼'
        elif dir_equals(dirn, Left):
            ch = '◄'
        elif dir_equals(dirn, Right):
            ch = '►'
        elif dir_equals(dirn, UpperRight):
            ch = '◥'
        elif dir_equals(dirn, UpperLeft):
            ch = '◤'
        elif dir_equals(dirn, LowerRight):
            ch = '◢'
        elif dir_equals(dirn, LowerLeft):
            ch = '◣'
        else:
            if dir_equals(fallback_dir, Up):
                ch = '▲'
            elif dir_equals(fallback_dir, Down):
                ch = '▼'
            elif dir_equals(fallback_dir, Left):
                ch = '◄'
            elif dir_equals(fallback_dir, Right):
                ch = '►'
            elif dir_equals(fallback_dir, UpperRight):
                ch = '◥'
            elif dir_equals(fallback_dir, UpperLeft):
                ch = '◤'
            elif dir_equals(fallback_dir, LowerRight):
                ch = '◢'
            elif dir_equals(fallback_dir, LowerLeft):
                ch = '◣'
            else:
                ch = '●'
    else:
        if dir_equals(dirn, Up):
            ch = '^'
        elif dir_equals(dirn, Down):
            ch = 'v'
        elif dir_equals(dirn, Left):
            ch = '<'
        elif dir_equals(dirn, Right):
            ch = '>'
        else:
            if dir_equals(fallback_dir, Up):
                ch = '^'
            elif dir_equals(fallback_dir, Down):
                ch = 'v'
            elif dir_equals(fallback_dir, Left):
                ch = '<'
            elif dir_equals(fallback_dir, Right):
                ch = '>'
            else:
                ch = '*'

    canvas[last_pos.x][last_pos.y] = ch
    return canvas


def draw_corners(graph: AsciiGraph, path: List[GridCoord]) -> Canvas:
    canvas = copy_canvas(graph.canvas)
    for idx in range(1, len(path) - 1):
        coord = path[idx]
        dc = grid_to_drawing_coord(graph, coord)
        prev_dir = determine_direction(path[idx - 1], coord)
        next_dir = determine_direction(coord, path[idx + 1])

        if not graph.config.useAscii:
            if (dir_equals(prev_dir, Right) and dir_equals(next_dir, Down)) or (dir_equals(prev_dir, Up) and dir_equals(next_dir, Left)):
                corner = '┐'
            elif (dir_equals(prev_dir, Right) and dir_equals(next_dir, Up)) or (dir_equals(prev_dir, Down) and dir_equals(next_dir, Left)):
                corner = '┘'
            elif (dir_equals(prev_dir, Left) and dir_equals(next_dir, Down)) or (dir_equals(prev_dir, Up) and dir_equals(next_dir, Right)):
                corner = '┌'
            elif (dir_equals(prev_dir, Left) and dir_equals(next_dir, Up)) or (dir_equals(prev_dir, Down) and dir_equals(next_dir, Right)):
                corner = '└'
            else:
                corner = '+'
        else:
            corner = '+'

        canvas[dc.x][dc.y] = corner

    return canvas


def draw_arrow_label(graph: AsciiGraph, edge: AsciiEdge) -> Canvas:
    canvas = copy_canvas(graph.canvas)
    if not edge.text:
        return canvas
    drawing_line = line_to_drawing(graph, edge.labelLine)
    draw_text_on_line(canvas, drawing_line, edge.text)
    return canvas


def draw_text_on_line(canvas: Canvas, line: List[DrawingCoord], label: str) -> None:
    if len(line) < 2:
        return
    min_x = min(line[0].x, line[1].x)
    max_x = max(line[0].x, line[1].x)
    min_y = min(line[0].y, line[1].y)
    max_y = max(line[0].y, line[1].y)
    middle_x = min_x + (max_x - min_x) // 2
    middle_y = min_y + (max_y - min_y) // 2
    start_x = middle_x - (len(label) // 2)
    draw_text(canvas, DrawingCoord(start_x, middle_y), label)


def draw_subgraph_box(sg: AsciiSubgraph, graph: AsciiGraph) -> Canvas:
    width = sg.maxX - sg.minX
    height = sg.maxY - sg.minY
    if width <= 0 or height <= 0:
        return mk_canvas(0, 0)

    frm = DrawingCoord(0, 0)
    to = DrawingCoord(width, height)
    canvas = mk_canvas(width, height)

    if not graph.config.useAscii:
        for x in range(frm.x + 1, to.x):
            canvas[x][frm.y] = '─'
            canvas[x][to.y] = '─'
        for y in range(frm.y + 1, to.y):
            canvas[frm.x][y] = '│'
            canvas[to.x][y] = '│'
        canvas[frm.x][frm.y] = '┌'
        canvas[to.x][frm.y] = '┐'
        canvas[frm.x][to.y] = '└'
        canvas[to.x][to.y] = '┘'
    else:
        for x in range(frm.x + 1, to.x):
            canvas[x][frm.y] = '-'
            canvas[x][to.y] = '-'
        for y in range(frm.y + 1, to.y):
            canvas[frm.x][y] = '|'
            canvas[to.x][y] = '|'
        canvas[frm.x][frm.y] = '+'
        canvas[to.x][frm.y] = '+'
        canvas[frm.x][to.y] = '+'
        canvas[to.x][to.y] = '+'

    return canvas


def draw_subgraph_label(sg: AsciiSubgraph, graph: AsciiGraph) -> Tuple[Canvas, DrawingCoord]:
    width = sg.maxX - sg.minX
    height = sg.maxY - sg.minY
    if width <= 0 or height <= 0:
        return mk_canvas(0, 0), DrawingCoord(0, 0)

    canvas = mk_canvas(width, height)
    label_y = 1
    label_x = (width // 2) - (len(sg.name) // 2)
    if label_x < 1:
        label_x = 1

    for i, ch in enumerate(sg.name):
        if label_x + i < width:
            canvas[label_x + i][label_y] = ch

    return canvas, DrawingCoord(sg.minX, sg.minY)


def sort_subgraphs_by_depth(subgraphs: List[AsciiSubgraph]) -> List[AsciiSubgraph]:
    def depth(sg: AsciiSubgraph) -> int:
        return 0 if sg.parent is None else 1 + depth(sg.parent)
    return sorted(subgraphs, key=depth)


def draw_graph(graph: AsciiGraph) -> Canvas:
    use_ascii = graph.config.useAscii

    for sg in sort_subgraphs_by_depth(graph.subgraphs):
        sg_canvas = draw_subgraph_box(sg, graph)
        graph.canvas = merge_canvases(graph.canvas, DrawingCoord(sg.minX, sg.minY), use_ascii, sg_canvas)

    for node in graph.nodes:
        if not node.drawn and node.drawingCoord and node.drawing:
            graph.canvas = merge_canvases(graph.canvas, node.drawingCoord, use_ascii, node.drawing)
            node.drawn = True

    line_canvases: List[Canvas] = []
    corner_canvases: List[Canvas] = []
    arrow_canvases: List[Canvas] = []
    box_start_canvases: List[Canvas] = []
    label_canvases: List[Canvas] = []

    for edge in graph.edges:
        path_c, box_start_c, arrow_c, corners_c, label_c = draw_arrow(graph, edge)
        line_canvases.append(path_c)
        corner_canvases.append(corners_c)
        arrow_canvases.append(arrow_c)
        box_start_canvases.append(box_start_c)
        label_canvases.append(label_c)

    zero = DrawingCoord(0, 0)
    graph.canvas = merge_canvases(graph.canvas, zero, use_ascii, *line_canvases)
    graph.canvas = merge_canvases(graph.canvas, zero, use_ascii, *corner_canvases)
    graph.canvas = merge_canvases(graph.canvas, zero, use_ascii, *arrow_canvases)
    graph.canvas = merge_canvases(graph.canvas, zero, use_ascii, *box_start_canvases)
    graph.canvas = merge_canvases(graph.canvas, zero, use_ascii, *label_canvases)

    for sg in graph.subgraphs:
        if not sg.nodes:
            continue
        label_canvas, offset = draw_subgraph_label(sg, graph)
        graph.canvas = merge_canvases(graph.canvas, offset, use_ascii, label_canvas)

    return graph.canvas


# =============================================================================
# Sequence renderer
# =============================================================================

def render_sequence_ascii(text: str, config: AsciiConfig) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('%%')]
    diagram = parse_sequence_diagram(lines)
    if not diagram.actors:
        return ''

    use_ascii = config.useAscii

    H = '-' if use_ascii else '─'
    V = '|' if use_ascii else '│'
    TL = '+' if use_ascii else '┌'
    TR = '+' if use_ascii else '┐'
    BL = '+' if use_ascii else '└'
    BR = '+' if use_ascii else '┘'
    JT = '+' if use_ascii else '┬'
    JB = '+' if use_ascii else '┴'
    JL = '+' if use_ascii else '├'
    JR = '+' if use_ascii else '┤'

    actor_idx: Dict[str, int] = {a.id: i for i, a in enumerate(diagram.actors)}

    box_pad = 1
    actor_box_widths = [len(a.label) + 2 * box_pad + 2 for a in diagram.actors]
    half_box = [((w + 1) // 2) for w in actor_box_widths]
    actor_box_h = 3

    adj_max_width = [0] * max(len(diagram.actors) - 1, 0)
    for msg in diagram.messages:
        fi = actor_idx[msg.from_id]
        ti = actor_idx[msg.to_id]
        if fi == ti:
            continue
        lo = min(fi, ti)
        hi = max(fi, ti)
        needed = len(msg.label) + 4
        num_gaps = hi - lo
        per_gap = (needed + num_gaps - 1) // num_gaps
        for g in range(lo, hi):
            adj_max_width[g] = max(adj_max_width[g], per_gap)

    ll_x = [half_box[0]]
    for i in range(1, len(diagram.actors)):
        gap = max(
            half_box[i - 1] + half_box[i] + 2,
            adj_max_width[i - 1] + 2,
            8,
        )
        ll_x.append(ll_x[i - 1] + gap)

    msg_arrow_y: List[int] = []
    msg_label_y: List[int] = []
    block_start_y: Dict[int, int] = {}
    block_end_y: Dict[int, int] = {}
    div_y_map: Dict[str, int] = {}
    note_positions: List[Dict[str, object]] = []

    cur_y = actor_box_h

    for m_idx, msg in enumerate(diagram.messages):
        for b_idx, block in enumerate(diagram.blocks):
            if block.startIndex == m_idx:
                cur_y += 2
                block_start_y[b_idx] = cur_y - 1

        for b_idx, block in enumerate(diagram.blocks):
            for d_idx, div in enumerate(block.dividers):
                if div.index == m_idx:
                    cur_y += 1
                    div_y_map[f"{b_idx}:{d_idx}"] = cur_y
                    cur_y += 1

        cur_y += 1

        is_self = (msg.from_id == msg.to_id)
        if is_self:
            msg_label_y.append(cur_y + 1)
            msg_arrow_y.append(cur_y)
            cur_y += 3
        else:
            msg_label_y.append(cur_y)
            msg_arrow_y.append(cur_y + 1)
            cur_y += 2

        for note in diagram.notes:
            if note.afterIndex == m_idx:
                cur_y += 1
                n_lines = note.text.split('\\n')
                n_width = max(len(l) for l in n_lines) + 4
                n_height = len(n_lines) + 2

                a_idx = actor_idx.get(note.actorIds[0], 0)
                if note.position == 'left':
                    nx = ll_x[a_idx] - n_width - 1
                elif note.position == 'right':
                    nx = ll_x[a_idx] + 2
                else:
                    if len(note.actorIds) >= 2:
                        a_idx2 = actor_idx.get(note.actorIds[1], a_idx)
                        nx = (ll_x[a_idx] + ll_x[a_idx2]) // 2 - (n_width // 2)
                    else:
                        nx = ll_x[a_idx] - (n_width // 2)
                nx = max(0, nx)

                note_positions.append({
                    'x': nx,
                    'y': cur_y,
                    'width': n_width,
                    'height': n_height,
                    'lines': n_lines,
                })
                cur_y += n_height

        for b_idx, block in enumerate(diagram.blocks):
            if block.endIndex == m_idx:
                cur_y += 1
                block_end_y[b_idx] = cur_y
                cur_y += 1

    cur_y += 1
    footer_y = cur_y
    total_h = footer_y + actor_box_h

    last_ll = ll_x[-1] if ll_x else 0
    last_half = half_box[-1] if half_box else 0
    total_w = last_ll + last_half + 2

    for msg in diagram.messages:
        if msg.from_id == msg.to_id:
            fi = actor_idx[msg.from_id]
            self_right = ll_x[fi] + 6 + 2 + len(msg.label)
            total_w = max(total_w, self_right + 1)
    for np in note_positions:
        total_w = max(total_w, np['x'] + np['width'] + 1)

    canvas = mk_canvas(total_w, total_h - 1)

    def draw_actor_box(cx: int, top_y: int, label: str) -> None:
        w = len(label) + 2 * box_pad + 2
        left = cx - (w // 2)
        canvas[left][top_y] = TL
        for x in range(1, w - 1):
            canvas[left + x][top_y] = H
        canvas[left + w - 1][top_y] = TR
        canvas[left][top_y + 1] = V
        canvas[left + w - 1][top_y + 1] = V
        ls = left + 1 + box_pad
        for i, ch in enumerate(label):
            canvas[ls + i][top_y + 1] = ch
        canvas[left][top_y + 2] = BL
        for x in range(1, w - 1):
            canvas[left + x][top_y + 2] = H
        canvas[left + w - 1][top_y + 2] = BR

    for i in range(len(diagram.actors)):
        x = ll_x[i]
        for y in range(actor_box_h, footer_y + 1):
            canvas[x][y] = V

    for i, actor in enumerate(diagram.actors):
        draw_actor_box(ll_x[i], 0, actor.label)
        draw_actor_box(ll_x[i], footer_y, actor.label)
        if not use_ascii:
            canvas[ll_x[i]][actor_box_h - 1] = JT
            canvas[ll_x[i]][footer_y] = JB

    for m_idx, msg in enumerate(diagram.messages):
        fi = actor_idx[msg.from_id]
        ti = actor_idx[msg.to_id]
        from_x = ll_x[fi]
        to_x = ll_x[ti]
        is_self = fi == ti
        is_dashed = msg.lineStyle == 'dashed'
        is_filled = msg.arrowHead == 'filled'

        line_char = '.' if (is_dashed and use_ascii) else ('╌' if is_dashed else H)

        if is_self:
            top_y = msg_arrow_y[m_idx]
            mid_y = msg_label_y[m_idx]
            bot_y = top_y + 2
            loop_x = from_x + 6

            canvas[from_x][top_y] = JL if not use_ascii else '+'
            for x in range(from_x + 1, loop_x):
                canvas[x][top_y] = line_char
            canvas[loop_x][top_y] = TR if not use_ascii else '+'

            for y in range(top_y + 1, bot_y):
                canvas[loop_x][y] = V

            arrow_head = '<' if use_ascii else ('◄' if is_filled else '◁')
            canvas[loop_x][bot_y] = BL if not use_ascii else '+'
            for x in range(from_x + 1, loop_x):
                canvas[x][bot_y] = line_char
            canvas[from_x][bot_y] = arrow_head

            label_start = from_x + 2
            for i, ch in enumerate(msg.label):
                canvas[label_start + i][mid_y] = ch
            continue

        label_y = msg_label_y[m_idx]
        arrow_y = msg_arrow_y[m_idx]

        label_start = min(from_x, to_x) + 2
        for i, ch in enumerate(msg.label):
            canvas[label_start + i][label_y] = ch

        if from_x < to_x:
            for x in range(from_x + 1, to_x):
                canvas[x][arrow_y] = line_char
            arrow_head = '>' if use_ascii else ('▶' if is_filled else '▷')
            canvas[to_x][arrow_y] = arrow_head
        else:
            for x in range(to_x + 1, from_x):
                canvas[x][arrow_y] = line_char
            arrow_head = '<' if use_ascii else ('◀' if is_filled else '◁')
            canvas[to_x][arrow_y] = arrow_head

    for b_idx, block in enumerate(diagram.blocks):
        start_y = block_start_y.get(b_idx)
        end_y = block_end_y.get(b_idx)
        if start_y is None or end_y is None:
            continue
        left = min(ll_x)
        right = max(ll_x)
        top = start_y
        bottom = end_y

        canvas[left - 2][top] = TL
        for x in range(left - 1, right + 2):
            canvas[x][top] = H
        canvas[right + 2][top] = TR

        canvas[left - 2][bottom] = BL
        for x in range(left - 1, right + 2):
            canvas[x][bottom] = H
        canvas[right + 2][bottom] = BR

        for y in range(top + 1, bottom):
            canvas[left - 2][y] = V
            canvas[right + 2][y] = V

        header = f"{block.type} {block.label}".strip()
        for i, ch in enumerate(header):
            canvas[left - 1 + i][top + 1] = ch

        for d_idx, div in enumerate(block.dividers):
            dy = div_y_map.get(f"{b_idx}:{d_idx}")
            if dy is None:
                continue
            canvas[left - 2][dy] = JL
            for x in range(left - 1, right + 2):
                canvas[x][dy] = H
            canvas[right + 2][dy] = JR
            label = f"{div.label}".strip()
            for i, ch in enumerate(label):
                canvas[left - 1 + i][dy + 1] = ch

    for np in note_positions:
        nx = np['x']
        ny = np['y']
        n_width = np['width']
        n_height = np['height']
        lines = np['lines']
        canvas[nx][ny] = TL
        for x in range(1, n_width - 1):
            canvas[nx + x][ny] = H
        canvas[nx + n_width - 1][ny] = TR
        canvas[nx][ny + n_height - 1] = BL
        for x in range(1, n_width - 1):
            canvas[nx + x][ny + n_height - 1] = H
        canvas[nx + n_width - 1][ny + n_height - 1] = BR
        for y in range(1, n_height - 1):
            canvas[nx][ny + y] = V
            canvas[nx + n_width - 1][ny + y] = V
        for i, line in enumerate(lines):
            start_x = nx + 2
            for j, ch in enumerate(line):
                canvas[start_x + j][ny + 1 + i] = ch

    return canvas_to_string(canvas)


# =============================================================================
# Class diagram renderer
# =============================================================================

def format_member(m: ClassMember) -> str:
    vis = m.visibility or ''
    typ = f": {m.type}" if m.type else ''
    return f"{vis}{m.name}{typ}"


def build_class_sections(cls: ClassNode) -> List[List[str]]:
    header: List[str] = []
    if cls.annotation:
        header.append(f"<<{cls.annotation}>>")
    header.append(cls.label)
    attrs = [format_member(m) for m in cls.attributes]
    methods = [format_member(m) for m in cls.methods]
    if not attrs and not methods:
        return [header]
    if not methods:
        return [header, attrs]
    return [header, attrs, methods]


def get_marker_shape(rel_type: str, use_ascii: bool, direction: Optional[str] = None) -> str:
    if rel_type in ('inheritance', 'realization'):
        if direction == 'down':
            return '^' if use_ascii else '△'
        if direction == 'up':
            return 'v' if use_ascii else '▽'
        if direction == 'left':
            return '>' if use_ascii else '◁'
        return '<' if use_ascii else '▷'
    if rel_type == 'composition':
        return '*' if use_ascii else '◆'
    if rel_type == 'aggregation':
        return 'o' if use_ascii else '◇'
    if rel_type in ('association', 'dependency'):
        if direction == 'down':
            return 'v' if use_ascii else '▼'
        if direction == 'up':
            return '^' if use_ascii else '▲'
        if direction == 'left':
            return '<' if use_ascii else '◀'
        return '>' if use_ascii else '▶'
    return '>'


def render_class_ascii(text: str, config: AsciiConfig) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('%%')]
    diagram = parse_class_diagram(lines)
    if not diagram.classes:
        return ''

    use_ascii = config.useAscii
    h_gap = 4
    v_gap = 3

    class_sections: Dict[str, List[List[str]]] = {}
    class_box_w: Dict[str, int] = {}
    class_box_h: Dict[str, int] = {}

    for cls in diagram.classes:
        sections = build_class_sections(cls)
        class_sections[cls.id] = sections
        max_text = 0
        for section in sections:
            for line in section:
                max_text = max(max_text, len(line))
        box_w = max_text + 4
        total_lines = 0
        for section in sections:
            total_lines += max(len(section), 1)
        box_h = total_lines + (len(sections) - 1) + 2
        class_box_w[cls.id] = box_w
        class_box_h[cls.id] = box_h

    class_by_id = {c.id: c for c in diagram.classes}
    parents: Dict[str, set[str]] = {}
    children: Dict[str, set[str]] = {}

    for rel in diagram.relationships:
        is_hier = rel.type in ('inheritance', 'realization')
        parent_id = rel.to_id if (is_hier and rel.markerAt == 'to') else rel.from_id
        child_id = rel.from_id if (is_hier and rel.markerAt == 'to') else rel.to_id
        parents.setdefault(child_id, set()).add(parent_id)
        children.setdefault(parent_id, set()).add(child_id)

    level: Dict[str, int] = {}
    roots = [c for c in diagram.classes if (c.id not in parents or not parents[c.id])]
    queue = [c.id for c in roots]
    for cid in queue:
        level[cid] = 0

    level_cap = max(len(diagram.classes) - 1, 0)
    qi = 0
    while qi < len(queue):
        cid = queue[qi]
        qi += 1
        child_set = children.get(cid)
        if not child_set:
            continue
        for child_id in child_set:
            new_level = level.get(cid, 0) + 1
            if new_level > level_cap:
                continue
            if (child_id not in level) or (level[child_id] < new_level):
                level[child_id] = new_level
                queue.append(child_id)

    for cls in diagram.classes:
        if cls.id not in level:
            level[cls.id] = 0

    max_level = max(level.values()) if level else 0
    level_groups = [[] for _ in range(max_level + 1)]
    for cls in diagram.classes:
        level_groups[level[cls.id]].append(cls.id)

    placed: Dict[str, Dict[str, object]] = {}
    current_y = 0

    for lv in range(max_level + 1):
        group = level_groups[lv]
        if not group:
            continue
        current_x = 0
        max_h = 0
        for cid in group:
            cls = class_by_id[cid]
            w = class_box_w[cid]
            h = class_box_h[cid]
            placed[cid] = {
                'cls': cls,
                'sections': class_sections[cid],
                'x': current_x,
                'y': current_y,
                'width': w,
                'height': h,
            }
            current_x += w + h_gap
            max_h = max(max_h, h)
        current_y += max_h + v_gap

    total_w = 0
    total_h = 0
    for p in placed.values():
        total_w = max(total_w, p['x'] + p['width'])
        total_h = max(total_h, p['y'] + p['height'])
    total_w += 2
    total_h += 2

    canvas = mk_canvas(total_w - 1, total_h - 1)

    for p in placed.values():
        box_canvas = draw_multi_box(p['sections'], use_ascii)
        for bx in range(len(box_canvas)):
            for by in range(len(box_canvas[0])):
                ch = box_canvas[bx][by]
                if ch != ' ':
                    cx = p['x'] + bx
                    cy = p['y'] + by
                    if cx < total_w and cy < total_h:
                        canvas[cx][cy] = ch

    def box_bounds(cid: str) -> Tuple[int, int, int, int]:
        p = placed[cid]
        return (p['x'], p['y'], p['x'] + p['width'] - 1, p['y'] + p['height'] - 1)

    def h_segment_hits_box(y: int, x1: int, x2: int, skip: set[str]) -> bool:
        a = min(x1, x2)
        b = max(x1, x2)
        for cid in placed:
            if cid in skip:
                continue
            bx0, by0, bx1, by1 = box_bounds(cid)
            if by0 <= y <= by1 and not (b < bx0 or a > bx1):
                return True
        return False

    def v_segment_hits_box(x: int, y1: int, y2: int, skip: set[str]) -> bool:
        a = min(y1, y2)
        b = max(y1, y2)
        for cid in placed:
            if cid in skip:
                continue
            bx0, by0, bx1, by1 = box_bounds(cid)
            if bx0 <= x <= bx1 and not (b < by0 or a > by1):
                return True
        return False

    pending_markers: List[Tuple[int, int, str]] = []
    pending_labels: List[Tuple[int, int, str]] = []
    label_spans: List[Tuple[int, int, int]] = []

    for rel in diagram.relationships:
        c1 = placed.get(rel.from_id)
        c2 = placed.get(rel.to_id)
        if not c1 or not c2:
            continue

        x1 = c1['x'] + c1['width'] // 2
        y1 = c1['y'] + c1['height']
        x2 = c2['x'] + c2['width'] // 2
        y2 = c2['y'] - 1

        start_x, start_y = x1, y1
        end_x, end_y = x2, y2

        mid_y = (start_y + end_y) // 2
        skip_boxes = {rel.from_id, rel.to_id}
        if h_segment_hits_box(mid_y, start_x, end_x, skip_boxes):
            for delta in range(1, total_h + 1):
                moved = False
                for candidate in (mid_y - delta, mid_y + delta):
                    if not (0 <= candidate < total_h):
                        continue
                    if h_segment_hits_box(candidate, start_x, end_x, skip_boxes):
                        continue
                    mid_y = candidate
                    moved = True
                    break
                if moved:
                    break
        line_char = '.' if (rel.type in ('dependency', 'realization') and use_ascii) else ('╌' if rel.type in ('dependency', 'realization') else '-')
        v_char = ':' if (rel.type in ('dependency', 'realization') and use_ascii) else ('┊' if rel.type in ('dependency', 'realization') else '|')
        if not use_ascii:
            line_char = '╌' if rel.type in ('dependency', 'realization') else '─'
            v_char = '┊' if rel.type in ('dependency', 'realization') else '│'

        for y in range(start_y, mid_y + 1):
            if 0 <= start_x < total_w and 0 <= y < total_h:
                canvas[start_x][y] = v_char
        step = 1 if end_x >= start_x else -1
        for x in range(start_x, end_x + step, step):
            if 0 <= x < total_w and 0 <= mid_y < total_h:
                canvas[x][mid_y] = line_char
        for y in range(mid_y, end_y + 1):
            if 0 <= end_x < total_w and 0 <= y < total_h:
                canvas[end_x][y] = v_char

        if rel.markerAt == 'from':
            direction = 'down'
            marker_x, marker_y = start_x, start_y - 1
        else:
            direction = 'up'
            marker_x, marker_y = end_x, end_y + 1

        marker = get_marker_shape(rel.type, use_ascii, direction)
        if 0 <= marker_x < total_w and 0 <= marker_y < total_h:
            pending_markers.append((marker_x, marker_y, marker))

        if rel.label:
            label_x = (start_x + end_x) // 2 - (len(rel.label) // 2)
            label_x = max(0, label_x)
            label_y = mid_y - 1
            if label_y >= 0:
                lx1 = label_x
                lx2 = label_x + len(rel.label) - 1
                placed_label = False
                for dy in (0, -1, 1, -2, 2):
                    cy = label_y + dy
                    if not (0 <= cy < total_h):
                        continue
                    overlap = False
                    for sy, sx1, sx2 in label_spans:
                        if sy == cy and not (lx2 < sx1 or lx1 > sx2):
                            overlap = True
                            break
                    if overlap:
                        continue
                    pending_labels.append((label_x, cy, rel.label))
                    label_spans.append((cy, lx1, lx2))
                    placed_label = True
                    break
                if not placed_label:
                    pending_labels.append((label_x, label_y, rel.label))

        if rel.fromCardinality:
            text = rel.fromCardinality
            for i, ch in enumerate(text):
                lx = start_x - len(text) - 1 + i
                ly = start_y - 1
                if 0 <= lx < total_w and 0 <= ly < total_h:
                    canvas[lx][ly] = ch
        if rel.toCardinality:
            text = rel.toCardinality
            for i, ch in enumerate(text):
                lx = end_x + 1 + i
                ly = end_y + 1
                if 0 <= lx < total_w and 0 <= ly < total_h:
                    canvas[lx][ly] = ch

    for mx, my, marker in pending_markers:
        canvas[mx][my] = marker
    for lx, ly, text in pending_labels:
        for i, ch in enumerate(text):
            x = lx + i
            if 0 <= x < total_w and 0 <= ly < total_h:
                canvas[x][ly] = ch

    return canvas_to_string(canvas)


# =============================================================================
# ER diagram renderer
# =============================================================================

def format_attribute(attr: ErAttribute) -> str:
    key_str = (','.join(attr.keys) + ' ') if attr.keys else '   '
    return f"{key_str}{attr.type} {attr.name}"


def build_entity_sections(entity: ErEntity) -> List[List[str]]:
    header = [entity.label]
    attrs = [format_attribute(a) for a in entity.attributes]
    return [header] if not attrs else [header, attrs]


def get_crows_foot_chars(card: str, use_ascii: bool) -> str:
    if use_ascii:
        if card == 'one':
            return '||'
        if card == 'zero-one':
            return 'o|'
        if card == 'many':
            return '}|'
        if card == 'zero-many':
            return 'o{'
    else:
        if card == 'one':
            return '║'
        if card == 'zero-one':
            return 'o║'
        if card == 'many':
            return '╟'
        if card == 'zero-many':
            return 'o╟'
    return '||'


def render_er_ascii(text: str, config: AsciiConfig) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('%%')]
    diagram = parse_er_diagram(lines)
    if not diagram.entities:
        return ''

    use_ascii = config.useAscii
    h_gap = 6
    v_gap = 3

    entity_sections: Dict[str, List[List[str]]] = {}
    entity_box_w: Dict[str, int] = {}
    entity_box_h: Dict[str, int] = {}

    for ent in diagram.entities:
        sections = build_entity_sections(ent)
        entity_sections[ent.id] = sections
        max_text = 0
        for section in sections:
            for line in section:
                max_text = max(max_text, len(line))
        box_w = max_text + 4
        total_lines = 0
        for section in sections:
            total_lines += max(len(section), 1)
        box_h = total_lines + (len(sections) - 1) + 2
        entity_box_w[ent.id] = box_w
        entity_box_h[ent.id] = box_h

    max_per_row = max(2, int((len(diagram.entities) ** 0.5) + 0.999))

    placed: Dict[str, Dict[str, object]] = {}
    current_x = 0
    current_y = 0
    max_row_h = 0
    col_count = 0

    for ent in diagram.entities:
        w = entity_box_w[ent.id]
        h = entity_box_h[ent.id]
        if col_count >= max_per_row:
            current_y += max_row_h + v_gap
            current_x = 0
            max_row_h = 0
            col_count = 0
        placed[ent.id] = {
            'entity': ent,
            'sections': entity_sections[ent.id],
            'x': current_x,
            'y': current_y,
            'width': w,
            'height': h,
        }
        current_x += w + h_gap
        max_row_h = max(max_row_h, h)
        col_count += 1

    total_w = 0
    total_h = 0
    for p in placed.values():
        total_w = max(total_w, p['x'] + p['width'])
        total_h = max(total_h, p['y'] + p['height'])
    total_w += 4
    total_h += 1

    canvas = mk_canvas(total_w - 1, total_h - 1)

    for p in placed.values():
        box_canvas = draw_multi_box(p['sections'], use_ascii)
        for bx in range(len(box_canvas)):
            for by in range(len(box_canvas[0])):
                ch = box_canvas[bx][by]
                if ch != ' ':
                    cx = p['x'] + bx
                    cy = p['y'] + by
                    if cx < total_w and cy < total_h:
                        canvas[cx][cy] = ch

    H = '-' if use_ascii else '─'
    V = '|' if use_ascii else '│'
    dash_h = '.' if use_ascii else '╌'
    dash_v = ':' if use_ascii else '┊'

    for rel in diagram.relationships:
        e1 = placed.get(rel.entity1)
        e2 = placed.get(rel.entity2)
        if not e1 or not e2:
            continue

        line_h = H if rel.identifying else dash_h
        line_v = V if rel.identifying else dash_v

        e1_cx = e1['x'] + e1['width'] // 2
        e1_cy = e1['y'] + e1['height'] // 2
        e2_cx = e2['x'] + e2['width'] // 2
        e2_cy = e2['y'] + e2['height'] // 2

        same_row = abs(e1_cy - e2_cy) < max(e1['height'], e2['height'])

        if same_row:
            left, right = (e1, e2) if e1_cx < e2_cx else (e2, e1)
            left_card, right_card = (rel.cardinality1, rel.cardinality2) if e1_cx < e2_cx else (rel.cardinality2, rel.cardinality1)
            start_x = left['x'] + left['width']
            end_x = right['x'] - 1
            line_y = left['y'] + left['height'] // 2

            for x in range(start_x, end_x + 1):
                if x < total_w:
                    canvas[x][line_y] = line_h

            left_chars = get_crows_foot_chars(left_card, use_ascii)
            for i, ch in enumerate(left_chars):
                mx = start_x + i
                if mx < total_w:
                    canvas[mx][line_y] = ch

            right_chars = get_crows_foot_chars(right_card, use_ascii)
            for i, ch in enumerate(right_chars):
                mx = end_x - len(right_chars) + 1 + i
                if 0 <= mx < total_w:
                    canvas[mx][line_y] = ch

            if rel.label:
                gap_mid = (start_x + end_x) // 2
                label_start = max(start_x, gap_mid - (len(rel.label) // 2))
                label_y = line_y - 1
                if label_y >= 0:
                    for i, ch in enumerate(rel.label):
                        lx = label_start + i
                        if start_x <= lx <= end_x and lx < total_w:
                            canvas[lx][label_y] = ch
        else:
            upper, lower = (e1, e2) if e1_cy < e2_cy else (e2, e1)
            upper_card, lower_card = (rel.cardinality1, rel.cardinality2) if e1_cy < e2_cy else (rel.cardinality2, rel.cardinality1)
            start_y = upper['y'] + upper['height']
            end_y = lower['y'] - 1
            line_x = upper['x'] + upper['width'] // 2

            for y in range(start_y, end_y + 1):
                if y < total_h:
                    canvas[line_x][y] = line_v

            up_chars = get_crows_foot_chars(upper_card, use_ascii)
            if use_ascii:
                uy = start_y
                for i, ch in enumerate(up_chars):
                    if line_x + i < total_w:
                        canvas[line_x + i][uy] = ch
            else:
                uy = start_y
                if len(up_chars) == 1:
                    canvas[line_x][uy] = up_chars
                else:
                    canvas[line_x - 1][uy] = up_chars[0]
                    canvas[line_x][uy] = up_chars[1]

            low_chars = get_crows_foot_chars(lower_card, use_ascii)
            if use_ascii:
                ly = end_y
                for i, ch in enumerate(low_chars):
                    if line_x + i < total_w:
                        canvas[line_x + i][ly] = ch
            else:
                ly = end_y
                if len(low_chars) == 1:
                    canvas[line_x][ly] = low_chars
                else:
                    canvas[line_x - 1][ly] = low_chars[0]
                    canvas[line_x][ly] = low_chars[1]

            if rel.label:
                label_y = (start_y + end_y) // 2
                label_x = line_x + 2
                for i, ch in enumerate(rel.label):
                    lx = label_x + i
                    if lx < total_w and label_y < total_h:
                        canvas[lx][label_y] = ch

    return canvas_to_string(canvas)


# =============================================================================
# Top-level render
# =============================================================================

def detect_diagram_type(text: str) -> str:
    first_line = (text.strip().split('\n')[0].split(';')[0] if text.strip() else '').strip().lower()
    if re.match(r'^sequencediagram\s*$', first_line):
        return 'sequence'
    if re.match(r'^classdiagram\s*$', first_line):
        return 'class'
    if re.match(r'^erdiagram\s*$', first_line):
        return 'er'
    return 'flowchart'


def render_mermaid_ascii(text: str, use_ascii: bool = False, padding_x: int = 6, padding_y: int = 4, box_border_padding: int = 1) -> str:
    config = AsciiConfig(
        useAscii=use_ascii,
        paddingX=padding_x,
        paddingY=padding_y,
        boxBorderPadding=box_border_padding,
        graphDirection='TD',
    )

    diagram_type = detect_diagram_type(text)

    if diagram_type == 'sequence':
        return render_sequence_ascii(text, config)
    if diagram_type == 'class':
        return render_class_ascii(text, config)
    if diagram_type == 'er':
        return render_er_ascii(text, config)

    parsed = parse_mermaid(text)
    if parsed.direction in ('LR', 'RL'):
        config.graphDirection = 'LR'
    else:
        config.graphDirection = 'TD'

    graph = convert_to_ascii_graph(parsed, config)
    create_mapping(graph)
    draw_graph(graph)

    if parsed.direction == 'BT':
        flip_canvas_vertically(graph.canvas)

    return canvas_to_string(graph.canvas)


# =============================================================================
# CLI
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description='Render Mermaid diagrams to ASCII/Unicode.')
    parser.add_argument('input', help='Path to Mermaid text file')
    parser.add_argument('--ascii', action='store_true', help='Use ASCII characters instead of Unicode box drawing')
    parser.add_argument('--padding-x', type=int, default=6, help='Horizontal spacing between nodes')
    parser.add_argument('--padding-y', type=int, default=4, help='Vertical spacing between nodes')
    parser.add_argument('--box-padding', type=int, default=1, help='Padding inside node boxes')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    output = render_mermaid_ascii(
        text,
        use_ascii=args.ascii,
        padding_x=args.padding_x,
        padding_y=args.padding_y,
        box_border_padding=args.box_padding,
    )
    print(output)


if __name__ == '__main__':
    main()
