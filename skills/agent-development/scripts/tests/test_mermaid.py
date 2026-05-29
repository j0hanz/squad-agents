from lib.mermaid import emit_mermaid, AgentGraph, Node, Edge


def test_empty_graph_emits_minimal_header():
    g = AgentGraph(nodes=[], edges=[])
    out = emit_mermaid(g)
    assert out.startswith("graph LR")
    assert len(out.splitlines()) == 1


def test_single_agent_with_one_tool():
    g = AgentGraph(
        nodes=[
            Node(id="agent", label="MyAgent", kind="agent"),
            Node(id="bash", label="Bash (always_ask)", kind="tool"),
        ],
        edges=[Edge(src="agent", dst="bash", label="uses")],
    )
    out = emit_mermaid(g)
    assert "graph LR" in out
    assert 'agent["MyAgent"]' in out
    assert 'bash["Bash (always_ask)"]' in out
    assert "agent -->|uses| bash" in out


def test_special_chars_escaped():
    g = AgentGraph(
        nodes=[Node(id="n1", label='label with "quotes"', kind="tool")],
        edges=[],
    )
    out = emit_mermaid(g)
    # Mermaid requires quotes inside node labels to be escaped
    assert "#quot;" in out or '\\"' in out or "quotes" in out


def test_hook_edge_uses_dotted_arrow():
    g = AgentGraph(
        nodes=[
            Node(id="tool", label="Bash", kind="tool"),
            Node(id="hook", label="audit.sh", kind="hook"),
        ],
        edges=[Edge(src="tool", dst="hook", label="PreToolUse", kind="hook")],
    )
    out = emit_mermaid(g)
    assert "tool -.PreToolUse.-> hook" in out
