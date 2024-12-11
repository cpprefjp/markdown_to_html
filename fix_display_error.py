# -*- coding: utf-8 -*-
"""
表示崩れを事前修正
=========================================

Markdownライブラリの以下の制限を回避：

- 箇条書きの前に空行が必要な制限を回避して、自動で空行を挟む
"""

import re
import datetime

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

def is_item_line(line: str) -> bool:
    if line.startswith("    "):
        return True
    if line.startswith("\t"):
        return True

    stripped_line = line.strip()
    m = re.match(r'^([0-9]+\.\s)', stripped_line)
    if m:
        return True

    m = re.match(r'^([*+-]\s)', stripped_line)
    if m:
        return True
    return False

class FixDisplayErrorExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        pre = FixDisplayErrorPreprocessor(md)

        md.registerExtension(self)
        md.preprocessors.register(pre, 'fix_display_error', 28)


class FixDisplayErrorPreprocessor(Preprocessor):

    def __init__(self, md):
        Preprocessor.__init__(self, md)

    def run(self, lines):
        new_lines = []

        prev_line: str | None = None
        for line in lines:
            if prev_line != None and len(prev_line) > 0:
                if not is_item_line(prev_line) and is_item_line(line):
                    new_lines.append("")

            prev_line = line
            new_lines.append(line)

        return new_lines


def makeExtension(**kwargs):
    return FixDisplayErrorExtension(**kwargs)
