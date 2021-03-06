# =============================================================================
# FILE: lsp.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# =============================================================================

import re

from deoplete.source.base import Base

LSP_KINDS = [
    'Text',
    'Method',
    'Function',
    'Constructor',
    'Field',
    'Variable',
    'Class',
    'Interface',
    'Module',
    'Property',
    'Unit',
    'Value',
    'Enum',
    'Keyword',
    'Snippet',
    'Color',
    'File',
    'Reference',
    'Folder',
    'EnumMember',
    'Constant',
    'Struct',
    'Event',
    'Operator',
    'TypeParameter',
]


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'lsp'
        self.mark = '[lsp]'
        self.rank = 500
        self.input_pattern = r'[^\w\s]$'
        self.vars = {}
        self.vim.vars['deoplete#source#lsp#_results'] = []
        self.vim.vars['deoplete#source#lsp#_success'] = False
        self.vim.vars['deoplete#source#lsp#_requested'] = False

    def gather_candidates(self, context):
        if not self.vim.call('exists', '*lsp#server#add'):
            return []

        if not self.vim.call('luaeval',
                             'require("lsp.plugin").client.has_started()'):
            return []

        if context['is_async']:
            if self.vim.vars['deoplete#source#lsp#_requested']:
                context['is_async'] = False
                return self.process_candidates()
            return []

        self.vim.vars['deoplete#source#lsp#_requested'] = False
        context['is_async'] = True

        params = self.vim.call(
            'luaeval', 'require("lsp.structures").CompletionParams('
            '{ position = { character = _A }})',
            context['complete_position'])

        self.vim.call(
            'luaeval', 'require("deoplete").request_candidates('
            '_A.arguments, _A.filetype)',
            {'arguments': params, 'filetype': context['filetype']})

        return []

    def process_candidates(self):
        candidates = []
        results = self.vim.vars['deoplete#source#lsp#_results']
        if isinstance(results, dict):
            if 'items' not in results:
                self.print_error(
                    'LSP results does not have "items" key:{}'.format(
                        str(results)))
                return
            items = results['items']
        else:
            items = results
        for rec in items:
            if rec.get('insertText', ''):
                if rec.get('insertTextFormat', 0) != 1:
                    word = rec.get('entryName', rec.get('label'))
                else:
                    word = rec['insertText']
            else:
                word = rec.get('entryName', rec.get('label'))

            item = {
                'word': re.sub(r'\([^)]*\)', '', word),
                'abbr': rec['label'],
                'dup': 0,
            }

            if 'kind' in rec:
                item['kind'] = LSP_KINDS[rec['kind'] - 1]

            if 'detail' in rec and rec['detail']:
                item['info'] = rec['detail']

            candidates.append(item)

        return candidates
