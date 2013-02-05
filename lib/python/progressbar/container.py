#!/usr/bin/env python

class Container(object):
  DEFAULT_WIDTH = 80
  HAS_WIDTH = False
  def __init__(self, children=None):
    self.parent = None
    self.children = []
    self.width = None
    self.has_width = None
    if children:
      for child in children:
        self.add_child(child)

  def __str__(self):
    return "%s[]" % self.__class__.__name__

  def dump(self, level=0):
    indentation = '  '*level
    l = []
    l.append("%s%s -> %s" % (indentation, self, self.width))
    for child in self.children:
      l.extend(child.dump(level+1))
    return l

  def add_child(self, child):
    assert child.parent is None
    child.parent = self
    self.children.append(child)

  def initialize(self):
    self._set_has_width()
    if self.parent is None and not self.has_width:
      parent = FixedContainer(width=self.DEFAULT_WIDTH)
      parent.add_child(self)
      root = self.parent
    else:
      root = self
    self._set_root(root)
        
  def _set_root(self, root):
    self.root = root
    for child in self.children:
      child.root = root
      child._set_root(root)

  def _set_has_width(self):
    for child in self.children:
      child._set_has_width()
    if self.HAS_WIDTH:
      self.has_width = True
    else:
      if self.children:
        for child in self.children:
          if not child.has_width:
            self.has_width = False
            return
        self.has_width = True
      else:
        self.has_width = False
      
  def resize(self):
    self.root.reset()
    width = self.root._initial_width()
    self.root.set_width(width)

  def _initial_width(self):
    assert self.has_width
    width = 0
    for child in self.children:
      width += child._initial_width()
    return width

  def get_width_from_children(self):
    if self.width is not None:
      return self.width
    else:
      return sum(child.get_width_from_children() for child in self.children)

  def reset(self):
    self.set_width(None)
    for child in self.children:
      child.reset()

  def set_width(self, width):
    self.width = width
    self.propagate_width()

  def guess_width(self):
    pass

  def propagate_width(self):
    if self.width is None:
      return
    w_children = []
    p_children = []
    f_children = []
    sub_w = 0
    sub_p = 0.0
    sub_f = 0
    for child in self.children:
      if child.width is not None or isinstance(child, FixedContainer):
        w_children.append(child)
        child.set_width(child.width)
        sub_w += child.width
      elif isinstance(child, PercentageContainer):
        p_children.append(child)
        sub_p += child.percentage
      else:
        f_children.append(child)
        sub_f += 1
    rem_w = self.width - sub_w
    assert sub_p <= 100.0, "invalid percentage for children: %f" % sub_p
    p_lst = [(child, child.percentage) for child in p_children]
    if f_children:
      fill_percentage = (100.0-sub_p)/float(sub_f)
      p_lst.extend((child, fill_percentage) for child in f_children)
    if p_lst:
      rem_w = self.width - sub_w
      for child, percentage in p_lst[:-1]:
        child.set_width(min(rem_w, int(round(rem_w*percentage/100., 0))))
        sub_w += child.width
      child, percentage= p_lst[-1]
      child.set_width(self.width-sub_w)

class FixedContainer(Container):
  HAS_WIDTH = True
  def __init__(self, width, children=None):
    super(FixedContainer, self).__init__(children)
    self.set_fixed_width(width)

  def _initial_width(self):
    return self.fixed_width

  def get_width_from_children(self):
    return self.fixed_width

  def __str__(self):
    return "%s[%s]" % (self.__class__.__name__, self.fixed_width)

  def set_fixed_width(self, fixed_width):
    self.fixed_width = fixed_width
    #self.set_width()
    #if self.width is None:
      #raw_input("GGG")

  def set_width(self, width=None):
    if self.fixed_width is None:
      raw_input("YYY")
    super(FixedContainer, self).set_width(self.fixed_width)

class PercentageContainer(Container):
  def __init__(self, percentage, children=None):
    super(PercentageContainer, self).__init__(children)
    self.percentage = percentage

  def __str__(self):
    return "%s[%s]" % (self.__class__.__name__, self.percentage)

class FillContainer(Container):
  def __init__(self, children=None):
    super(FillContainer, self).__init__(children)

  def set_width(self, width):
    super(FillContainer, self).set_width(width)

ROOT = FixedContainer(Container.DEFAULT_WIDTH)

if __name__ == "__main__":
  r = FillContainer(	
			children=(
					FixedContainer(10),
					FillContainer(),
					PercentageContainer(25.0),
					FillContainer(),
					FixedContainer(30),
			)
  )
  r.initialize()

  for line in r.dump():
    print line

  print
  r.resize()

  for line in r.dump():
    print line
