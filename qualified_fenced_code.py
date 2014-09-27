#coding: utf-8
from __future__ import unicode_literals
"""
Fenced Code Extension の改造版
=========================================

github でのコードブロック記法が使える。

    >>> text = '''
    ... `````
    ... # コードをここに書く
    ... x = 10
    ... `````'''
    >>> print markdown.markdown(text, extensions=['qualified_fenced_code'])
    <pre><code># コードをここに書く
    x = 10
    </code></pre>

かつ、これらのコードに修飾ができる。

    >>> text = '''
    ... ```
    ... x = [3, 2, 1]
    ... y = sorted(x)
    ... x.sort()
    ... ```
    ... sorted[color ff0000]
    ... sort[link http://example.com/]
    ... '''
    >>> print markdown.markdown(text, extensions=['qualified_fenced_code'])
"""

from __future__ import absolute_import
import re
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.util import Processor
from markdown.extensions.codehilite import CodeHilite, CodeHiliteExtension

CODE_WRAP = '<pre><code%s>%s</code></pre>'
LANG_TAG = ' class="%s"'

QUALIFIED_FENCED_BLOCK_RE = re.compile(r'(?P<fence>`{3,})[ ]*(?P<lang>[a-zA-Z0-9_+-]*)[ ]*\n(?P<code>.*?)(?<=\n)\s*(?P=fence)[ ]*\n(\n|(?P<qualifies>.*?\n\s*\n))', re.MULTILINE|re.DOTALL)
QUALIFY_RE = re.compile(r'^\* +(?P<target>.*?)(?P<commands>(\[.*?\])*)$')
QUALIFY_COMMAND_RE = re.compile(r'\[(.*?)\]')


class QualifiedFencedCodeExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        fenced_block = QualifiedFencedBlockPreprocessor(md)
        md.registerExtension(self)

        md.preprocessors.add('qualified_fenced_code', fenced_block, ">normalize_whitespace")


def _make_random_string():
    """アルファベットから成るランダムな文字列を作る
    """
    import string
    from random import randrange
    alphabets = string.ascii_letters
    return ''.join(alphabets[randrange(len(alphabets))] for i in xrange(32))

class QualifyDictionary(object):
    def __init__(self):
        # 各コマンドに対する実際の処理
        def _qualify_italic(*xs):
            return '<i>{0}</i>'.format(*xs)
        def _qualify_color(*xs):
            return '<span style="color:#{1}">{0}</span>'.format(*xs)
        def _qualify_link(*xs):
            text = xs[0]
            url = xs[1]
            return '<a href="{1}">{0}</a>'.format(*xs)

        self.qualify_dic = {
            'italic': _qualify_italic,
            'color': _qualify_color,
            'link': _qualify_link,
        }

class Qualifier(object):
    """修飾１個分のデータを保持するクラス
    """
    def __init__(self, line, qdic):
        command_res = [r'(\[{cmd}(\]|.*?\]))'.format(cmd=cmd) for cmd in qdic.qualify_dic]

        qualify_re_str = r'^\* +(?P<target>.*?)(?P<commands>({commands})+)$'.format(
                            commands='|'.join(command_res))
        qualify_re = re.compile(qualify_re_str)

        # parsing
        m = qualify_re.search(line)
        if not m:
            raise ValueError, 'Failed parse'
        self.target = m.group('target')
        self.commands = []
        def f(match):
            self.commands.append(match.group(1))
        QUALIFY_COMMAND_RE.sub(f, m.group('commands'))

