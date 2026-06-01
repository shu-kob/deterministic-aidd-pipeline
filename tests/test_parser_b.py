import pytest
from reqops.modules.parser_b import parse_code_to_ast_structure

def test_parse_code_to_ast_structure_valid():
    code = """
import os

class UserHandler:
    def __init__(self, name):
        self.name = name

    def process_data(self):
        for i in range(10):
            print(self.name, i)

def global_helper():
    pass
"""
    result = parse_code_to_ast_structure(code)
    assert result["status"] == "success"
    
    struct = result["structure"]
    assert len(struct["classes"]) == 1
    assert struct["classes"][0]["name"] == "UserHandler"
    assert len(struct["classes"][0]["methods"]) == 2
    
    assert len(struct["functions"]) == 1
    assert struct["functions"][0]["name"] == "global_helper"
    
    assert len(struct["loops"]) == 1
    assert struct["loops"][0]["type"] == "For"


def test_parse_code_to_ast_structure_syntax_error():
    code = """
def broken_syntax(
    print("Forgot closing paren")
"""
    result = parse_code_to_ast_structure(code)
    assert result["status"] == "syntax_error"
    assert "error" in result
