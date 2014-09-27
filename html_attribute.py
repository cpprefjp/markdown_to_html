#coding: utf-8
from __future__ import unicode_literals
"""
markdown から変換した HTML に属性を追加する
"""

import re
from markdown.util import etree
from markdown import postprocessors
import markdown

HTML_TAGS = {
    'html',
    'head',
    'title',
    'base',
    'link',
    'meta',
    'style',
    'script',
    'noscript',
    'body',
    'section',
    'nav',
    'article',
    'aside',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'hgroup',
    'header',
    'footer',
    'address',
    'p',
    'hr',
    'pre',
    'blockquote',
    'ol',
    'ul',
    'li',
    'dl',
    'dt',
    'dd',
    'figure',
    'figcaption',
    'div',
    'a',
    'em',
    'strong',
    'small',
    's',
    'cite',
    'q',
    'dfn',
    'abbr',
    'time',
    'code',
    'var',
    'samp',
    'kbd',
    'sub',
    'sup',
    'i',
    'b',
    'u',
    'mark',
    'ruby',
    'rt',
    'rp',
    'bdi',
    'bdo',
    'span',
    'br',
    'wbr',
    'ins',
    'del',
    'img',
    'iframe',
    'embed',
    'object',
    'param',
    'video',
    'audio',
    'source',
    'track',
    'canvas',
    'map',
    'area',
    'table',
    'caption',
    'colgroup',
    'col',
    'tbody',
    'thead',
    'tfoot',
    'tr',
    'td',
    'th',
    'form',
    'fieldset',
    'legend',
    'label',
    'input',
    'button',
    'select',
    'datalist',
    'optgroup',
    'option',
    'textarea',
    'keygen',
    'output',
    'progress',
    'meter',
    'details',
    'summary',
    'command',
    'menu',
}

class SafeRawHtmlPostprocessor(postprocessors.Postprocessor):
    def run(self, text):
        for i in range(self.markdown.htmlStash.html_counter):
            html, safe = self.markdown.htmlStash.rawHtmlBlocks[i]
            if not safe:
                html = self.escape(html)
            text = text.replace(self.markdown.htmlStash.get_placeholder(i), html)
        return text

    def escape(self, html):
        # html tag
        m = re.match(r'^\<\/?([a-zA-Z0-9]+)[^\>]*\>$', html)
        if m:
            if m.group(1) in HTML_TAGS:
                return html
        # html entity
        m = re.match(r'^\&.*\;$', html)
        if m:
            return html
        return self.basic_escape(html)

    def basic_escape(self, html):
        html = html.replace('&', '&amp;')
        html = html.replace('<', '&lt;')
        html = html.replace('>', '&gt;')
        return html.replace('"', '&quot;')

class AttributePostprocessor(postprocessors.Postprocessor):
    def __init__(self, md):
        postprocessors.Postprocessor.__init__(self, md)
        self._markdown = md

    def _iterate(self, elements, f):
        f(elements)
        for child in elements.getchildren():
            self._iterate(child, f)

    def _add_color_code(self, element):
        if element.tag == 'code':
            text = element.text
            element.text = ''
            e = etree.SubElement(element, 'span', style='color: #000')
            e.text = text

    def _add_border_table(self, element):
        if element.tag == 'table':
            element.attrib['border'] = '1'
            element.attrib['bordercolor'] = '#888'
            element.attrib['style'] = 'border-collapse:collapse'

    def _remove_md(self, url):
        # サイト内絶対パスで末尾に .md があった場合、取り除く
        # （github のプレビューとの互換性のため）
        matched = re.match('([^#]*)\.md(#.*)?$', url)
        if matched:
            url = matched.group(1)
            anchor = matched.group(2)
            if anchor is not None:
                url = url + anchor
        return url

    def _to_absolute_url(self, element):
        if element.tag == 'a' and element.attrib.has_key('href'):
            base_url = self.config['base_url'].strip('/')
            base_paths = self.config['base_path'].strip('/').split('/')
            full_path = self.config['full_path']

            url = element.attrib['href']
            if url.startswith('http://') or url.startswith('https://'):
                # 絶対パス
                base_url_body = base_url.split('//', 2)[1]
                url_body = url.split('//', 2)[1]
                # 別ドメインの場合は別タブで開く
                if not url_body.startswith(base_url_body):
                    element.attrib['target'] = '_blank'
            elif url.startswith('/'):
                # サイト内絶対パス
                element.attrib['href'] = base_url + url
                element.attrib['href'] = self._remove_md(element.attrib['href'])
            elif url.startswith('#'):
                # ページ内リンク
                element.attrib['href'] = base_url + '/' + self._remove_md(full_path) + url
            else:
                # サイト内相対パス
                paths = []
                for p in base_paths + url.split('/'):
                    if p == '':
                        continue
                    elif p == '.':
                        continue
                    elif p == '..':
                        paths = paths[:-1]
                    else:
                        paths.append(p)
                element.attrib['href'] = base_url + '/' + '/'.join(paths)
                element.attrib['href'] = self._remove_md(element.attrib['href'])

    def run(self, text):
        text = '<{tag}>{text}</{tag}>'.format(tag=self._markdown.doc_tag, text=text)
        root = etree.fromstring(text.encode('utf-8'))
        self._iterate(root, self._add_color_code)
        self._iterate(root, self._add_border_table)
        self._iterate(root, self._to_absolute_url)

        output = self._markdown.serializer(root)
        if self._markdown.stripTopLevelTags:
            try:
                start = output.index('<%s>'%self._markdown.doc_tag)+len(self._markdown.doc_tag)+2
                end = output.rindex('</%s>'%self._markdown.doc_tag)
                output = output[start:end].strip()
            except ValueError:
                if output.strip().endswith('<%s />'%self._markdown.doc_tag):
                    # We have an empty document
                    output = ''
                else:
                    # We have a serious problem
                    raise ValueError('Markdown failed to strip top-level tags. Document=%r' % output.strip())
        return output

class AttributeExtension(markdown.Extension):
    def __init__(self, configs):
        # デフォルトの設定
        self.config = {
            'base_url' : [None, "Base URL used to link URL as absolute URL"],
            'base_path' : [None, "Base Path used to link URL as relative URL"],
            'full_path' : [None, "Full Path used to link URL as anchor URL"],
        }

        # ユーザ設定で上書き
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        attr = AttributePostprocessor(md)
        attr.config = self.getConfigs()
        md.postprocessors.add('html_attribute', attr, '_end')
        md.postprocessors['raw_html'] = SafeRawHtmlPostprocessor(md)

def makeExtension(configs):
    return AttributeExtension(configs)
