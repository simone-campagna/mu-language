#!/usr/bin/env python

class SpanError(Exception):
  pass

class SizedObj(object):
  def __init__(self, size=None):
    self._set_size(size)
  
  def get_size(self):
    return self._current_size

  def _set_size(self, size):
    self._current_size = size

  def __add__(self, other):
    other = sized_obj(other)
    return SizedObjAdd(self, other)

  def __radd__(self, other):
    other = sized_obj(other)
    return SizedObjAdd(self, other)

  def __sub__(self, other):
    other = sized_obj(other)
    return SizedObjSub(self, other)

  def __rsub__(self, other):
    other = sized_obj(other)
    return SizedObjSub(other, self)

  def __mul__(self, other):
    other = sized_obj(other)
    return SizedObjMul(self, other)

  def __rmul__(self, other):
    other = sized_obj(other)
    return SizedObjMul(self, other)

  def __div__(self, other):
    other = sized_obj(other)
    return SizedObjDiv(self, other)

  def __rdiv__(self, other):
    other = sized_obj(other)
    return SizedObjDiv(other, self)

  def __neg__(self):
    return SizedObjNeg(self)

  def __pos__(self):
    return SizedObjPos(self)

  def __str__(self):
    return "%s[%s]" % (self.__class__.__name__, self.get_size())

class SizedObjUnOp(SizedObj):
  OPERATOR = '?'
  def __init__(self, operand):
    assert isinstance(operand, SizedObj), "operand type %s is not %s" % (type(operand).__name__, SizedObj.__name__)
    self.operand = operand
    super(SizedObjUnOp, self).__init__()

  def __str__(self):
    return "%s(%s(%s))[%s]" % (self.__class__.OPERATOR, self.__class__.__name__, self.operand, self.get_size())

class SizedObjPos(SizedObjUnOp):
  OPERATOR = '+'
  def get_size(self):
    return self.operand.get_size()

class SizedObjNeg(SizedObjUnOp):
  OPERATOR = '-'
  def get_size(self):
    return -self.operand.get_size()

class SizedObjBinOp(SizedObj):
  OPERATOR = '?'
  def __init__(self, left, right):
    assert isinstance(left, SizedObj), "left operand type %s is not %s" % (type(left).__name__, SizedObj.__name__)
    assert isinstance(right, SizedObj), "right operand type %s is not %s" % (type(right).__name__, SizedObj.__name__)
    self.left = left
    self.right = right
    super(SizedObjBinOp, self).__init__()

  def __str__(self):
    return "(%s(%s(%s+%s))[%s]" % (self.__class__.OPERATOR, self.__class__.__name__, self.left, self.right, self.get_size())

class SizedObjAdd(SizedObjBinOp):
  OPERATOR = '+'
  def get_size(self):
    return self.left.get_size() + self.right.get_size()

class SizedObjSub(SizedObjBinOp):
  OPERATOR = '-'
  def get_size(self):
    return self.left.get_size() - self.right.get_size()

class SizedObjMul(SizedObjBinOp):
  OPERATOR = '*'
  def get_size(self):
    return self.left.get_size() * self.right.get_size()

class SizedObjDiv(SizedObjBinOp):
  OPERATOR = '/'
  def get_size(self):
    return self.left.get_size() // self.right.get_size()

def sized_obj(obj):
  if isinstance(obj, int):
    return SizedObj(obj)
  elif isinstance(obj, Span):
    return SizedObjPos(obj)
  elif isinstance(obj, SizedObj):
    return obj
  else:
    raise SpanError, "invalid type %s" % type(obj).__name__

