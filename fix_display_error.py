# -*- coding: utf-8 -*-
"""
表示崩れを事前修正
=========================================

Markdownライブラリの以下の制限を回避：

- 箇条書きの前に空行が必要な制限を回避して、自動で空行を挟む
- コードブロックのあとにコード修飾以外を書く際は空行が必要になる制限を回避して、自動で空行を挟む
"""

import re
import datetime

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

def is_item_line(line: str) -> bool:
    stripped_line = line.strip()
    m = re.match(r'^([0-9]+\.\s)', stripped_line)
    if m:
        return True

    m = re.match(r'^([*+-]\s)', stripped_line)
    if m:
        return True
    return False

def is_qualify_or_meta(line: str) -> bool:
    if not is_item_line(line):
        return False
    if "[meta" in line:
        return True
    if "[mathjax enable]" in line:
        return True
    if "[link" in line:
        return True
    if "[color" in line:
        return True
    if "[italic]" in line:
        return True
    return False

class FixDisplayErrorExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        pre = FixDisplayErrorPreprocessor(md)

        md.registerExtension(self)
        #md.preprocessors.add('fix_display_error', pre, ">qualified_fenced_code")
        md.preprocessors.register(pre, 'fix_display_error', 29)


class FixDisplayErrorPreprocessor(Preprocessor):

    def __init__(self, md):
        Preprocessor.__init__(self, md)

    def run(self, lines):
        new_lines = []

        in_outer_code_block: bool = False
        in_code_block: bool = False
        prev_line: str | None = None
        is_prev_code_block = False
        for line in lines:
            is_outer_code_block = line.strip().startswith("````")
            if is_outer_code_block:
                in_outer_code_block = not in_outer_code_block
                prev_line = line
                new_lines.append(line)
                continue

            if not in_outer_code_block:
                is_code_block = line.strip().startswith("```")
                if is_code_block:
                    in_code_block = not in_code_block
                    if not in_code_block:
                        is_prev_code_block = True
                        prev_line = line
                        new_lines.append(line)
                        continue

            if is_prev_code_block and len(line) > 0 and not is_item_line(line) and not is_qualify_or_meta(line):
                is_prev_code_block = False
                new_lines.append("")

            if in_code_block:
                prev_line = line
                new_lines.append(line)
                continue

            if prev_line != None:
                if not is_item_line(prev_line) and is_item_line(line) and not is_qualify_or_meta(line):
                    new_lines.append("")

            prev_line = line
            new_lines.append(line)

        return new_lines


def makeExtension(**kwargs):
    return FixDisplayErrorExtension(**kwargs)
