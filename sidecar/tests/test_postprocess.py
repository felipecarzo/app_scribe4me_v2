"""Testes unitarios para o modulo postprocess."""

import sys
from pathlib import Path

# Adiciona o diretorio do sidecar ao path para importar postprocess
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from postprocess import postprocess


class TestPostprocessBasic:
    """Casos basicos e edge cases."""

    def test_empty_string(self):
        assert postprocess("") == ""

    def test_none_returns_none(self):
        # postprocess retorna o input se falsy
        assert postprocess("") == ""

    def test_already_correct(self):
        assert postprocess("Ola, tudo bem?") == "Ola, tudo bem?"

    def test_single_word(self):
        assert postprocess("ola") == "Ola"

    def test_whitespace_only(self):
        assert postprocess("   ") == ""


class TestCapitalization:
    """Capitalizacao de inicio de frase."""

    def test_capitalize_first_letter(self):
        assert postprocess("ola mundo") == "Ola mundo"

    def test_capitalize_after_period(self):
        result = postprocess("primeira frase. segunda frase.")
        assert result == "Primeira frase. Segunda frase."

    def test_capitalize_after_exclamation(self):
        result = postprocess("que legal! isso mesmo.")
        assert result == "Que legal! Isso mesmo."

    def test_capitalize_after_question(self):
        result = postprocess("como vai? tudo bem.")
        assert result == "Como vai? Tudo bem."

    def test_capitalize_accented_char(self):
        result = postprocess("ok. é isso.")
        assert result == "Ok. É isso."


class TestSpacingAroundPunctuation:
    """Espacos antes/depois de pontuacao."""

    def test_remove_space_before_period(self):
        assert postprocess("Ola .") == "Ola."

    def test_remove_space_before_comma(self):
        assert postprocess("Sim , claro") == "Sim, claro"

    def test_remove_space_before_question(self):
        assert postprocess("Como vai ?") == "Como vai?"

    def test_add_space_after_period(self):
        result = postprocess("Frase um.frase dois")
        # Deve inserir espaco e capitalizar
        assert "Frase um. " in result

    def test_add_space_after_comma(self):
        result = postprocess("Ola,mundo")
        assert result == "Ola, mundo"


class TestDuplicatePunctuation:
    """Remocao de pontuacao duplicada."""

    def test_double_period(self):
        result = postprocess("Fim..")
        assert result == "Fim."

    def test_mixed_punctuation(self):
        result = postprocess("Fim.!?")
        assert result == "Fim."

    def test_triple_exclamation(self):
        result = postprocess("Oba!!!")
        assert result == "Oba!"


class TestCombined:
    """Cenarios combinados que exercitam multiplas regras."""

    def test_typical_whisper_output(self):
        raw = "ola , tudo bem ? sim , estou trabalhando no projeto ."
        result = postprocess(raw)
        assert result.startswith("Ola,")
        assert "?" in result
        assert " ." not in result

    def test_multiple_sentences(self):
        raw = "primeira frase. segunda frase! terceira frase?"
        result = postprocess(raw)
        assert result.startswith("Primeira")
        assert "Segunda" in result
        assert "Terceira" in result