class Span(SizedObj):
  def __init__(self, children=None, parent=None):
    super(Span, self).__init__()
    self.parent = None
    self.root = None
    self.level = None
    self.children = []
    self.fixed_children = []
    self.total_fraction_children = []
    self.free_fraction_children = []
    self.filler_children = []
    self.flexible_children = []
    self._set_parent(parent)
    if children:
      for child in children:
        self.add_child(child)
    self._setup()

  def set_root(self):
    self._set_root(self, 0)

  def _set_root(self, root, level):
    self.root = root
    self.level = level
    for child in self.children:
      child._set_root(root, level+1)

  def reset(self):
    self._set_size(None)
    for child in self.children:
      child.reset()

  def dump(self):
    ind = '  '*self.level
    if self.children:
      l = ["%s%s -> %s (%s)" % (ind, self, self._current_size, self._current_unassigned_size)]
    else:
      l = ["%s%s -> %s" % (ind, self, self._current_size)]
    for child in self.children:
      l.extend(child.dump())
    return l

  def __str__(self):
    return "%s[%s]" % (self.__class__.__name__, self.get_size())
    
  def _setup(self):
    self._set_size(0)
    self._current_unassigned_size = 0
    self._current_float_rounding = 0.0
    self._current_filling_size = 0


  def _set_parent(self, parent):
    if parent is None:
      return
    assert isinstance(parent, Span), "parent is not a Span: %s" % parent
    assert self.parent is None, "cannot change parent"
    parent.add_child(self)

  def add_child(self, child):
    assert isinstance(child, Span), "child is not a Span"
    assert child.parent is None, "cannot get non-orphan child (%s->%s/%s)" % (self, child, child.parent)
    child.parent = self
    self.children.append(child)
    if isinstance(child, FixedSpan):
      self.fixed_children.append(child)
    elif isinstance(child, FillerSpan):
      self.filler_children.append(child)
    elif isinstance(child, TotalFractionalSpan):
      self.total_fraction_children.append(child)
    elif isinstance(child, FreeFractionalSpan):
      self.free_fraction_children.append(child)
    elif isinstance(child, FlexibleSpan):
      self.flexible_children.append(child)

  def update(self):
    if self is self.root:
      if not isinstance(self, FixedSpan):
        raise SpanError, "root span must be FixedSpan"
    self._update()
    self._current_unassigned_size = self._current_size
    for child in self.fixed_children:
      child.update()
    self._current_float_rounding = 0.0
    for child in self.total_fraction_children:
      child.update()
    self._current_float_rounding = 0.0
    self._current_free_size = self._current_unassigned_size
    for child in self.free_fraction_children:
      child.update()
    for child in self.flexible_children:
      child.update()
    if self.filler_children:
      self._current_filling_size = self._current_unassigned_size/float(len(self.filler_children))
      for child in self.filler_children:
        child.update()

  def allocate_exact_size(self, child, size):
    obtained_size = self.parent.reserve_exact_size(child, size)
    if obtained_size is None:
      raise SpanError, ("%s: cannot allocate size: %d" % (child, size))
    self._current_size = size

  def free_size(self):
    return self._current_free_size

  def total_size(self):
    return self._current_size

  def allocate_float_size(self, child, float_size):
    size = self.parent.reserve_float_size(child, float_size)
    self._current_size = size

  def allocate_filling_size(self, child):
    self._current_size = self.parent.reserve_float_size(self, self.parent._current_filling_size)

  def allocate_size(self, child, size):
    self._current_size = self.parent.reserve_size(child, size)

  def reserve_exact_size(self, child, size):
    if size <= self._current_unassigned_size:
      self._current_unassigned_size -= size
      return size
    else:
      return None

  def reserve_float_size(self, child, float_size):
    size = min(self._current_unassigned_size, int(round(float_size+self._current_float_rounding, 0)))
    self._current_float_rounding += float_size - size
    self._current_unassigned_size -= size
    return size

  def reserve_size(self, child, wanted_size):
    size = min(self._current_unassigned_size, wanted_size)
    self._current_unassigned_size -= size
    return size
    
class FixedSpan(Span):
  def __init__(self, size, children=None, parent=None):
    super(FixedSpan, self).__init__(children=children, parent=parent)
    self._size = size
    self._set_size(size)
    self.set_size(size)

  def set_size(self, size):
    assert isinstance(size, int), "invalid size of type '%s' for %s" % (type(size).__name__, self.__class__.__name__)
    self._size = size

  def _update(self):
    size = self.get_size()
    if not self is self.root:
    #  self._current_size = size
    #else:
      self.allocate_exact_size(self, size)

  def get_size(self):
    return self._size

  def __str__(self):
    return "%s(%s)[%s]" % (self.__class__.__name__, self._size, self.get_size())
    
class FixedDependentSpan(FixedSpan):
  def __init__(self, sized_obj, children=None, parent=None):
    super(FixedDependentSpan, self).__init__(size=0, children=children, parent=parent)
    self.set_sized_obj(sized_obj)

  def set_sized_obj(self, sized_obj):
    assert isinstance(sized_obj, SizedObj), "invalid sized_obj of type '%s' for %s" % (type(sized_obj).__name__, self.__class__.__name__)
    self._sized_obj = sized_obj

  def set_size(self, size):
    self.set_sized_obj(sized_obj(size))

  def get_size(self):
    return self._sized_obj.get_size()

  def __str__(self):
    return "%s(%s)[%s]" % (self.__class__.__name__, self._sized_obj, self._sized_obj)

class AdaptiveSpan(FixedSpan):
  def __init__(self, size=0, children=None, parent=None):
    super(AdaptiveSpan, self).__init__(size, children=children, parent=parent)

class FlexibleSpan(Span):
  pass

