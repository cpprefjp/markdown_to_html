# -*- coding: utf-8 -*-
"""
表示崩れを事前修正
=========================================

Markdownライブラリの箇条書きの前に空行が必要な制限を回避
"""

import re
import datetime

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

def is_item_line(line: str) -> bool:
    m = re.match(r'^([0-9]+\.\s)', line)
    if m:
        return True

    m = re.match(r'^([+-]\s)', line)
    if m:
        return True
    return False

class FixDisplayErrorExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        pre = FixDisplayErrorPreprocessor(md)

        md.registerExtension(self)
        md.preprocessors.add('fix_display_error', pre, ">normalize_whitespace")


class FixDisplayErrorPreprocessor(Preprocessor):

    def __init__(self, md):
        Preprocessor.__init__(self, md)
        self._markdown = md

    def run(self, lines):
        new_lines = []
        self._markdown._meta_result = {}

        in_code_block: bool = False
        prev_line: str | None = None
        for line in lines:
            is_code_block = line.strip().startswith("```")
            if is_code_block:
                in_code_block = not in_code_block

            if in_code_block:
                new_lines.append(line)
                continue

            if prev_line != None:
                if not is_item_line(prev_line) and is_item_line(line):
                    new_lines.append("")

            prev_line = line
            new_lines.append(line)

        return new_lines


def makeExtension(**kwargs):
    return FixDisplayErrorExtension(**kwargs)
