import pytest
from reqops.modules.parser_a import segment_sentences, parse_logic_string

def test_segment_sentences():
    text = "AI-driven development is exciting. Prof. Smith agrees with U.S. standards. This is a second sentence."
    sentences = segment_sentences(text)
    assert len(sentences) == 2
    assert "Prof. Smith" in sentences[0]
    assert "U.S. standards" in sentences[0]
    assert sentences[1] == "This is a second sentence."

    # Japanese segmenting
    jp_text = "要件Aを定義します。これは継続検証パイプラインです。U.S.の基準も含みます。"
    jp_sentences = segment_sentences(jp_text)
    assert len(jp_sentences) == 3
    assert jp_sentences[0] == "要件Aを定義します。"
    assert jp_sentences[1] == "これは継続検証パイプラインです。"


def test_parse_logic_string_atomic():
    node = parse_logic_string("Active(x)")
    assert node["node_type"] == "Atomic"
    assert node["predicate_name"] == "Active"
    assert len(node["arguments"]) == 1
    assert node["arguments"][0]["name"] == "x"
    assert node["arguments"][0]["type"] == "Variable"


def test_parse_logic_string_negation():
    node = parse_logic_string("not (Active(x))")
    assert node["node_type"] == "Negation"
    assert node["operator"] == "Not"
    assert node["scope"]["node_type"] == "Atomic"
    assert node["scope"]["predicate_name"] == "Active"


def test_parse_logic_string_logical():
    node = parse_logic_string("Active(x) and Secure(y)")
    assert node["node_type"] == "Logical"
    assert node["operator"] == "And"
    assert node["left_operand"]["predicate_name"] == "Active"
    assert node["right_operand"]["predicate_name"] == "Secure"


def test_parse_logic_string_quantified():
    node = parse_logic_string("forall x (User(x) -> CanLogin(x))")
    assert node["node_type"] == "Quantified"
    assert node["operator"] == "ForAll"
    assert node["variable"] == "x"
    
    scope = node["scope"]
    assert scope["node_type"] == "Logical"
    assert scope["operator"] == "If"
    assert scope["left_operand"]["predicate_name"] == "User"
    assert scope["right_operand"]["predicate_name"] == "CanLogin"