class FractionalSpan(FlexibleSpan):
  def __init__(self, fraction, children=None, parent=None):
    super(FractionalSpan, self).__init__(children=children, parent=parent)
    self.set_fraction(fraction)

  def get_fraction(self):
    return self._fraction

  def set_fraction(self, fraction):
    assert isinstance(fraction, float), "invalid fraction of type '%s' for %s" % (type(fraction).__name__, self.__class__.__name__)
    assert 0.0 <= fraction <= 1.0, "invalid fraction '%s' for '%s'" % (fraction, self.__class__.__name__)
    self._fraction = fraction


  def __str__(self):
    return "%s(%s)[%s]" % (self.__class__.__name__, self._fraction, self.get_size())
    
class TotalFractionalSpan(FractionalSpan):
  def __init__(self, fraction, children=None, parent=None):
    super(TotalFractionalSpan, self).__init__(fraction, children=children, parent=parent)

  def get_percentage(self):
    return self._percentage

  def set_percentage(self, percentage):
    assert isinstance(percentage, float), "invalid percentage of type '%s' for %s" % (type(percentage).__name__, self.__class__.__name__)
    assert 0.0 <= percentage <= 100.0, "invalid percentage '%s' for '%s'" % (percentage, self.__class__.__name__)
    self._percentage = percentage
    self.set_fraction(self._percentage/100.0)


  def _update(self):
    self.allocate_float_size(self, self.parent.total_size()*self._fraction)

class TotalPercentualSpan(TotalFractionalSpan):
  def __init__(self, percentage, children=None, parent=None):
    assert isinstance(percentage, float), "invalid percentage of type '%s' for %s" % (type(percentage).__name__, self.__class__.__name__)
    assert 0.0 <= percentage <= 100.0, "invalid percentage '%s' for '%s'" % (percentage, self.__class__.__name__)
    self._percentage = percentage
    super(TotalPercentualSpan, self).__init__(self._percentage/100.0, children=children, parent=parent)


  def __str__(self):
    return "%s(%s)[%s]" % (self.__class__.__name__, self._percentage, self.get_size())
    
class FreeFractionalSpan(FractionalSpan):
  def __init__(self, fraction, children=None, parent=None):
    super(FreeFractionalSpan, self).__init__(fraction, children=children, parent=parent)

  def _update(self):
    self.allocate_float_size(self, self.parent.free_size()*self._fraction)

class FreePercentualSpan(FreeFractionalSpan):
  def __init__(self, percentage, children=None, parent=None):
    assert isinstance(percentage, float), "invalid percentage of type '%s' for %s" % (type(percentage).__name__, self.__class__.__name__)
    assert 0.0 <= percentage <= 100.0, "invalid percentage '%s' for '%s'" % (percentage, self.__class__.__name__)
    self._percentage = percentage
    super(FreePercentualSpan, self).__init__(self._percentage/100.0, children=children, parent=parent)

  def get_percentage(self):
    return self._percentage

  def set_percentage(self, percentage):
    assert isinstance(percentage, float), "invalid percentage of type '%s' for %s" % (type(percentage).__name__, self.__class__.__name__)
    assert 0.0 <= percentage <= 100.0, "invalid percentage '%s' for '%s'" % (percentage, self.__class__.__name__)
    self._percentage = percentage
    self.set_fraction(self._percentage/100.0)

  def __str__(self):
    return "%s(%s)[%s]" % (self.__class__.__name__, self._percentage, self.get_size())
    
class FillerSpan(FlexibleSpan):
  def _update(self):
    self.allocate_filling_size(self)

def span(obj, children=None, parent=None):
  if obj is None:
    return FillerSpan(children=children, parent=parent)
  elif isinstance(obj, int):
    return FixedSpan(obj, children=children, parent=parent)
  elif isinstance(obj, float):
    if obj < 0.0:
      return FreeFloatPercentage(obj, children=children, parent=parent)
    else:
      return TotalFloatPercentage(obj, children=children, parent=parent)
  elif isinstance(obj, SizedObj):
    return FixedSpan(obj, children=children, parent=parent)
  else:
     return None

if __name__ == "__main__":
  a = FillerSpan()
  b = FixedSpan(
    40,
  )
  c = FillerSpan()
  s0 = FixedSpan(
    100,
    (
      TotalPercentualSpan(
        2.5,
      ),
      a,
      b,
      c,
      TotalPercentualSpan(
        1.1,
      ),
    ),
  )
  s1 = FixedSpan(
    100,
    (
      FreePercentualSpan(
        49.0,
      ),
      FillerSpan(),
      FixedDependentSpan(
	(a+b+c),
      ),
      FixedSpan(
        4,
      ),
      FillerSpan(),
      FreePercentualSpan(
        51.0,
      ),
    ),
  )

  #print '\n'.join(s0.dump())
  s0.update()
  print '\n'.join(s0.dump())
  print
  #print '\n'.join(s1.dump())
  s1.update()
  print '\n'.join(s1.dump())
