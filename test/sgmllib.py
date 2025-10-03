# Simple sgmllib module for feedparser compatibility
# This is a minimal implementation to make feedparser work

import re

# Constants that feedparser expects
entityref = re.compile(r'&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile(r'&#(?:[0-9]+|[xX][0-9a-fA-F]+)')
starttagopen = re.compile(r'<[a-zA-Z]')
shorttagopen = re.compile(r'<([a-zA-Z][-.a-zA-Z0-9]*)\s*/(?:\s*>)')
endtagopen = re.compile(r'</\s*([a-zA-Z][-.a-zA-Z0-9]*)\s*>')
tagfind = re.compile(r'([a-zA-Z][-.a-zA-Z0-9]*)(?:\s|$)')
attrfind = re.compile(r'\s*([a-zA-Z_][-.:a-zA-Z0-9_]*)(\s*=\s*(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@]*))?')

# Additional constants that feedparser expects
interesting = re.compile(r'[&<]')
shorttag = re.compile(r'<([a-zA-Z][-.a-zA-Z0-9]*)\s*/(?:\s*>)')

# Exception class that feedparser expects
class incomplete(Exception):
    pass

class SGMLParser:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.rawdata = ""
        self.stack = []
        self.lasttag = None
        self.nomoretags = False
        self.literal = False
    
    def setnomoretags(self):
        self.nomoretags = True
    
    def setliteral(self, *args):
        self.literal = True
    
    def feed(self, data):
        self.rawdata = self.rawdata + data
        self.goahead(0)
    
    def close(self):
        self.goahead(1)
    
    def goahead(self, end):
        pass
    
    def handle_starttag(self, tag, method, attrs):
        pass
    
    def handle_endtag(self, tag, method):
        pass
    
    def handle_data(self, data):
        pass
    
    def handle_charref(self, name):
        pass
    
    def handle_entityref(self, name):
        pass
    
    def handle_comment(self, data):
        pass
    
    def handle_decl(self, decl):
        pass
    
    def handle_pi(self, data):
        pass
    
    def unknown_starttag(self, tag, attrs):
        pass
    
    def unknown_endtag(self, tag):
        pass
    
    def unknown_charref(self, ref):
        pass
    
    def unknown_entityref(self, ref):
        pass
    
    # Additional methods that feedparser expects
    def parse_starttag(self, i):
        return i, None, None
    
    def parse_endtag(self, i):
        return i, None
    
    def parse_comment(self, i):
        return i
    
    def parse_pi(self, i):
        return i
    
    def parse_declaration(self, i):
        return i
    
    def parse_entityref(self, i):
        return i
    
    def parse_charref(self, i):
        return i
    
    def parse_entity(self, i):
        return i
    
    def parse_doctype(self, i):
        return i
    
    def parse_processing_instruction(self, i):
        return i
    
    def parse_comment(self, i):
        return i
    
    def parse_cdata(self, i):
        return i
    
    def parse_rcdata(self, i):
        return i
    
    def parse_cdata_section(self, i):
        return i
    
    def parse_rcdata_section(self, i):
        return i
    
    def parse_rawdata(self, i):
        return i
    
    def parse_rawdata_section(self, i):
        return i
    
    def parse_plaintext(self, i):
        return i
    
    def parse_plaintext_section(self, i):
        return i
    
    def parse_script(self, i):
        return i
    
    def parse_script_section(self, i):
        return i
    
    def parse_style(self, i):
        return i
    
    def parse_style_section(self, i):
        return i
    
    def parse_title(self, i):
        return i
    
    def parse_title_section(self, i):
        return i
    
    def parse_base(self, i):
        return i
    
    def parse_base_section(self, i):
        return i
    
    def parse_isindex(self, i):
        return i
    
    def parse_isindex_section(self, i):
        return i
    
    def parse_meta(self, i):
        return i
    
    def parse_meta_section(self, i):
        return i
    
    def parse_link(self, i):
        return i
    
    def parse_link_section(self, i):
        return i
    
    def parse_script_section(self, i):
        return i
    
    def parse_style_section(self, i):
        return i
    
    def parse_title_section(self, i):
        return i
    
    def parse_base_section(self, i):
        return i
    
    def parse_isindex_section(self, i):
        return i
    
    def parse_meta_section(self, i):
        return i
    
    def parse_link_section(self, i):
        return i

# Export the class and constants
__all__ = ['SGMLParser', 'entityref', 'charref', 'starttagopen', 'shorttagopen', 'endtagopen', 'tagfind', 'attrfind', 'incomplete', 'interesting', 'shorttag'] 