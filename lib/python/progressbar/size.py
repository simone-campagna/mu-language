
class Span(object):
  def __init__(self, parent, segments):
    self.parent = parent
    if self.parent is not None:
      assert isinstance(parent, Span)
      self.parent.add_child(self)
    if not isinstance(segments, (tuple, list)):
      segments = (segments,)
    self.w_segments = []
    self.p_segments = []
    self.f_segments = 0
    self.s_segments = []
    for segment in segments:
      if isinstance(segment, int):
        self.w_segments.append(segment)
      elif isinstance(segment, float):
        self.p_segments.append(segment)
      elif segment is None:
        self.f_segments += 1
      elif isinstance(segment, size):
        self.s_segments.append(segment)
    self._set_is_fixed()
    self.children = []
    
  def add_child(self, child):
    assert child.parent is None
    child.parent = self
    self.children.append(child)
    self._is_fixed = None
    self._set_is_fixed()

  def add_children(self, children):
    for child in children:
      assert child.parent is None
      child.parent = self
      self.children.append(child)

  @property
  def is_fixed(self):
    if self._is_fixed is None:
      self._set_is_fixed
    return is_fixed

  def _set_is_fixed(self):
    if self.p_segments or self.f_segments:
      self._is_fixed = False
      return
    if self.s_segments:
      for segment in self.s_segments:
        if not segment.is_fixed:
          self._is_fixed = False
          return
    self._is_fixed = True

class BaseSpan(object):
  def __init__(self, children, parent=None):
    self.parent is None
    self.__set_parent(parent)
    for child in children:
      self.add_child(child)
    self._size = 0
    self._unassigned_size = 0

  @property
  def size(self):
    return self._size

  def __set_parent(self, parent):
    assert isinstance(parent, BaseSpan), "parent is not a Span"
    assert self.parent is None, "cannot change parent"
    parent.add_child(self)

  def add_child(self, child):
    assert isinstance(child, BaseSpan), "child is not a Span"
    assert child.parent is None, "cannot get non-orphan child"
    child.parent = self
    self.children.append(child)

  def set_size(self):
    self._set_size()
    for child in self.children:
      child.set_size()

  def allocate_size(self, size):
    size = self.parent.reserve_size(size)
    self.size = size

  def reserve_size(self, child, wanted_size):
    size = min(self._unassigned_size, wanted_size)
    self._unassigned_size -= size
    return size
    
class SizedSpan(BaseSpan):
  def __init__(self, children, size, parent=None):
    assert isinstance(size, int), "invalid size of type '%s' for %s" % (type(size).__name__, self.__class__.__name__)
    self._size = size

  def _set_size(self):
    self.allocate_size(self._size)

class PercentualSpan(BaseSpan):
  def __init__(self, children, percentage, parent=None):
    assert isinstance(size, float), "invalid size of type '%s' for %s" % (type(size).__name__, self.__class__.__name__)
    self._percentage = percentage
    self._fraction = self._percentage/100.0

  def _set_size(self):
    self.allocate_size(int(round(self.parent.size*self._fraction, 0)))
      
