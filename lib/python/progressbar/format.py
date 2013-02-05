#!/usr/bin/env python
# -*- coding: utf-8 -*-

import terminal

class Format(str):
  #def __init__(self, init=None):
  #  str.__init__(self, init)

  def __len__(self):
    return 0

  def __repr__(self):
    return "%s(%r)" % (self.__class__.__name__, str.__repr__(self))

class FormattedString(list):
  def __init__(self, init=None):
    if isinstance(init, (list, tuple)):
      super(FormattedString, self).__init__(init)
      self._len = None
    elif isinstance(init, self.__class__):
      super(FormattedString, self).__init__(init)
      self._len = init._len
    elif init is None:
      super(FormattedString, self).__init__()
      self._len = 0
    else:
      super(FormattedString, self).__init__([init])
      self._len = len(init)

  def append(self, item):
    #assert isinstance(item, basestring)
    if self._len is not None:
      self._len += len(item)
    if isinstance(item, self.__class__):
      super(FormattedString, self).extend(item)
    else:
      super(FormattedString, self).append(item)

  def extend(self, sequence):
    self._len = None
    super(FormattedString, self).extend(sequence)

  def insert(self, idx, item):
    if self._len is not None:
      self._len += len(item)
    #if isinstance(item, self.__class__):
    #  for c, i in enumerate(item):
    #    super(FormattedString, self).insert(idx+c, i)
    #else:
    super(FormattedString, self).insert(idx, item)
    #super(FormattedString, self).append(item)

  #__setitem__ = None
  __delitem__ = None
  __setslice__ = None
  __delslice__ = None
  remove = None

  def __len__(self):
    if self._len is None:
      self._len = sum(len(item) for item in self)
    return self._len
        
  def ljust(self, width, fill=' '):
    result = self.__class__(self)
    fill = self.__class__(fill)
    len_filling = width - len(self)
    if len_filling > 0:
      if len(fill) == 1:
        filling = fill*len_filling
      else:
        filling = fill*(len_filling//len(fill))
        filling += fill[:len_filling-len(filling)]
      result.append(filling)
    return result

  def rjust(self, width, fill=' '):
    result = self.__class__(self)
    fill = self.__class__(fill)
    len_filling = width - len(self)
    if len_filling > 0:
      if len(fill) == 1:
        filling = fill*len_filling
      else:
        filling = fill*(len_filling//len(fill))
        filling += fill[:len_filling-len(filling)]
      result.insert(0, filling)
    return result

  def center(self, width, fill=' '):
    result = self.__class__(self)
    fill = self.__class__(fill)
    len_filling = width - len(self)
    if len_filling > 0:
      len_filling_l = len_filling//2
      len_filling_r = (len_filling+1)//2
      if len(fill) == 1:
        filling_l = fill*len_filling_l
        filling_r = fill*len_filling_r
      else:
        filling_l = fill*(len_filling_l//len(fill))
        filling_l += fill[:len_filling_l-len(filling_l)]
        filling_r = fill*(len_filling_r//len(fill))
        filling_r += fill[:len_filling_r-len(filling_r)]
      result.insert(0, filling_l)
      result.append(filling_r)
    return result

  def __getitem__(self, idx):
    l = len(self)
    if idx < 0:
      idx += l
    if idx < 0 or idx > l:
      raise IndexError, "%s index out of range: %d not in (%d, %d)" % (self.__class__.__name__, idx, 0, l)
    for item in self:
      len_item = len(item)
      if idx < len_item:
        return item[idx]
      idx -= len_item

  def __setitem__(self, idx, value):
    l = len(self)
    if idx < 0:
      idx += l
    if idx < 0 or idx > l:
      raise IndexError, "%s index out of range: %d not in (%d, %d)" % (self.__class__.__name__, idx, 0, l)
    for c, item in enumerate(self):
      len_item = len(item)
      if idx < len_item:
        list.__setitem__(self, c, item[:idx] + value + item[idx+1:])
        #item[idx] = value
        return
      idx -= len_item

  def __getslice__(self, ib, ie):
    if ib >= ie:
      return self.__class__()
    l = []
    m_len = ie-ib
    offset = 0
    for item in self:
      if isinstance(item, Format):
        l.append(item)
      elif m_len > 0:
        txt = item
        l_txt = len(item)
        if ib < offset+l_txt:
          t = txt[ib-offset:ib-offset+m_len]
          l.append(t)
          m_len -= len(t)
          ib += len(t)
        offset += l_txt
    return self.__class__(l)

  def formatted_string(self):
    #print '000', list.__str__(self)
    return ''.join(self)

  __str__ = formatted_string

  def unformatted_string(self):
    return ''.join(item for item in self if not isinstance(item, Format))

  def __repr__(self):
    return '%s(%s)' % (self.__class__.__name__, list.__repr__(self))

  def apply_format(self, b_fmt, e_fmt=Format(terminal.NORMAL)):
    #print "<<<", repr(self)
    self.insert(0, b_fmt)
    self.append(e_fmt)
    #print ">>>", repr(self)
    #raw_input()

  def __add__(self, other):
    return self.__class__(list.__add__(self, other))

  def __iadd__(self, other):
    return self.__class__(list.__iadd__(self, other))

  def __radd__(self, other):
    return self.__class__(list.__radd__(self, other))

  def __mul__(self, other):
    return self.__class__(list.__mul__(self, other))

  def __imul__(self, other):
    return self.__class__(list.__imul__(self, other))

class Formatter(object):
  NORMAL = terminal.NORMAL
  def __init__(self, color=None, bg_color=None, underline=False, bold=False, blink=False, reverse=False, dim=False):
    self.formats = []
    if color is not None:
      self.formats.append(getattr(terminal, color.upper()))
    if bg_color is not None:
      self.formats.append(getattr(terminal, ("bg_%s"%bg_color).upper()))
    if underline:
      self.formats.append(getattr(terminal, "UNDERLINE"))
    if bold:
      self.formats.append(getattr(terminal, "BOLD"))
    if blink:
      self.formats.append(getattr(terminal, "BLINK"))
    if reverse:
      self.formats.append(getattr(terminal, "REVERSE"))
    if dim:
      self.formats.append(getattr(terminal, "DIM"))
    self.format_str = Format(''.join(self.formats))

  def str_format(self):
    return self.format_str
  def format(self, obj):
    res = FormattedString(obj)
    res.apply_format(self.format_str)
    return res

  def format_string_in_place(self, obj):
    #if not isinstance(obj, FormattedString):
    #  print obj, ''.join(obj)
    obj.apply_format(self.format_str)

  def format_string(self, obj):
    res = FormattedString(obj)
    res.apply_format(self.format_str)
    return res

  __call__ = format
if __name__ == '__main__':
  fs = FormattedString(['alfa', Format('<red>'), 'beta', Format('<blue>'), 'gamma'])

  print fs, len(fs)
  print fs.formatted_string(), len(fs.formatted_string())
  print fs.unformatted_string(), len(fs.unformatted_string())
  for i in xrange(len(fs)):
    print '  ', i, repr(fs[i])

  s = fs.unformatted_string()
  
  for ib, ie in [
			(2, 6),
			(3, 8),
			(2, 2),
			(4, 4),
			(-6, -2),
			(-2, -6),
			(-6, 100),
			(None, 6),
			(2, None),
			(None, None),
    ]:
      if ib is None:
        if ie is None:
          fs_slice = fs[:]
          s_slice = s[:]
        else:
          fs_slice = fs[:ie]
          s_slice = s[:ie]
      else:
        if ie is None:
          fs_slice = fs[ib:]
          s_slice = s[ib:]
        else:
          fs_slice = fs[ib:ie]
          s_slice = s[ib:ie]
      print ib, ie, fs_slice, s_slice
      assert fs_slice.unformatted_string() == s_slice
          
  print repr(fs[2:6])
  print repr(fs[:6])
