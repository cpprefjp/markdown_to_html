#coding: utf-8
from __future__ import unicode_literals
"""
メタデータ
=========================================

メタデータを記述できるようにする

    >>> text = '''# push_back
    ... * vector[meta header]
    ... * function[meta id-type]
    ... * std[meta namespace]
    ... * vector[meta class]
    ...
    ... 本文
    ... '''
    >>> md = markdown.Markdown(['meta'])
    >>> print md.convert(text)
    <h1>コードをここに書く</h1>
    <p>本文</p>
    >>> md._meta_result
    {'header': 'vector', 'id-type': 'function', 'namespace': 'std', 'class': 'vector'}
"""

from __future__ import absolute_import
import re
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


META_RE = re.compile(r'^\s*\*\s*(?P<target>.*?)\[meta\s+(?P<name>.*?)\]\s*$')


class MetaExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        meta = MetaPreprocessor(md)
        md.registerExtension(self)

        md.preprocessors.add('meta', meta, ">normalize_whitespace")


class MetaPreprocessor(Preprocessor):

    def __init__(self, md):
        Preprocessor.__init__(self, md)
        self._markdown = md

    def run(self, lines):
        new_lines = []
        self._markdown._meta_result = {}
        for line in lines:
            m = META_RE.match(line)
            if m:
                target = m.group('target')
                name = m.group('name')
                self._markdown._meta_result[name] = target
            else:
                new_lines.append(line)
        return new_lines


def makeExtension(configs=None):
    return MetaExtension(configs=configs)
