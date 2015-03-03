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
from markdown import postprocessors


META_RE = re.compile(r'^\s*\*\s*(?P<target>.*?)\[meta\s+(?P<name>.*?)\]\s*$')


class MetaExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        metapre = MetaPreprocessor(md)
        metapost = MetaPostprocessor(md)

        md.registerExtension(self)
        md.preprocessors.add('meta', metapre, ">normalize_whitespace")
        md.postprocessors.add('meta', metapost, '_end')


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


class MetaPostprocessor(postprocessors.Postprocessor):

    def __init__(self, md):
        postprocessors.Postprocessor.__init__(self, md)
        self._markdown = md

    def run(self, text):
        if not hasattr(self._markdown, '_meta_result'):
            return text

        meta = self._markdown._meta_result

        if 'class' in meta:
            text = text.replace('<h1>', '<h1><span class="class" title="class {cls}">{cls}::</span>'.format(cls=meta['class']))
        if 'namespace' in meta:
            text = text.replace('<h1>', '<h1><span class="namespace" title="namespace {ns}">{ns}::</span>'.format(ns=meta['namespace']))
        if 'header' in meta:
            text = '<div class="header">&lt;{}&gt;</div>'.format(meta['header']) + text
        if 'id-type' in meta:
            text = '<div class="identifier-type">{}</div>'.format(meta['id-type']) + text
        return text


def makeExtension(configs=None):
    return MetaExtension(configs=configs)