class QualifierList(object):
    def __init__(self, lines):
        self._qdic = QualifyDictionary()

        # Qualifier を作るが、エラーになったデータは取り除く
        def ignore(f, *args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                return None
        self._qs = filter(None, [ignore(Qualifier, v, self._qdic) for v in lines])


    def mark(self, code):
        """置換対象になる単語にマーキングを施す

        対象文字列が 'sort' だとすれば、文字列中にある全ての 'sort' を
        '{ランダムな文字列}sort{ランダムな文字列}'
        という文字列に置換する。
        """
        if len(self._qs) == 0:
            return code

        # 置換対象になる単語を正規表現で表す
        def get_target_re(target):
            return '((?<=[^a-zA-Z_])|(?:^)){target}((?=[^a-zA-Z_])|(?:$))'.format(
                target=re.escape(target)
            )
        target_re_text = '|'.join('(?:{})'.format(get_target_re(q.target)) for q in self._qs)

        # 対象となる単語を置換し、その置換された文字列を後で辿るための正規表現（text_re_list）と、
        # 置換された文字列に対してどのような修飾を行えばいいかという辞書（match_qualifier）を作る。
        text_re_list = []
        match_qualifier = { }
        def mark_command(match):
            # 各置換毎に一意な文字列を用意する
            match_name = _make_random_string()
            # 対象となる単語がどの修飾のデータなのかを調べる
            text = match.group(0)
            q = (q for q in self._qs if q.target == text).next()
            match_qualifier[match_name] = q

            # text をこの文字列に置換する
            text = '{match_name}{original}{match_name}'.format(
                match_name=match_name,
                original=text,
            )
            # 置換された text だけを確実に検索するための正規表現
            text_re = '(?:{match_name}(?P<{match_name}>.*?)(?:{match_name}))'.format(
                match_name=match_name
            )
            text_re_list.append(text_re)
            return text
        # 対象になる単語を一括置換
        code = re.sub(target_re_text, mark_command, code)
        # マークされた文字列を見つけるための正規表現を作る
        self._code_re = re.compile('|'.join(r for r in text_re_list))
        self._match_qualifier = match_qualifier
        return code

    def qualify(self, html):
        # 修飾の指定がなかった
        if len(self._qs) == 0:
            return html
        # 修飾の指定はあったが、検索してみると修飾する文字列が見つからなかった
        if len(self._code_re.pattern) == 0:
            return html

        # マークされた文字列を探しだして、そのマークに対応した修飾を行う
        def convert(match):
            m,q = ((m,q) for m,q in self._match_qualifier.iteritems() if match.group(m)).next()
            text = match.group(m)
            for command in q.commands:
                xs = command.split(' ')
                c = xs[0]
                remain = xs[1:]
                # 修飾
                text = self._qdic.qualify_dic[c](text, *remain)
            return text
        return self._code_re.sub(convert, html)

class QualifiedFencedBlockPreprocessor(Preprocessor):

    def __init__(self, md):
        Preprocessor.__init__(self, md)

        self.checked_for_codehilite = False
        self.codehilite_conf = {}

    def run(self, lines):
        # Check for code hilite extension
        if not self.checked_for_codehilite:
            for ext in self.markdown.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.config
                    break

            self.checked_for_codehilite = True

        text = "\n".join(lines)
        while 1:
            m = QUALIFIED_FENCED_BLOCK_RE.search(text)
            if m:
                qualifies = m.group('qualifies') or ''
                qualifies = filter(None, qualifies.split('\n'))
                code = m.group('code')
                qualifier_list = QualifierList(qualifies)
                code = qualifier_list.mark(code)

                # If config is not empty, then the codehighlite extension
                # is enabled, so we call it to highlite the code
                if self.codehilite_conf and m.group('lang'):
                    highliter = CodeHilite(code,
                            linenums=self.codehilite_conf['linenums'][0],
                            guess_lang=self.codehilite_conf['guess_lang'][0],
                            css_class=self.codehilite_conf['css_class'][0],
                            style=self.codehilite_conf['pygments_style'][0],
                            lang=(m.group('lang') or None),
                            noclasses=self.codehilite_conf['noclasses'][0])

                    code = highliter.hilite()
                else:
                    lang = ''
                    if m.group('lang'):
                        lang = LANG_TAG % m.group('lang')

                    code = CODE_WRAP % (lang, self._escape(code))

                code = qualifier_list.qualify(code)

                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = '%s\n%s\n%s'% (text[:m.start()], placeholder, text[m.end():])
            else:
                break
        return text.split("\n")

    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(configs=None):
    return QualifiedFencedCodeExtension(configs=configs)
