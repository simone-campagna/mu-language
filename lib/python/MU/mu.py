#!/usr/bin/env python
# -*- coding: utf-8 -*-


import imp
import sys
import mu_debug
import mu_config
import math
import itertools
import time
import os
import resource
import optparse
from progressbar import terminal, widget, getchar

class Mu_Console(object):
  def __init__(self, mu, max_cache=10000):
    self.mu = mu
    self.stdout = mu.stdout
    self.cache = []
    self.max_cache = max_cache
    self.last_itn = None
    self.last_sym = None

  def put(self, thread, c):
    if self.mu.itn == self.last_itn:
      raise Mu_RuntimeError, ("multiple print at iteration %d" % self.mu.itn, thread)
    self.last_itn = self.mu.itn
    self.last_sym = c
    self.stdout.write(c*thread.operator_multiplicity)
    self.stdout.flush()
    self.cache.append(c)
    del self.cache[:len(self.cache)-self.max_cache]

  def show(self):
    self.stdout.write(''.join(self.console))
    self.stdout.flush()

  def __str__(self):
    return ''.join(self.cache)

  def __repr__(self):
    return '%s<%s>' % (self.__class__.__name__, str(self))
    
  def __len__(self):
    return len(self.cache)

#  def __nonzero__(self):
#    return self.cache.__nonzero__

class Mu_Value(object):
  def __init__(self, value, int_value=None, str_value=None, flt_value=None):
    self.value = value
    self.int_value = int_value
    self.str_value = str_value
    self.flt_value = flt_value
  def asInt(self):
    if self.int_value is None:
      self.int_value = self.toInt()
    return self.int_value
  def asStr(self):
    if self.str_value is None:
      self.str_value = self.toStr()
    return self.str_value
  def asFlt(self):
    if self.flt_value is None:
      self.flt_value = self.toFlt()
    return self.flt_value
  def toInt(self):
    raise NotImplemented
  def toStr(self):
    raise NotImplemented
  def toFlt(self):
    raise NotImplemented
  @classmethod
  def factory(clss, value):
    if isinstance(value, (int, long)):
      return Mu_Int(value)
    elif isinstance(value, str):
      return Mu_Str(value)
    elif isinstance(value, float):
      return Mu_Flt(value)
    else:
      raise Mu_Error, "invalid value <%s> %s" % (type(value).__name__, repr(value)) 
  def clone(self):
    return self.__class__(self.value, self.int_value, self.str_value, self.flt_value)
  def __hash__(self):
    return hash(self.asInt())
  def __repr__(self):
    l = [repr(self.value)]
    if self.int_value is not None:
      l.append("%s=%s" % ('asInt', repr(self.int_value)))
    if self.str_value is not None:
      l.append("%s=%s" % ('asStr', repr(self.str_value)))
    if self.flt_value is not None:
      l.append("%s=%s" % ('asFlt', repr(self.flt_value)))
    return "%s(%s)" % (self.__class__.__name__, ', '.join(l))

  __int__ = asInt
  __str__ = asStr
  __float__ = asFlt
  def __iadd__(self, other):
    return Mu_Int(self.asInt()+int(other))
  def __isub__(self, other):
    return Mu_Int(self.asInt()-int(other))
  def __neg__(self):
    return Mu_Int(-self.asInt())
  def __pos__(self):
    return self
  def __eq__(self, other):
    if self.__class__ is other.__class__:
      return self.value == other.value
    else:
      return self.asInt() == int(other)
  def __ne__(self, other):
    if self.__class__ is other.__class__:
      return self.value != other.value
    else:
      return self.asInt() != int(other)
  def __lt__(self, other):
    if self.__class__ is other.__class__:
      return self.value <  other.value
    else:
      return self.asInt() <  int(other)
  def __le__(self, other):
    if self.__class__ is other.__class__:
      return self.value <= other.value
    else:
      return self.asInt() <= int(other)
  def __gt__(self, other):
    if self.__class__ is other.__class__:
      return self.value >  other.value
    else:
      return self.asInt() >  int(other)
  def __ge__(self, other):
    if self.__class__ is other.__class__:
      return self.value >= other.value
    else:
      return self.asInt() >= int(other)
  def __cmp__(self, other):
    if self.__class__ is other.__class__:
      return cmp(self.value, other.value)
    else:
      return cmp(self.asInt(), int(other))
  #def __hash__(self):
  #  return hash(self.value)

class Mu_Int(Mu_Value):
  def __init__(self, value, int_value=None, str_value=None, flt_value=None):
    int_value = value
    super(Mu_Int, self).__init__(value, int_value, str_value, flt_value)
  def toInt(self):
    return self.value
  def toStr(self):
    return Mu_i2a(self.value)
  def toFlt(self):
    return float(Mu_i2a(self.value))
  def __iadd__(self, other):
    self.value += int(other)
    self.int_value = self.value
    self.str_value = None
    self.flt_value = None
    return self
  def __isub__(self, other):
    self.value -= int(other)
    self.int_value = self.value
    self.str_value = None
    self.flt_value = None
    return self
  def __neg__(self):
    self.value = -self.value
    self.int_value = self.value
    self.str_value = None
    self.flt_value = None
    return self

class Mu_Str(Mu_Value):
  def __init__(self, value, int_value=None, str_value=None, flt_value=None):
    str_value = value
    super(Mu_Str, self).__init__(value, int_value, str_value, flt_value)
  def toInt(self):
    return Mu_a2i(self.value)
  def toStr(self):
    return self.value
  def toFlt(self):
    return float(self.value)

class Mu_Flt(Mu_Value):
  def __init__(self, value, int_value=None, str_value=None, flt_value=None):
    flt_value = value
    super(Mu_Flt, self).__init__(value, int_value, str_value, flt_value)
  def toInt(self):
    return int(self.value)
  def toStr(self):
    return str(self.value)
  def toFlt(self):
    return self.value

class Mu_Stack(object):
  def __init__(self): #, thread):
    #self.thread = thread
    #self.mu_board = self.thread.mu_board
    self.data = []
    self.last_itn = None

  def __len__(self):
    return len(self.data)

  def multiple_push(self, thread, values):
    if thread.mu_board.mu.itn == self.last_itn:
      raise Mu_RuntimeError, ("multiple push at iteration %d" % thread.mu_board.mu.itn, thread)
    m = thread.operator_multiplicity
    mu_values = [Mu_Value.factory(e) for e in values]
    if m > 1:
      mu_values += [e.clone() for e in mu_values*(m-1)]
    return self._multiple_push(thread, mu_values)

  def _multiple_push(self, thread, mu_values):
    self.last_itn = thread.mu_board.mu.itn
    self.data.extend(mu_values)

  def int_push(self, thread, int_value):
    self._push(thread, Mu_Int(int_value))

  def str_push(self, thread, str_value):
    self._push(thread, Mu_Str(str_value))

  def flt_push(self, thread, flt_value):
    self._push(thread, Mu_Flt(flt_value))

  def push(self, thread, value):
    self._push(thread, Mu_Value.factory(value))

  def _push(self, thread, mu_value):
    if thread.mu_board.mu.itn == self.last_itn:
      raise Mu_RuntimeError, ("multiple push at iteration %d" % thread.mu_board.mu.itn, thread)
    self.last_itn = thread.mu_board.mu.itn
    m = thread.operator_multiplicity
    if m > 1:
      self.data.extend(mu_value.clone() for dummy in xrange(m))
    else:
      self.data.append(mu_value)

  def escaped_push(self, thread, int_value):
    if int_value == Mu.a2i('n'):
      int_value = Mu.a2i('\n')
    elif int_value == Mu.a2i('t'):
      int_value = Mu.a2i('\t')
    elif int_value == Mu.a2i('b'):
      int_value = Mu.a2i('\b')
    return self._push(thread, Mu_Int(int_value))

  def pop(self, thread):
    if not self.data:
      raise Mu_RuntimeError, ("pop on empty stack", thread)
    m = thread.operator_multiplicity
    del self.data[-m:]
    #del self.data[-thread.operator_multiplicity:]

  def latest(self, thread):
    if self.data:
      return self.data[-1].clone()
    else:
      raise Mu_RuntimeError, ("empty stack", thread)

  def pop_latest(self, thread):
    if self.data:
      return self.data.pop()
    else:
      raise Mu_RuntimeError, ("empty stack", thread)

  def integer_print(self, thread):
    m = max(thread.operator_multiplicity, 0)
    if self.data:
      thread.mu_board.mu.console.put(thread, str(self.data[-1].asInt())*m)
    else:
      raise Mu_RuntimeError, ("integer_print on empty stack", thread)

  def ascii_print(self, thread):
    m = max(thread.operator_multiplicity, 0)
    if self.data:
      thread.mu_board.mu.console.put(thread, self.data[-1].asStr()*m)
    else:
      raise Mu_RuntimeError, ("ascii_print on empty stack", thread)

  def debug_stack_put(self, thread):
    m = '<%s>' % ','.join(str(d.asInt()) for d in self.data)
    thread.mu_board.mu.console.put(thread, m)

  def duplicate(self, thread):
    if self.data:
      m = max(thread.operator_multiplicity, 1)
      if m == 1:
        self.data.append(self.data[-1].clone())
      else:
        l = [e.clone() for e in self.data[-1:]*m]
        self.data.extend(l)
    else:
      raise Mu_RuntimeError, ("duplicate on short stack", thread)

  def clear(self, thread):
    del self.data[:]

  def copy(self, thread, stack):
    m = max(thread.operator_multiplicity, 1)
    if m == 1:
      self.data.extend(e.clone() for e in stack.data)
    else:
      self.data.extend([e.clone() for e in stack.data*m])

  def join(self, thread):
    num = thread.operator_multiplicity
    if len(self.data) >= num:
      l = [e.asInt() for e in self.data[-num-1:]]
      del self.data[-num-1:]
      self.data.append(Mu_Int(Mu_l2i(l)))
    else:
      raise Mu_RuntimeError, ("join on short stack", thread)

  def split(self, thread):
    num = thread.operator_multiplicity
    if len(self.data) >= num:
      l = [e.asInt() for e in self.data[-num-1:]]
      del self.data[-num:]
      for i in l:
        self.data.extend(Mu_Int(e) for e in Mu_i2l(i))
    else:
      raise Mu_RuntimeError, ("split on short stack", thread)

  def length(self, thread):
    multiplicity = max(thread.operator_multiplicity, 1)
    if multiplicity == 1:
      self.data.append(Mu_Int(len(self.data)))
    else:
      l = len(self.data)
      self.data.extend(Mu_Int(l) for dummy in xrange(multiplicity))

  def increment(self, thread):
    if self.data:
      self.data[-1] += thread.operator_multiplicity
    else:
      raise Mu_RuntimeError, ("increment on empty stack", thread)

  def rotate_left(self, thread):
    if len(self.data) > 1:
      m = thread.operator_multiplicity%len(self.data)
      self.data = self.data[m:] + self.data[:m]

  def rotate_right(self, thread):
    if len(self.data) > 1:
      m = thread.operator_multiplicity%len(self.data)
      self.data = self.data[-m:] + self.data[:-m]

  def reverse(self, thread):
    multiplicity = max(thread.operator_multiplicity, 1)%2
    if multiplicity != 0:
      self.data.reverse()

  def decrement(self, thread):
    if self.data:
      self.data[-1] -= thread.operator_multiplicity
    else:
      raise Mu_RuntimeError, ("decrement on empty stack", thread)
      
  def negate(self, thread):
    multiplicity = max(thread.operator_multiplicity, 1)%2
    if self.data:
      if multiplicity != 0:
        self.data[-1] = -self.data[-1]
    else:
      raise Mu_RuntimeError, ("negate on empty stack", thread)
      
  def clone(self):
    s = self.__class__()
    s.data = [e.clone() for e in self.data]
    return s

  def __str__(self):
    return '[%d](%s)' % (id(self), ','.join(str(value) for value in self.data))

  def __repr__(self):
    return "%s<%s>" % (
		self.__class__.__name__,
		str(self),
    )
 
class Mu_ThreadGroup(list):
  def __init__(self, mu_board, parent_group):
    list.__init__(self)
    self.mu_board = mu_board
    self.parent_group = parent_group
    if self.parent_group:
      self.parent_group.children_groups.append(self)
    self.children_groups = []

  def add_thread(self, thread):
    self.append(thread)

  def del_thread(self, thread):
    self.remove(thread)

  def __hash__(self):
    return hash(id(self))

  def __str__(self):
    return "Mu_Group<%s>[%d](%s)" % (id(self), len(self), ':'.join(str(id(thread)) for thread in self))

  def is_completed(self):
    groups = self
    for thread in self:
      if not thread.completed:
        return False
    for group in self.children_groups:
      if not group.is_completed():
        return False
    return True
        

class Mu_Frame(object):
  def __init__(self, mu_board, parent_thread=None):
    self.mu_board = mu_board
    self.parent_thread = parent_thread
    self.threads = set()

  #def set_completed(self):
  #  for thread in set(self.thread):
  #    thread.set_completed()

  def add_thread(self, thread):
    self.threads.add(thread)

  def del_thread(self, thread):
    self.threads.remove(thread)

  @property
  def completed(self):
    return len(self.threads) == 0

  def new_thread(self, parent_thread, cur, dir, op=None, group=None, clone_stack=False, same_stack=False):
    thread = Mu_Thread.WITH_PARENT_STACK_CLONE(self, parent_thread, cur, dir, op, group=group)
    #thread.clone_parent_stack()
    return thread

  def __str__(self):
    return 'PARENT=%s, #THREADS=%d' % (
		self.parent_thread,
		len(self.threads),
    )

  def __repr__(self):
    return '%s<%s>' % (
		self.__class__.__name__,
		str(self),
    )

#class Mu_MainFunctionFrame(Mu_Frame):
#  def __init__(self, function, parent_thread):
#    self.function = function
#    super(Mu_MainFunctionFrame, self).__init__(function.mu_board, parent_thread)
  
class Mu_FunctionFrame(Mu_Frame):
  def __init__(self, function, parent_thread):
    self.function = function
    super(Mu_FunctionFrame, self).__init__(function.mu_board, parent_thread)
    self.REGISTER_RETURN_SYMBOL = None
  
  def del_thread(self, thread):
    super(Mu_FunctionFrame, self).del_thread(thread)
    if len(self.threads) == 0 and self.parent_thread is not None:
      if self.REGISTER_RETURN_SYMBOL is not None:
        self.parent_thread.REGISTER_APPLY_SYMBOL = self.REGISTER_RETURN_SYMBOL
      self.parent_thread.wakeup()
      #self.mu_board.threads.add(self.parent_thread)
      #self.mu_board.waiting_threads.remove(self.parent_thread)

class Mu_ImplicitFunctionFrame(Mu_FunctionFrame):
  #def __init__(self, function, parent_thread):
  #  super(Mu_ImplicitFunctionFrame, self).__init__(function, parent_thread)

  def del_thread(self, thread):
    self.parent_thread.cur = thread.cur[0]-thread.dir[0], thread.cur[1]-thread.dir[1]
    self.parent_thread.dir = thread.dir
    super(Mu_FunctionFrame, self).del_thread(thread)
    if len(self.threads) == 0:
      self.parent_thread.wakeup()

class Mu_StacklessImplicitFunctionFrame(Mu_ImplicitFunctionFrame):
  pass

class Mu_Function(object):
  FRAME_CLASS = Mu_FunctionFrame
  def __init__(self, mu_board, cur, dir, op=None):
    self.mu_board = mu_board
    self.cur = cur
    self.dir = dir
    self.op = op

  def _create_thread(self, parent_thread, function_frame):
    thread = Mu_Thread.WITH_NEW_STACK(
					function_frame,
					parent_thread,
					self.cur,
					self.dir,
					self.op,
    )
    return thread

  def __call__(self, parent_thread):
    function_frame = self.__class__.FRAME_CLASS(self, parent_thread)
    thread = self._create_thread(parent_thread, function_frame)
    parent_thread.wait_frame = function_frame,
    self.mu_board.add_thread(thread)
    parent_thread.sleep()

  def begin(self):
    parent_thread = None
    function_frame = self.__class__.FRAME_CLASS(self, parent_thread)
    thread = self._create_thread(parent_thread, function_frame)
    self.mu_board.add_thread(thread)

class Mu_StaticFunction(Mu_Function):
  FRAME_CLASS = Mu_FunctionFrame
  def __init__(self, mu_board, cur, dir, op=None):
    super(Mu_StaticFunction, self).__init__(mu_board, cur, dir, op)
    self._saved_stack = Mu_Stack()

  def _create_thread(self, parent_thread, function_frame):
    thread = Mu_Thread.WITH_STACK(
						self._saved_stack,
						function_frame,
						parent_thread,
						self.cur,
						self.dir,
						self.op,
    )
    return thread

#class Mu_MainFunction(Mu_Function):
#  FRAME_CLASS = Mu_MainFunctionFrame
#  def __init__(self, mu_board, cur, dir, op=None):
#    super(Mu_MainFunction, self).__init__(mu_board, cur, dir, op)
#    self._saved_stack = Mu_Stack()
#
#  def _create_thread(self, function_frame):
#    thread = Mu_Thread.WITH_STACK(
#						self._saved_stack,
#						function_frame,
#						None,
#						self.cur,
#						self.dir,
#						self.op,
#    )
#    return thread
#
#  def __call__(self):
#    function_frame = self.__class__.FRAME_CLASS(self, None)
#    thread = self._create_thread(function_frame)
#    self.mu_board.add_thread(thread)
    
class Mu_ImplicitFunction(Mu_Function):
  FRAME_CLASS = Mu_ImplicitFunctionFrame
  #def __init__(self, mu_board, cur, dir, op=None):
  #  super(Mu_ImplicitFunction, self).__init__(mu_board, cur, dir, op)

class Mu_StacklessImplicitFunction(Mu_Function):
  FRAME_CLASS = Mu_StacklessImplicitFunctionFrame
  #def __init__(self, mu_board, cur, dir, op=None):
  #  super(Mu_StacklessImplicitFunction, self).__init__(mu_board, cur, dir, op)

  def _create_thread(self, parent_thread, function_frame):
    thread = Mu_Thread.WITH_PARENT_STACK_LINK(
						function_frame,
						parent_thread,
						self.cur,
						self.dir,
						self.op,
    )
    #thread.link_parent_stack()
    return thread
  
class Mu_Thread(object):
  def __init__(self, frame, parent_thread, cur, dir, op=None, group=None):
    self.frame = frame
    self.mu_board = self.frame.mu_board
    self.parent_thread = parent_thread
    self.cur = cur
    self.dir = dir
    self.op = op
    self.__completed = False
    self.wait_frame = None
    self.stack_threads = []
    self.frame.add_thread(self)
    self.is_held = False
    self.is_holding = False
    self.is_waiting = False
    self._operator_multiplicity_default = 1
    self._operator_multiplicity = self._operator_multiplicity_default
    if group is None:
      group = Mu_ThreadGroup(self.mu_board, None)
    self.group = group
    self.group.add_thread(self)
    self.REGISTER_APPLY_SYMBOL = None
    self.REGISTER_STRING_ESCAPE = False
    self.REGISTER_EXCEPTION_CUR_DIR = None
    #self.step = self._step
    self.unset_op()
 
  @classmethod
  def WITH_STACK(clss, stack, frame, parent_thread, cur, dir, op=None, group=None):
    thread = clss(frame, parent_thread, cur, dir, op, group)
    thread.local_stack = stack
    #print "HERE", id(thread), thread.local_stack
    thread.stack_thread = thread
    thread.stack = thread.local_stack
    return thread

  @classmethod
  def WITH_NEW_STACK(clss, frame, parent_thread, cur, dir, op=None, group=None):
    thread = clss(frame, parent_thread, cur, dir, op, group)
    thread.local_stack = Mu_Stack()
    thread.stack_thread = thread
    thread.stack = thread.local_stack
    return thread

  @classmethod
  def WITH_PARENT_STACK_CLONE(clss, frame, parent_thread, cur, dir, op=None, group=None):
    thread = clss(frame, parent_thread, cur, dir, op, group)
    thread.local_stack = thread.parent_thread.stack.clone()
    thread.stack_thread = thread
    thread.stack = thread.local_stack
    return thread

  @classmethod
  def WITH_PARENT_STACK_LINK(clss, frame, parent_thread, cur, dir, op=None, group=None):
    thread = clss(frame, parent_thread, cur, dir, op, group)
    thread.local_stack = thread.parent_thread.stack
    thread.stack_thread = thread.parent_thread.stack_thread
    thread.stack = thread.local_stack
    return thread

  def _set_stack(self):
    if self.stack_thread is self:
      self.stack = self.local_stack
    else:
      self.stack = self.stack_thread.stack

  @property
  def operator_multiplicity(self):
    i = self._operator_multiplicity
    self._operator_multiplicity = self._operator_multiplicity_default
    return i

  def hold(self):
    self.is_held = True
    self.mu_board.mu.held_threads.add(self)
    self.mu_board.del_thread(self)

  def release(self):
    self.is_held = False
    self.mu_board.add_thread(self)
    self.mu_board.mu.held_threads.remove(self)

  def sleep(self):
    self.is_waiting = True
    self.mu_board.mu.waiting_threads.add(self)
    self.mu_board.mu.threads.remove(self)

  def wakeup(self):
    if self.completed:
      return
    self.is_waiting = False
    self.mu_board.add_thread(self)
    self.mu_board.mu.waiting_threads.remove(self)

  def __get_completed(self):
    return self.__completed

  def set_completed(self):
    if not self.__completed:
      self.__completed = True
      self.frame.del_thread(self)
      self.mu_board.del_thread(self)
      self.group.del_thread(self)

  completed = property(__get_completed, set_completed)

  def set_op(self, op):
    self.op = op
    self._step_function = self._step_unary

  def unset_op(self):
    self.op = None
    self._step_function = self._step_empty

  def _catch_exception(self, e):
    #for thread in set(self.frame.threads):
    #  print "COMPLETED:", thread.cur, thread.dir, repr(Mu_i2a(thread.mu_board.board[thread.cur[0]][thread.cur[1]]))
    #  thread.set_completed()
    if self.REGISTER_EXCEPTION_CUR_DIR:
      self.cur, self.dir = self.REGISTER_EXCEPTION_CUR_DIR
      symbol = self.mu_board.board[self.cur[0]][self.cur[1]]
      empty_operator = self.mu_board.step_operator[symbol]
      self.REGISTER_EXCEPTION_CUR_DIR = None
      self.unset_op()
      return self._step_function(symbol, empty_operator)
    else:
      self.set_completed()
      if self.parent_thread is not None:
        self.parent_thread._catch_exception(e)
      else:
        raise e
    
  def step(self):
    cur_i, cur_j = self.cur
    dir_i, dir_j = self.dir
    cur_i += dir_i
    cur_j += dir_j
    #cur_i, cur_j = cur_i+dir_i, cur_j+dir_j
    self.cur = cur_i, cur_j
    symbol = self.mu_board.board[cur_i][cur_j]
    try:
      return self._step_function(symbol, self.mu_board.step_operator[symbol])
    except Mu_CodeError, e:
      self._catch_exception(e)
    #finally:
    #  self.step = self._step

#  def _step(self):
#    cur_i, cur_j = self.cur
#    dir_i, dir_j = self.dir
#    cur_i, cur_j = cur_i+dir_i, cur_j+dir_j
#    self.cur = cur_i, cur_j
#    symbol = self.mu_board.board[cur_i][cur_j]
#    empty_operator = self.mu_board.step_operator[symbol]
#    return self._step_function(symbol, empty_operator)
    
  def _step_unary(self, symbol, empty_operator):
    self.op(self, symbol, empty_operator)
    
  def _step_empty(self, symbol, empty_operator):
    empty_operator(self, symbol, empty_operator)

  def _step_empty_operator__stack_if_negative(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_if_negative)

  def _step_unary_operator__stack_if_negative(self, symbol, empty_operator):
    if self.stack.latest(self).asInt() < 0:
      #symbol = Mu.DIRECTION_SYMBOL[self.dir]
      empty_operator = self.mu_board.step_operator[Mu.SYM_BRIDGE]
    self.unset_op()
    return self._step_function(symbol, empty_operator)

  def _step_empty_operator__stack_if_positive(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_if_positive)

  def _step_unary_operator__stack_if_positive(self, symbol, empty_operator):
    if self.stack.latest(self).asInt() > 0:
      #symbol = Mu.DIRECTION_SYMBOL[self.dir]
      empty_operator = self.mu_board.step_operator[Mu.SYM_BRIDGE]
    self.unset_op()
    return self._step_function(symbol, empty_operator)

  def _step_empty_operator__stack_if_nonzero(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_if_nonzero)

  def _step_unary_operator__stack_if_nonzero(self, symbol, empty_operator):
    if self.stack.latest(self).asInt() != 0:
      #symbol = Mu.DIRECTION_SYMBOL[self.dir]
      empty_operator = self.mu_board.step_operator[Mu.SYM_BRIDGE]
    self.unset_op()
    return self._step_function(symbol, empty_operator)

  def _step_empty_operator__stack_if_zero(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_if_zero)

  def _step_unary_operator__stack_if_zero(self, symbol, empty_operator):
    if self.stack.latest(self).asInt() == 0:
      #symbol = Mu.DIRECTION_SYMBOL[self.dir]
      empty_operator = self.mu_board.step_operator[Mu.SYM_BRIDGE]
    self.unset_op()
    return self._step_function(symbol, empty_operator)

  def _step_empty_operator__operator_call_wrapper(self, call_operator, symbol, empty_operator):
    self.call_operator = call_operator
    return self._step_empty_operator__operator_call(symbol, empty_operator)

  def _step_empty_operator__operator_call(self, symbol, empty_operator):
    self.set_op(self.__class__._step_empty_operator__operator_call_trace)
    self.call_mult = self.operator_multiplicity
    return self._step_function(symbol, self.op)
    
  def _step_empty_operator__operator_call_trace(self, symbol, empty_operator):
    if self.call_mult > 0:
      self.call_operator(self)
      self.call_mult -= 1
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
    else:
      self.unset_op()
      if self.REGISTER_APPLY_SYMBOL is not None:
        symbol = self.REGISTER_APPLY_SYMBOL
        self.REGISTER_APPLY_SYMBOL = None
        return self._step_function(symbol, self.mu_board.step_operator[symbol])

  def _step_empty_operator__function_call(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__function_call)

  def _step_unary_operator__function_call(self, symbol, empty_operator):
    self.call_function = self.mu_board.get_function(symbol, self)
    self.set_op(self.__class__._step_unary_operator__function_call_trace)
    self.call_mult = self.operator_multiplicity
    return self._step_function(symbol, self.op)

  def _step_unary_operator__function_call_trace(self, symbol, empty_operator):
    if self.call_mult > 0:
      self.call_function(self)
      self.call_mult -= 1
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
    else:
      self.unset_op()
      if self.REGISTER_APPLY_SYMBOL is not None:
        symbol = self.REGISTER_APPLY_SYMBOL
        self.REGISTER_APPLY_SYMBOL = None
        return self._step_function(symbol, self.mu_board.step_operator[symbol])

  def _step_unary_operator__raise_unexpected_unary_operator(self, symbol, empty_operator):
    raise Mu_SyntaxError, ("unexpected unary operator %d[%s]" % (self.op, Mu.i2a(self.op)), self)

  def _step_empty_operator__ignore(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__ignore)

  def _step_unary_operator__ignore(self, symbol, empty_operator):
    self.unset_op()

  def _step_empty_operator__stack_push(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_push)

  def _step_unary_operator__stack_push(self, symbol, empty_operator):
    self.stack.push(self, symbol)
    self.unset_op()

  def _step_empty_operator__stack_escaped_push(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__stack_escaped_push)

  def _step_unary_operator__stack_escaped_push(self, symbol, empty_operator):
    self.stack.push(self, Mu.ESCAPED_SYMBOLS.get(symbol, symbol))
    self.unset_op()

  def _step_unary_operator__wait(self, symbol, empty_operator):
    if self._wait_num_cycles > 0:
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
      self._wait_num_cycles -= 1
    else:
      self.unset_op()
      self._step_function(symbol, empty_operator)

  def _step_empty_operator__local_variable_set(self, symbol, empty_operator):
    variable_name = self.stack.pop_latest(self)
    variable_value = self.stack.pop_latest(self)
    #print "LSET", repr(variable_name), type(variable_name), '=', repr(variable_value), type(variable_value)
    self.mu_board.set_local_variable(variable_name, variable_value)

  def _step_empty_operator__global_variable_set(self, symbol, empty_operator):
    variable_name = self.stack.pop_latest(self)
    variable_value = self.stack.pop_latest(self)
    #print "GSET", repr(variable_name), type(variable_name), '=', repr(variable_value), type(variable_value)
    self.mu_board.set_global_variable(variable_name, variable_value)

  def _step_empty_operator__variable_del(self, symbol, empty_operator):
    variable_name = self.stack.pop_latest(self)
    result = self.mu_board.del_variable(variable_name)
    if not result:
      raise Mu_RuntimeError, ('variable [%d]/"%r" not defined' % (int(variable_name), str(variable_name)), self)

  def _step_empty_operator__variable_get(self, symbol, empty_operator):
    variable_name = self.stack.pop_latest(self)
    #print "GET", repr(variable_name), type(variable_name), variable_name
    variable_value = self.mu_board.get_variable(variable_name)
    if variable_value is None:
      raise Mu_RuntimeError, ('variable [%d]/"%r" not defined' % (int(variable_name), str(variable_name)), self)
    #print "HERE", variable_name, variable_value
    self.stack._push(self, variable_value)

  def _step_empty_operator__lambda_begin(self, symbol, empty_operator):
    self.lambda_function = Mu_ImplicitFunction(self.mu_board, self.cur, self.dir, None)
    self.set_op(self.__class__._step_empty_operator__lambda_call_trace)
    self.lambda_mult = self.operator_multiplicity
    if self.lambda_mult <= 0:
      raise Mu_RuntimeError, ("invalid multiplicity %d" % self.lambda_mult, self)
    return self._step_function(symbol, self.op)

  def _step_empty_operator__lambda_call_trace(self, symbol, empty_operator):
    if self.lambda_mult > 0:
      self.lambda_function(self)
      self.lambda_mult -= 1
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
    else:
      self.unset_op()

  def _step_empty_operator__lambda_return(self, symbol, empty_operator):
    for thread in set(self.frame.threads):
      thread.set_completed()

  def _step_empty_operator__block_begin(self, symbol, empty_operator):
    self.block_function = Mu_StacklessImplicitFunction(self.mu_board, self.cur, self.dir, None)
    self.set_op(self.__class__._step_empty_operator__block_call_trace)
    self.block_mult = self.operator_multiplicity
    if self.block_mult <= 0:
      raise Mu_RuntimeError, ("invalid multiplicity %d" % self.block_mult, self)
    return self._step_function(symbol, self.op)

  def _step_empty_operator__block_call_trace(self, symbol, empty_operator):
    if self.block_mult > 0:
      self.block_function(self)
      self.block_mult -= 1
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
    else:
      self.unset_op()

  def _step_empty_operator__block_return(self, symbol, empty_operator):
    for thread in set(self.frame.threads):
      thread.set_completed()

  def _step_empty_operator__stack_operator_multiplier(self, symbol, empty_operator):
    self._operator_multiplicity = self.stack.pop_latest(self).asInt()
    self._operator_multiplicity_default = 1

  def _step_empty_operator__stack_string(self, symbol, empty_operator):
    self.mu_board.check_bounds(self.cur, self.dir)
    if self.REGISTER_STRING_ESCAPE:
      self._string.append(Mu.ESCAPED_SYMBOLS.get(symbol, symbol))
      self.REGISTER_STRING_ESCAPE = False
    else:
      if symbol == Mu.ESCAPE_SYMBOL:
        self.REGISTER_STRING_ESCAPE = True
      elif symbol != Mu.SYM_STACK_STRING_END:
        self._string.append(symbol)
      else:
        self.stack.push(self, Mu.l2a(self._string))
        self.unset_op()

  def _step_empty_operator__stack_string_begin(self, symbol, empty_operator):
    self._string = []
    self.set_op(self.__class__._step_empty_operator__stack_string)

  def _step_empty_operator__stack_int(self, symbol, empty_operator):
    self.mu_board.check_bounds(self.cur, self.dir)
    if symbol != Mu.SYM_STACK_INT_END:
      if symbol < Mu.SYM_0 or symbol > Mu.SYM_9:
        if symbol in (Mu.SYM_SIGN_PLUS, Mu.SYM_SIGN_MINUS) and len(self._int) == 0:
          # sign!
          pass
        else:
          raise Mu_RuntimeError, ("invalid char %d[%s] for integer definition" % (symbol, Mu.i2a(symbol)), self)
      self._int.append(Mu.i2a(symbol))
      self.set_op(self.__class__._step_empty_operator__stack_int)
    else:
      r = int(''.join(self._int))
      self.stack.push(self, r)
      self.unset_op()

  def _step_empty_operator__stack_int_begin(self, symbol, empty_operator):
    self._int = []
    self.set_op(self.__class__._step_empty_operator__stack_int)

  def _step_empty_operator__wait(self, symbol, empty_operator):
    self._wait_num_cycles = max(0, self.operator_multiplicity)
    self.set_op(self.__class__._step_unary_operator__wait)

  def _step_empty_operator__exception_raise(self, symbol, empty_operator):
    raise Mu_RuntimeError, ("exception raised", self)

  def _step_empty_operator__exception_set_handler(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__exception_set_handler)

  def _step_unary_operator__exception_set_handler(self, symbol, empty_operator):
    self.REGISTER_EXCEPTION_CUR_DIR = self.cur, self.dir
    self.unset_op()

  def _step_empty_operator__exception_unset_handler(self, symbol, empty_operator):
    self.REGISTER_EXCEPTION_CUR_DIR = None

  def _step_empty_operator__raise_unexpected_empty_operator(self, symbol, empty_operator):
    raise Mu_SyntaxError, ("unexpected operator %d[%s]" % (symbol, Mu.i2a(symbol)), self)

  def _step_empty_operator__stack_mainfunction_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_mainfunction(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_function_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_function(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_staticfunction_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_staticfunction(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_imainfunction_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_imainfunction(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_ifunction_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_ifunction(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_istaticfunction_define(self, symbol, empty_operator):
    fun_ord = self.stack.latest(self).asInt()
    self.mu_board.add_istaticfunction(fun_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_operator_define(self, symbol, empty_operator):
    op_ord = self.stack.latest(self).asInt()
    self.mu_board.add_operator(op_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__stack_ioperator_define(self, symbol, empty_operator):
    op_ord = self.stack.latest(self).asInt()
    self.mu_board.add_ioperator(op_ord, self.cur, self.dir)
    self.set_completed()
    
  def _step_empty_operator__absorber(self, symbol, empty_operator):
    self.set_completed()

  def _step_empty_operator__bridge(self, symbol, empty_operator):
    pass

  def _step_empty_operator__end(self, symbol, empty_operator):
    self.set_completed()
    self.mu_board.mu.completed = True

  def _step_empty_operator__function_return(self, symbol, empty_operator):
    self.set_op(self.__class__._step_unary_operator__function_return)

  def _step_unary_operator__function_return(self, symbol, empty_operator):
    self.frame.REGISTER_RETURN_SYMBOL = symbol
    for thread in set(self.frame.threads):
      thread.set_completed()

  def _step_empty_operator__stack_char_input(self, symbol, empty_operator):
    mult = self.operator_multiplicity
    for i in xrange(mult):
      #inp = self.mu_board.mu.stdin.read(1)
      inp = getchar.getchar(self.mu_board.mu.stdin)
      #print '<%s:%s:%s>' % (inp, repr(inp), mult)
      self.stack._push(self, Mu_Str(inp))

  def _step_empty_operator__stack_ascii_input(self, symbol, empty_operator):
    mult = self.operator_multiplicity
    for i in xrange(mult):
      #inp = raw_input()
      inp = self.mu_board.mu.stdin.readline().rstrip('\n')
      self.stack._push(self, Mu_Str(inp))

  def _step_empty_operator__stack_integer_input(self, symbol, empty_operator):
    mult = self.operator_multiplicity
    for i in xrange(mult):
      #inp = raw_input()
      inp = self.mu_board.mu.stdin.readline().rstrip('\n')
      try:
        i = int(inp)
      except ValueError, e:
        raise Mu_RuntimeError, ("invalid integer in input: %s" % inp, self)
      self.stack.push(self, i)

  def _step_empty_operator__hold(self, symbol, empty_operator):
    self.mu_board.mu.mark_holding(self)

  def _step_empty_operator__release(self, symbol, empty_operator):
    self.mu_board.mu.mark_releasing(self)

  def _step_empty_operator__stack_move_to_loc(self, symbol, empty_operator):
    mult = self.operator_multiplicity
    if mult > len(self.stack):
      raise Mu_RuntimeError, ("invalid multiplicity %d for operator %d[%s]: cur_stack has %d items" % (mult, symbol, Mu.i2a(symbol), len(self.stack)), self)
    if self.stack is self.local_stack:
      raise Mu_RuntimeError, ("cannot copy loc_stack to loc_stack", self)
    l = self.stack.data[-mult:]
    l.reverse()
    #print "---", id(self), self.cur, self.dir, self.local_stack, self.stack, l
    self.local_stack.data.extend(l)
    del self.stack.data[-mult:]

  def _step_empty_operator__stack_move_from_loc(self, symbol, empty_operator):
    mult = self.operator_multiplicity
    if mult > len(self.local_stack):
      raise Mu_RuntimeError, ("invalid multiplicity %d for operator %d[%s]: loc_stack has %d items" % (mult, symbol, Mu.i2a(symbol), len(self.stack)), self)
    if self.stack is self.local_stack:
      raise Mu_RuntimeError, ("cannot copy loc_stack to loc_stack", self)
    l = self.local_stack.data[-mult:]
    l.reverse()
    self.stack.data.extend(l)
    del self.local_stack.data[-mult:]

  def _step_empty_operator__stack_pop(self, symbol, empty_operator):
    self.stack.pop(self)

  def _step_empty_operator__pass(self, symbol, empty_operator):
    pass

#  def _step_empty_operator__set_unary_operator(self, symbol, empty_operator):
#    self.op = unary_operator

  def _step_empty_operator__stack_up(self, symbol, empty_operator):
    for i in xrange(self.operator_multiplicity):
      if self.stack_thread.parent_thread:
        self.stack_threads.append(self.stack_thread)
        self.stack_thread = self.stack_thread.parent_thread
        self._set_stack()
      else:
        raise Mu_RuntimeError, ("stack_up: cannot get parent_thread", self)

  def _step_empty_operator__stack_down(self, symbol, empty_operator):
    for i in xrange(self.operator_multiplicity):
      if self.stack_threads:
        self.stack_thread = self.stack_threads.pop()
        self._set_stack()
      else:
        raise Mu_RuntimeError, ("stack_down: cannot get child_thread", self)

  def _step_empty_operator__stack_function_load_and_call(self, symbol, empty_operator):
    fun_ord = self.stack.pop_latest(self).asInt()
    self.call_function = self.mu_board.get_function(fun_ord, self)
    self.set_op(self.__class__._step_empty_operator__stack_function_load_and_call_trace)
    self.call_mult = self.operator_multiplicity
    return self._step_function(symbol, self.op)

  def _step_empty_operator__stack_function_load_and_call_trace(self, symbol, empty_operator):
    if self.call_mult > 0:
      self.call_function(self)
      self.call_mult -= 1
      self.cur = self.cur[0]-self.dir[0], self.cur[1]-self.dir[1]
    else:
      self.unset_op()

  def _step_empty_operator__fork(self, symbol, empty_operator):
    branch_group = Mu_ThreadGroup(self.mu_board, self.group)
    for dir in Mu.DIRECTIONS_FORK[self.dir]:
      sym = Mu.DIRECTION_SYMBOL[dir]
      new_i, new_j = self.cur[0]+dir[0], self.cur[1]+dir[1]
      if not self.mu_board.matrix[new_i][new_j] in Mu.DIRECTIONS_INVALID_SYMBOLS[dir]:
        new_thread = self.frame.new_thread(self, self.cur, dir, None, group=branch_group, clone_stack=True)
        self.mu_board.add_thread(new_thread)
    self.set_completed()

  def _step_empty_operator__join(self, symbol, empty_operator):
    self.mu_board.mu.add_join_waiter(self)

  def _step_empty_operator__serialize(self, symbol, empty_operator):
    branch_group = self.group
    dir_i, dir_j = self.dir
    inv_dir = (-dir_i, -dir_j)
    serialized_threads = []
    for dir in Mu.DIRECTIONS_FORK[self.dir]:
      if dir == inv_dir:
        continue
      sym = Mu.DIRECTION_SYMBOL[dir]
      new_i, new_j = self.cur[0]+dir[0], self.cur[1]+dir[1]
      if not self.mu_board.matrix[new_i][new_j] in Mu.DIRECTIONS_INVALID_SYMBOLS[dir]:
        branch_group = Mu_ThreadGroup(self.mu_board, self.group)
        new_thread = self.frame.new_thread(self, self.cur, dir, None, group=branch_group, clone_stack=True)
        self.mu_board.add_thread(new_thread)
        serialized_threads.append(new_thread)
    self.mu_board.mu.add_serial_waiters(serialized_threads)
    self.set_completed()

  def _step_empty_operator__hinge(self, symbol, empty_operator):
    candidates = []
    for dir in Mu.DIRECTIONS_FORK[self.dir]:
      new_i, new_j = self.cur[0]+dir[0], self.cur[1]+dir[1]
      if not self.mu_board.matrix[new_i][new_j] in Mu.DIRECTIONS_INVALID_SYMBOLS[dir] + (Mu.SYM_HINGE, ):
        candidates.append(dir)
    if len(candidates) == 0:
      raise Mu_SyntaxError, ("invalid hinge", self)
    elif len(candidates) > 1:
      raise Mu_SyntaxError, ("multiple hinge", self)
    self.dir = candidates[0]

#  def _step_empty_operator__direction(self, symbol, empty_operator):
#    self.dir = Mu.DIRECTIONS_COMPOSITION[self.dir][symbol]

  def _step_empty_operator__vertical(self, symbol, empty_operator):
    #if self.dir[1] != 0:
    self.dir = Mu.COMPOSITION_VERTICAL[self.dir]

  def _step_empty_operator__inv_diagonal(self, symbol, empty_operator):
    self.dir = Mu.COMPOSITION_INV_DIAGONAL[self.dir]

  def _step_empty_operator__horizontal(self, symbol, empty_operator):
    #if self.dir[0] != 0:
    self.dir = Mu.COMPOSITION_HORIZONTAL[self.dir]

  def _step_empty_operator__diagonal(self, symbol, empty_operator):
    self.dir = Mu.COMPOSITION_DIAGONAL[self.dir]

  def _step_empty_operator__stack_increment(self, symbol, empty_operator):
    self.stack.increment(self)

  def _step_empty_operator__stack_decrement(self, symbol, empty_operator):
    self.stack.decrement(self)

  def _step_empty_operator__stack_rotate_left(self, symbol, empty_operator):
    self.stack.rotate_left(self)

  def _step_empty_operator__stack_rotate_right(self, symbol, empty_operator):
    self.stack.rotate_right(self)

  def _step_empty_operator__stack_reverse(self, symbol, empty_operator):
    self.stack.reverse(self)

  def _step_empty_operator__stack_length(self, symbol, empty_operator):
    self.stack.length(self)

  def _step_empty_operator__stack_duplicate(self, symbol, empty_operator):
    self.stack.duplicate(self)

  def _step_empty_operator__stack_clear(self, symbol, empty_operator):
    self.stack.clear(self)

  def _step_empty_operator__stack_copy(self, symbol, empty_operator):
    if self.stack_thread.parent_thread:
      parent_stack = self.stack_thread.parent_thread.stack
    else:
      raise Mu_RuntimeError, ("stack_up: cannot get parent_thread", self)
    for i in xrange(self.operator_multiplicity):
      self.stack.copy(self, parent_stack)

  def _step_empty_operator__stack_negate(self, symbol, empty_operator):
    self.stack.negate(self)

  def _step_empty_operator__stack_join(self, symbol, empty_operator):
    self.stack.join(self)

  def _step_empty_operator__stack_split(self, symbol, empty_operator):
    self.stack.split(self)

  def _step_empty_operator__stack_ascii_print(self, symbol, empty_operator):
    self.stack.ascii_print(self)

  def _step_empty_operator__stack_debug_print(self, symbol, empty_operator):
    self.stack.debug_stack_put(self)

  def _step_empty_operator__stack_integer_print(self, symbol, empty_operator):
    self.stack.integer_print(self)

  def _step_empty_operator__obstacle(self, symbol, empty_operator):
    self.dir = -self.dir[0], -self.dir[1]

  def _step_empty_operator__stack_load(self, symbol, empty_operator):
    symbol = self.stack.latest(self).asInt()
    empty_operator = self.mu_board.step_operator[symbol]
    return self._step_function(symbol, empty_operator)

  def _step_empty_operator__stack_digit(self, symbol, empty_operator):
    self.stack.push(self, symbol-Mu.SYM_0)

  def __str__(self):
    return 'CUR=(%2d, %2d)[%c], DIR=(%2d, %2d)[%c:%s], OP=%s, ID=%s, FRAME=%s, WAIT=%s' % (
		self.cur[0], self.cur[1], self.mu_board.matrix[self.cur[0]][self.cur[1]],
		self.dir[0], self.dir[1], Mu.DIRECTION_SYMBOL[self.dir], Mu.DIRECTION_NAME[self.dir][0],
		self.op,
		id(self),
		repr(self.frame),
		self.wait_frame is not None,
    )
  def __repr__(self):
    return '%s<%s>' % (
		self.__class__.__name__,
		str(self),
    )

      
MU_MAX_ORD = 128
_LOG_MU_MAX_ORD2 = math.log(MU_MAX_ORD+2)
def Mu_l2a(l):
  return ''.join(Mu_i2a(e) for e in l)

def Mu_a2l(a):
  return [Mu_a2i(e) for e in a.split('')]

def Mu_l2i(l):
  result = 0
  for i in l:
    f = MU_MAX_ORD**int(math.ceil(math.log(i+2)/_LOG_MU_MAX_ORD2))
    result = (result*f)+i
  return result

def Mu_i2l(i):
  if i<Mu.MAX_ORD:
    return [i]
  else:
    l = []
    while i>0:
      i, m = divmod(i, MU_MAX_ORD)
      l.append(m)
    l.reverse()
    return l

def Mu_a2i(s):
  result = 0
  for c in s:
    result = (result*MU_MAX_ORD)+ord(c)
  return result

def Mu_i2a(i):
  if i<MU_MAX_ORD:
    return chr(i)
  else:
    l = []
    while i>0:
      i, m = divmod(i, MU_MAX_ORD)
      l.append(chr(m))
    l.reverse()
    return ''.join(l)

class Mu(object):
  ESCAPE_SYMBOL = Mu_a2i('\\')
  ESCAPED_SYMBOLS = {
	Mu_a2i('n'):Mu_a2i('\n'),
	Mu_a2i('b'):Mu_a2i('\b'),
	Mu_a2i('t'):Mu_a2i('\t'),
	Mu_a2i('r'):Mu_a2i('\r'),
  }
  SYM_0 = Mu_a2i('0')
  SYM_9 = Mu_a2i('9')
  SYM_a = Mu_a2i('a')
  SYM_z = Mu_a2i('z')
  SYM_A = Mu_a2i('A')
  SYM_Z = Mu_a2i('Z')
  SYM_SIGN_PLUS = Mu_a2i('+')
  SYM_SIGN_MINUS = Mu_a2i('-')
  SYM_MIN = 0
  SYM_MAX = 127
  MAX_ORD = MU_MAX_ORD
  DIR_C  = ( 0,  0)
  DIR_N  = (-1,  0)
  DIR_NE = (-1,  1)
  DIR_E  = ( 0,  1)
  DIR_SE = ( 1,  1)
  DIR_S  = ( 1,  0)
  DIR_SW = ( 1, -1)
  DIR_W  = ( 0, -1)
  DIR_NW = (-1, -1)
  SYM_WHITESPACE				= Mu_a2i(' ')
  SYM_START					= Mu_a2i('`')
  SYM_VERTICAL					= Mu_a2i('|')
  SYM_HORIZONTAL				= Mu_a2i('-')
  SYM_DIAGONAL					= Mu_a2i('\\')
  SYM_INV_DIAGONAL				= Mu_a2i('/')
  SYM_OBSTACLE					= Mu_a2i('X')
  SYM_ABSORBER					= Mu_a2i('#')
  SYM_STACK_INCREMENT				= Mu_a2i('+')
  SYM_STACK_DECREMENT				= Mu_a2i('_')
  SYM_STACK_DUPLICATE				= Mu_a2i('d')
  SYM_STACK_CLEAR				= Mu_a2i('c')
  SYM_STACK_COPY				= Mu_a2i('q')
  SYM_STACK_NEGATE				= Mu_a2i('!')
  SYM_STACK_PUSH				= Mu_a2i("'")
  SYM_STACK_ESCAPED_PUSH			= Mu_a2i('~')
  SYM_STACK_POP					= Mu_a2i('P')
  SYM_STACK_ASCII_PRINT				= Mu_a2i(':')
  SYM_STACK_INTEGER_PRINT			= Mu_a2i(';')
  SYM_STACK_DEBUG_PRINT				= Mu_a2i('D')
  SYM_STACK_IOPERATOR_DEFINE			= Mu_a2i('o')
  SYM_STACK_IFUNCTION_DEFINE			= Mu_a2i('f')
  SYM_STACK_ISTATICFUNCTION_DEFINE		= Mu_a2i('s')
  SYM_STACK_OPERATOR_DEFINE			= Mu_a2i('O')
  SYM_STACK_FUNCTION_DEFINE			= Mu_a2i('F')
  SYM_STACK_STATICFUNCTION_DEFINE		= Mu_a2i('S')
  SYM_STACK_FUNCTION_LOAD_AND_CALL		= Mu_a2i('&')
  SYM_STACK_LOAD				= Mu_a2i('Y')
  SYM_STACK_UP					= Mu_a2i('^')
  SYM_STACK_DOWN				= Mu_a2i('v')
  SYM_STACK_IF_POSITIVE				= Mu_a2i('>')
  SYM_STACK_IF_NEGATIVE				= Mu_a2i('<')
  SYM_STACK_IF_NONZERO				= Mu_a2i('?')
  SYM_STACK_IF_ZERO				= Mu_a2i('=')
  SYM_STACK_STRING_BEGIN			= Mu_a2i('"')
  SYM_STACK_STRING_END				= Mu_a2i('"')
  SYM_STACK_INT_BEGIN				= Mu_a2i('[')
  SYM_STACK_INT_END				= Mu_a2i(']')
  SYM_STACK_JOIN				= Mu_a2i('J')
  SYM_STACK_SPLIT				= Mu_a2i('K')
  SYM_STACK_LENGTH				= Mu_a2i('l')
  SYM_STACK_ROTATE_LEFT				= Mu_a2i('L')
  SYM_STACK_ROTATE_RIGHT			= Mu_a2i('R')
  SYM_STACK_REVERSE				= Mu_a2i('z')
  SYM_STACK_MOVE_TO_LOC				= Mu_a2i('m')
  SYM_STACK_MOVE_FROM_LOC			= Mu_a2i('M')
  SYM_IOPERATOR_BEGIN				= Mu_a2i('o')
  SYM_IFUNCTION_BEGIN				= Mu_a2i('f')
  SYM_ISTATICFUNCTION_BEGIN			= Mu_a2i('s')
  SYM_OPERATOR_BEGIN				= Mu_a2i('O')
  SYM_STATICFUNCTION_BEGIN			= Mu_a2i('S')
  SYM_FUNCTION_BEGIN				= Mu_a2i('F')
  SYM_FUNCTION_RETURN				= Mu_a2i('$')
  SYM_LAMBDA_BEGIN				= Mu_a2i('(')
  SYM_LAMBDA_RETURN				= Mu_a2i(')')
  SYM_MAINFUNCTION_BEGIN			= Mu_a2i("B")
  SYM_MAINFUNCTION_DEFINE			= Mu_a2i("B")
  SYM_IMAINFUNCTION_BEGIN			= Mu_a2i("b")
  SYM_IMAINFUNCTION_DEFINE			= Mu_a2i("b")
  SYM_BEGIN_AND_HOLD				= Mu_a2i('H')
  SYM_BLOCK_BEGIN				= Mu_a2i('{')
  SYM_BLOCK_RETURN				= Mu_a2i('}')
  SYM_FUNCTION_CALL				= Mu_a2i('C')
  SYM_END					= Mu_a2i('E')
  SYM_BRIDGE					= Mu_a2i('.')
  SYM_FORK					= Mu_a2i('*')
  SYM_JOIN					= Mu_a2i('@')
  SYM_SERIALIZE					= Mu_a2i('%')
  SYM_HINGE					= Mu_a2i(',')
  SYM_IGNORE					= Mu_a2i('i')
  SYM_WAIT					= Mu_a2i('w')
  SYM_STACK_CHAR_INPUT				= Mu_a2i('a')
  SYM_STACK_ASCII_INPUT				= Mu_a2i('A')
  SYM_STACK_INTEGER_INPUT			= Mu_a2i('I')
  SYM_HOLD					= Mu_a2i('h')
  SYM_RELEASE					= Mu_a2i('r')
  SYM_OPERATOR_MULTIPLIER			= Mu_a2i('x')
  SYM_GLOBAL_VARIABLE_SET			= Mu_a2i('N')
  SYM_LOCAL_VARIABLE_SET			= Mu_a2i('n')
  SYM_VARIABLE_GET				= Mu_a2i('V')
  SYM_VARIABLE_DEL				= Mu_a2i('W')
  SYM_EXCEPTION_RAISE				= Mu_a2i('e')
  SYM_EXCEPTION_SET_HANDLER			= Mu_a2i('t')
  SYM_EXCEPTION_UNSET_HANDLER			= Mu_a2i('T')
  DIRECTION_SYMBOL = {
		DIR_C:	SYM_BRIDGE,
		DIR_E:	SYM_HORIZONTAL,
		DIR_SE:	SYM_DIAGONAL,
		DIR_S:	SYM_VERTICAL,
		DIR_SW:	SYM_INV_DIAGONAL,
		DIR_W:	SYM_HORIZONTAL,
		DIR_NW:	SYM_DIAGONAL,
		DIR_N:	SYM_VERTICAL,
		DIR_NE:	SYM_INV_DIAGONAL,
  }
  DIRECTION_NAME = {
		DIR_C:	("C",  "CENTER"),
		DIR_E:	("E",  "EAST"),
		DIR_SE:	("SE", "SOUTH-EAST"),
		DIR_S:	("S",  "SOUTH"),
		DIR_SW:	("SW", "SOUTH-WEST"),
		DIR_W:	("W",  "WEST"),
		DIR_NW:	("NW", "NORTH-WEST"),
		DIR_N:	("N",  "NORTH"),
		DIR_NE:	("NE", "NORTH-EAST"),
  }
  DIRECTIONS_FORK = {
			DIR_E:	(DIR_E, DIR_SE, DIR_S, DIR_SW,        DIR_NW, DIR_N, DIR_NE),
			DIR_SE:	(DIR_E, DIR_SE, DIR_S, DIR_SW, DIR_W,         DIR_N, DIR_NE),
			DIR_S:	(DIR_E, DIR_SE, DIR_S, DIR_SW, DIR_W, DIR_NW,        DIR_NE),
			DIR_SW:	(DIR_E, DIR_SE, DIR_S, DIR_SW, DIR_W, DIR_NW, DIR_N        ),
			DIR_W:	(       DIR_SE, DIR_S, DIR_SW, DIR_W, DIR_NW, DIR_N, DIR_NE),
			DIR_NW:	(DIR_E,         DIR_S, DIR_SW, DIR_W, DIR_NW, DIR_N, DIR_NE),
			DIR_N:	(DIR_E, DIR_SE,        DIR_SW, DIR_W, DIR_NW, DIR_N, DIR_NE),
			DIR_NE:	(DIR_E, DIR_SE, DIR_S,         DIR_W, DIR_NW, DIR_N, DIR_NE),
  }
  DIRECTIONS_INVALID_SYMBOLS = {
					DIR_E:	(SYM_VERTICAL,                 SYM_DIAGONAL, SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_SE:	(SYM_VERTICAL, SYM_HORIZONTAL,               SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_S:	(              SYM_HORIZONTAL, SYM_DIAGONAL, SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_SW:	(SYM_VERTICAL, SYM_HORIZONTAL, SYM_DIAGONAL,                   SYM_WHITESPACE, SYM_ABSORBER),
					DIR_W:	(SYM_VERTICAL,                 SYM_DIAGONAL, SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_NW:	(SYM_VERTICAL, SYM_HORIZONTAL,               SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_N:	(              SYM_HORIZONTAL, SYM_DIAGONAL, SYM_INV_DIAGONAL, SYM_WHITESPACE, SYM_ABSORBER),
					DIR_NE:	(SYM_VERTICAL, SYM_HORIZONTAL, SYM_DIAGONAL,                   SYM_WHITESPACE, SYM_ABSORBER),
  }
  COMPOSITION_VERTICAL = {
				DIR_E:	DIR_W,
				DIR_SE:	DIR_SW,
				DIR_S:	DIR_S,
				DIR_SW:	DIR_SE,
				DIR_W:	DIR_E,
				DIR_NW:	DIR_NE,
				DIR_N:	DIR_N,
				DIR_NE:	DIR_NW,
  }
  COMPOSITION_INV_DIAGONAL = {
				DIR_E:	DIR_N,
				DIR_SE:	DIR_NW,
				DIR_S:	DIR_W,
				DIR_SW:	DIR_SW,
				DIR_W:	DIR_S,
				DIR_NW:	DIR_SE,
				DIR_N:	DIR_E,
				DIR_NE:	DIR_NE,
  }
  COMPOSITION_HORIZONTAL = {
				DIR_E:	DIR_E,
				DIR_SE:	DIR_NE,
				DIR_S:	DIR_N,
				DIR_SW:	DIR_NW,
				DIR_W:	DIR_W,
				DIR_NW:	DIR_SW,
				DIR_N:	DIR_S,
				DIR_NE:	DIR_SE,
  }
  COMPOSITION_DIAGONAL = {
				DIR_E:	DIR_S,
				DIR_SE:	DIR_SE,
				DIR_S:	DIR_E,
				DIR_SW:	DIR_NE,
				DIR_W:	DIR_N,
				DIR_NW:	DIR_NW,
				DIR_N:	DIR_W,
				DIR_NE:	DIR_SW,
  }
						
						
  DIRECTIONS_COMPOSITION = {     
				DIR_E:	{     # SYM_HORIZONTAL
						SYM_VERTICAL:		DIR_W,
						SYM_INV_DIAGONAL:	DIR_N,
						SYM_HORIZONTAL:		DIR_E,
						SYM_DIAGONAL:		DIR_S,
					},
				DIR_SE:	{     # SYM_DIAGONAL
						SYM_VERTICAL:		DIR_SW,
						SYM_INV_DIAGONAL:	DIR_NW,
						SYM_HORIZONTAL:		DIR_NE,
						SYM_DIAGONAL:		DIR_SE,
					},
				DIR_S:	{     # SYM_VERTICAL
						SYM_VERTICAL:		DIR_S,
						SYM_INV_DIAGONAL:	DIR_W,
						SYM_HORIZONTAL:		DIR_N,
						SYM_DIAGONAL:		DIR_E,
					},
				DIR_SW:	{     # SYM_INV_DIAGONAL
						SYM_VERTICAL:		DIR_SE,
						SYM_INV_DIAGONAL:	DIR_SW,
						SYM_HORIZONTAL:		DIR_NW,
						SYM_DIAGONAL:		DIR_NE,
					},
				DIR_W:	{     # SYM_HORIZONTAL
						SYM_VERTICAL:		DIR_E,
						SYM_INV_DIAGONAL:	DIR_S,
						SYM_HORIZONTAL:		DIR_W,
						SYM_DIAGONAL:		DIR_N,
					},
				DIR_NW:	{     # SYM_DIAGONAL
						SYM_VERTICAL:		DIR_NE,
						SYM_INV_DIAGONAL:	DIR_SE,
						SYM_HORIZONTAL:		DIR_SW,
						SYM_DIAGONAL:		DIR_NW,
					},
				DIR_N:	{     # SYM_VERTICAL
						SYM_VERTICAL:		DIR_N,
						SYM_INV_DIAGONAL:	DIR_E,
						SYM_HORIZONTAL:		DIR_S,
						SYM_DIAGONAL:		DIR_W,
					},
				DIR_NE:	{     # SYM_INV_DIAGONAL
						SYM_VERTICAL:		DIR_NW,
						SYM_INV_DIAGONAL:	DIR_NE,
						SYM_HORIZONTAL:		DIR_SE,
						SYM_DIAGONAL:		DIR_SW,
					},
  }
  TRANSLATION = {
			'\\t':		'        ',
  }
  DIRECTIONS = (
		DIR_E,
		DIR_SE,
		DIR_S,
		DIR_SW,
		DIR_W,
		DIR_NW,
		DIR_N,
		DIR_NE,
  )

  OPERATOR = {
	"BRIDGE":			(
						"Continue thread",
						None,
					),
	"ABSORBER":			(
						"Delete a thread",
						None,
					),
	"STACK_DIGIT":			(
						"Put a 1-digit integer on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_digit,
					),
	"STACK_POP":			(
						"Pop 1 item from CUR-STACK",
						Mu_Thread._step_empty_operator__stack_pop,
					),
	"STACK_DOWN":			(
						"Make CUR-STACK point 1 thread down",
						Mu_Thread._step_empty_operator__stack_down,
					),
	"STACK_UP":			(
						"Make CUR-STACK point 1 thread up",
						Mu_Thread._step_empty_operator__stack_up,
					),
	"STACK_LOAD":			(
						"Load operator from CUR-STACK",
						Mu_Thread._step_empty_operator__stack_load,
					),
	"STACK_INCREMENT":		(
						"Increment last item on CUR_STACK",
						Mu_Thread._step_empty_operator__stack_increment,
					),
	"STACK_DECREMENT":		(
						"Increment last item on CUR_STACK",
						Mu_Thread._step_empty_operator__stack_decrement,
					),
	"STACK_ROTATE_LEFT":		(
						"Left-rotate CUR-STACK",
						Mu_Thread._step_empty_operator__stack_rotate_left,
					),
	"STACK_ROTATE_RIGHT":		(
						"Right-rotate CUR-STACK",
						Mu_Thread._step_empty_operator__stack_rotate_right,
					),
	"STACK_REVERSE":		(
						"Right-rotate CUR-STACK",
						Mu_Thread._step_empty_operator__stack_reverse,
					),
	"STACK_CLEAR":			(
						"Clear CUR-STACK",
						Mu_Thread._step_empty_operator__stack_clear,
					),
	"STACK_COPY":			(
						"Copy CUR-STACK",
						Mu_Thread._step_empty_operator__stack_copy,
					),
	"STACK_DUPLICATE":		(
						"Duplicate last item on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_duplicate,
					),
	"STACK_NEGATE":			(
						"Negate last item CUR-STACK",
						Mu_Thread._step_empty_operator__stack_negate,
					),
	"STACK_JOIN":			(
						"Join last two items on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_join,
					),
	"STACK_SPLIT":			(
						"Split last item on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_split,
					),
	"STACK_MOVE_TO_LOC":		(
						"Move last item on CUR-STACK to LOC-STACK",
						Mu_Thread._step_empty_operator__stack_move_to_loc,
					),
	"STACK_MOVE_FROM_LOC":		(
						"Move last item on LOC-STACK to CUR-STACK",
						Mu_Thread._step_empty_operator__stack_move_from_loc,
					),
	"STACK_INTEGER_PRINT":		(
						"Print last item on CUR-STACK as integer",
						Mu_Thread._step_empty_operator__stack_integer_print,
					),
	"STACK_ASCII_PRINT":		(
						"Print last item on CUR-STACK as ascii",
						Mu_Thread._step_empty_operator__stack_ascii_print,
					),
	"STACK_DEBUG_PRINT":		(
						"Print CUR-STACK (debug)",
						Mu_Thread._step_empty_operator__stack_debug_print,
					),
	"VERTICAL":			(
						"S<->N direction",
						Mu_Thread._step_empty_operator__vertical,
					),
	"HORIZONTAL":			(
						"E<->W direction",
						Mu_Thread._step_empty_operator__horizontal,
					),
	"DIAGONAL":			(
						"SW<->NE direction",
						Mu_Thread._step_empty_operator__diagonal,
					),
	"INV_DIAGONAL":			(
						"SE<->NW direction",
						Mu_Thread._step_empty_operator__inv_diagonal,
					),
	"OBSTACLE":			(
						"Reflect the thread",
						Mu_Thread._step_empty_operator__obstacle,
					),
	"MAINFUNCTION_BEGIN":		(
						"Begin a MAIN thread",
						Mu_Thread._step_empty_operator__fork,
					),
	"IMAINFUNCTION_BEGIN":		(
						"Begin an IMAIN thread",
						Mu_Thread._step_empty_operator__fork,
					),
	"BEGIN_AND_HOLD":		(
						"Begin a thread and hold other threads",
						Mu_Thread._step_empty_operator__fork,
					),
	"FORK":				(
						"Fork a thread",
						Mu_Thread._step_empty_operator__fork,
					),
	"JOIN":				(
						"Join threads",
						Mu_Thread._step_empty_operator__join,
					),
	"SERIALIZE":			(
						"Serialize threads",
						Mu_Thread._step_empty_operator__serialize,
					),
	"HINGE":			(
						"Change thread direction",
						Mu_Thread._step_empty_operator__hinge,
					),
	"STACK_IOPERATOR_DEFINE":	(
						"Define an internal operator",
						Mu_Thread._step_empty_operator__stack_ioperator_define,
					),
	"STACK_OPERATOR_DEFINE":	(
						"Define an operator",
						Mu_Thread._step_empty_operator__stack_operator_define,
					),
	"STACK_IMAINFUNCTION_DEFINE":	(
						"Define an internal MAIN function",
						Mu_Thread._step_empty_operator__stack_imainfunction_define,
					),
	"STACK_MAINFUNCTION_DEFINE":	(
						"Define a MAIN function",
						Mu_Thread._step_empty_operator__stack_mainfunction_define,
					),
	"STACK_IFUNCTION_DEFINE":	(
						"Define an internal function",
						Mu_Thread._step_empty_operator__stack_ifunction_define,
					),
	"STACK_FUNCTION_DEFINE":	(
						"Define a function",
						Mu_Thread._step_empty_operator__stack_function_define,
					),
	"STACK_ISTATICFUNCTION_DEFINE":	(
						"Define an internal static function",
						Mu_Thread._step_empty_operator__stack_istaticfunction_define,
					),
	"STACK_STATICFUNCTION_DEFINE":	(
						"Define a static function",
						Mu_Thread._step_empty_operator__stack_staticfunction_define,
					),
	"STACK_FUNCTION_LOAD_AND_CALL":	(
						"Load a function whose name is last item on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_function_load_and_call,
					),
	"FUNCTION_RETURN":		(
						"Returns from a function",
						Mu_Thread._step_empty_operator__function_return,
					),
	"LAMBDA_BEGIN":			(
						"Begin a lambda function",
						Mu_Thread._step_empty_operator__lambda_begin,
					),
	"LAMBDA_RETURN":		(
						"Return from a lambda function",
						Mu_Thread._step_empty_operator__lambda_return,
					),
	"BLOCK_BEGIN":			(
						"Begin a block",
						Mu_Thread._step_empty_operator__block_begin,
					),
	"BLOCK_RETURN":			(
						"Return from a block",
						Mu_Thread._step_empty_operator__block_return,
					),
	"END":				(
						"End the program",
						Mu_Thread._step_empty_operator__end,
					),
	"WAIT":				(
						"Wait one cycle",
						Mu_Thread._step_empty_operator__wait,
					),
	"STACK_CHAR_INPUT":		(
						"Read a single char and push it on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_char_input,
					),
	"STACK_ASCII_INPUT":		(
						"Read an ascii string and push it on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_ascii_input,
					),
	"STACK_INTEGER_INPUT":		(
						"Read an integer and push it on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_integer_input,
					),
	"HOLD":				(
						"Hold other threads",
						Mu_Thread._step_empty_operator__hold,
					),
	"RELEASE":			(
						"Release held threads",
						Mu_Thread._step_empty_operator__release,
					),
	"STACK_STRING_BEGIN":		(
						"Begin a string",
						Mu_Thread._step_empty_operator__stack_string_begin,
					),
	"STACK_STRING_END":		(
						"End a string and push it on CUR-STACK",
						None,
					),
	"STACK_INT_BEGIN":		(
						"Begin an integer",
						Mu_Thread._step_empty_operator__stack_int_begin,
					),
	"STACK_INT_END":		(
						"End an integer and push it on CUR-STACK",
						None,
					),
	"STACK_OPERATOR_MULTIPLIER":	(
						"Apply multiplier given by last item on CUR-STACK to next multipliable operator",
						Mu_Thread._step_empty_operator__stack_operator_multiplier,
					),
	"STACK_LENGTH":			(
						"Push CUR-STACK length on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_length,
					),
	"EXCEPTION_RAISE":		(
						"Raise an exception",
						Mu_Thread._step_empty_operator__exception_raise,
					),
	"EXCEPTION_SET_HANDLER":	(
						"Set an exception handler",
						Mu_Thread._step_empty_operator__exception_set_handler,
					),
	"EXCEPTION_UNSET_HANDLER":	(
						"Unset the exception",
						Mu_Thread._step_empty_operator__exception_unset_handler,
					),
	"IGNORE":			(
						"Ignore next character on thread",
						Mu_Thread._step_empty_operator__ignore,
					),
	"FUNCTION_CALL":		(
						"Call function whose name is given by next character on thread",
						Mu_Thread._step_empty_operator__function_call,
					),
	"STACK_PUSH":			(
						"Push next thread character on CUR-STACK",
						Mu_Thread._step_empty_operator__stack_push,
					),
	"STACK_ESCAPED_PUSH":			(
						"Push next thread character on CUR-STACK, with an escape",
						Mu_Thread._step_empty_operator__stack_escaped_push,
					),
	"STACK_IF_POSITIVE":		(
						"Use next thread character only if last item on CUR-STACK is not positive",
						Mu_Thread._step_empty_operator__stack_if_positive,
					),
	"STACK_IF_NEGATIVE":		(
						"Use next thread character only if last item on CUR-STACK is not negative",
						Mu_Thread._step_empty_operator__stack_if_negative,
					),
	"STACK_IF_NONZERO":		(
						"Use next thread character only if last item on CUR-STACK is zero",
						Mu_Thread._step_empty_operator__stack_if_nonzero,
					),
	"STACK_IF_ZERO":		(
						"Use next thread character only if last item on CUR-STACK is nonzero",
						Mu_Thread._step_empty_operator__stack_if_zero,
					),
	"START":			(
						"Start a thread",
						Mu_Thread._step_empty_operator__fork,
					),
	"LOCAL_VARIABLE_SET":		(
						"Get the value of a local variable",
						Mu_Thread._step_empty_operator__local_variable_set,
					),
	"GLOBAL_VARIABLE_SET":		(
						"Set the value of a global variable",
						Mu_Thread._step_empty_operator__global_variable_set,
					),
	"VARIABLE_GET":			(
						"Get the value of a variable",
						Mu_Thread._step_empty_operator__variable_get,
					),
	"VARIABLE_DEL":			(
						"Del a variable",
						Mu_Thread._step_empty_operator__variable_del,
					),
	"UNEXPECTED":			(
						"An unexpected symbol; causes a syntax error",
						Mu_Thread._step_empty_operator__raise_unexpected_empty_operator,
					),
  }

  SYMBOL_OPERATOR = {
	SYM_START:				"START",
	SYM_ABSORBER:				"ABSORBER",
	SYM_OBSTACLE:				"OBSTACLE",
	SYM_BRIDGE:				"BRIDGE",
	SYM_IGNORE:				"IGNORE",
	SYM_FUNCTION_CALL:			"FUNCTION_CALL",
	SYM_STACK_PUSH:				"STACK_PUSH",
	SYM_STACK_ESCAPED_PUSH:			"STACK_ESCAPED_PUSH",
	SYM_STACK_IF_POSITIVE:			"STACK_IF_POSITIVE",
	SYM_STACK_IF_NEGATIVE:			"STACK_IF_NEGATIVE",
	SYM_STACK_IF_NONZERO:			"STACK_IF_NONZERO",
	SYM_STACK_IF_ZERO:			"STACK_IF_ZERO",
	SYM_STACK_POP:				"STACK_POP",
	SYM_STACK_DOWN:				"STACK_DOWN",
	SYM_STACK_UP:				"STACK_UP",
	SYM_STACK_INCREMENT:			"STACK_INCREMENT",
	SYM_STACK_DECREMENT:			"STACK_DECREMENT",
	SYM_STACK_ROTATE_LEFT:			"STACK_ROTATE_LEFT",
	SYM_STACK_ROTATE_RIGHT:			"STACK_ROTATE_RIGHT",
	SYM_STACK_REVERSE:			"STACK_REVERSE",
	SYM_STACK_CLEAR:			"STACK_CLEAR",
	SYM_STACK_COPY:				"STACK_COPY",
	SYM_STACK_DUPLICATE:			"STACK_DUPLICATE",
	SYM_STACK_NEGATE:			"STACK_NEGATE",
	SYM_STACK_JOIN:				"STACK_JOIN",
	SYM_STACK_SPLIT:			"STACK_SPLIT",
	SYM_STACK_MOVE_TO_LOC:			"STACK_MOVE_TO_LOC",
	SYM_STACK_MOVE_FROM_LOC:		"STACK_MOVE_FROM_LOC",
	SYM_STACK_INTEGER_PRINT:		"STACK_INTEGER_PRINT",
	SYM_STACK_ASCII_PRINT:			"STACK_ASCII_PRINT",
	SYM_STACK_DEBUG_PRINT:			"STACK_DEBUG_PRINT",
	SYM_STACK_LOAD:				"STACK_LOAD",
	SYM_VERTICAL:				"VERTICAL",
	SYM_HORIZONTAL:				"HORIZONTAL",
	SYM_DIAGONAL:				"DIAGONAL",
	SYM_INV_DIAGONAL:			"INV_DIAGONAL",
	SYM_MAINFUNCTION_BEGIN:			"MAINFUNCTION_BEGIN",
	SYM_MAINFUNCTION_DEFINE:		"STACK_MAINFUNCTION_DEFINE",
	SYM_IMAINFUNCTION_DEFINE:		"STACK_IMAINFUNCTION_DEFINE",
	SYM_BEGIN_AND_HOLD:			"BEGIN_AND_HOLD",
	SYM_FORK:				"FORK",
	SYM_JOIN:				"JOIN",
	SYM_SERIALIZE:				"SERIALIZE",
	SYM_HINGE:				"HINGE",
	SYM_STACK_IOPERATOR_DEFINE:		"STACK_IOPERATOR_DEFINE",
	SYM_STACK_IFUNCTION_DEFINE:		"STACK_IFUNCTION_DEFINE",
	SYM_STACK_ISTATICFUNCTION_DEFINE:	"STACK_ISTATICFUNCTION_DEFINE",
	SYM_STACK_OPERATOR_DEFINE:		"STACK_OPERATOR_DEFINE",
	SYM_STACK_FUNCTION_DEFINE:		"STACK_FUNCTION_DEFINE",
	SYM_STACK_STATICFUNCTION_DEFINE:	"STACK_STATICFUNCTION_DEFINE",
	SYM_STACK_FUNCTION_LOAD_AND_CALL:	"STACK_FUNCTION_LOAD_AND_CALL",
	SYM_FUNCTION_RETURN:			"FUNCTION_RETURN",
	SYM_LAMBDA_BEGIN:			"LAMBDA_BEGIN",
	SYM_LAMBDA_RETURN:			"LAMBDA_RETURN",
	SYM_BLOCK_BEGIN:			"BLOCK_BEGIN",
	SYM_BLOCK_RETURN:			"BLOCK_RETURN",
	SYM_END:				"END",
	SYM_WAIT:				"WAIT",
	SYM_STACK_CHAR_INPUT:			"STACK_CHAR_INPUT",
	SYM_STACK_ASCII_INPUT:			"STACK_ASCII_INPUT",
	SYM_STACK_INTEGER_INPUT:		"STACK_INTEGER_INPUT",
	SYM_HOLD:				"HOLD",
	SYM_RELEASE:				"RELEASE",
	SYM_STACK_STRING_BEGIN:			"STACK_STRING_BEGIN",
	SYM_STACK_INT_BEGIN:			"STACK_INT_BEGIN",
	SYM_OPERATOR_MULTIPLIER:		"STACK_OPERATOR_MULTIPLIER",
	SYM_STACK_LENGTH:			"STACK_LENGTH",
	SYM_EXCEPTION_RAISE:			"EXCEPTION_RAISE",
	SYM_EXCEPTION_SET_HANDLER:		"EXCEPTION_SET_HANDLER",
	SYM_EXCEPTION_UNSET_HANDLER:		"EXCEPTION_UNSET_HANDLER",
	SYM_GLOBAL_VARIABLE_SET:		"GLOBAL_VARIABLE_SET",
	SYM_LOCAL_VARIABLE_SET:			"LOCAL_VARIABLE_SET",
	SYM_VARIABLE_GET:			"VARIABLE_GET",
	SYM_VARIABLE_DEL:			"VARIABLE_DEL",
	Mu_a2i('0'):				"STACK_DIGIT",
	Mu_a2i('1'):				"STACK_DIGIT",
	Mu_a2i('2'):				"STACK_DIGIT",
	Mu_a2i('3'):				"STACK_DIGIT",
	Mu_a2i('4'):				"STACK_DIGIT",
	Mu_a2i('5'):				"STACK_DIGIT",
	Mu_a2i('6'):				"STACK_DIGIT",
	Mu_a2i('7'):				"STACK_DIGIT",
	Mu_a2i('8'):				"STACK_DIGIT",
	Mu_a2i('9'):				"STACK_DIGIT",
	SYM_WHITESPACE:				"ABSORBER",
  }
  FAKE_SYMBOL_OPERATOR = {
	SYM_STACK_STRING_END:			"STACK_STRING_END",
	SYM_STACK_INT_END:			"STACK_INT_END",
  }
  def __init__(self, stdin=None, stdout=None, stderr=None):
    self.itn = 0
    if stdin is None:
      stdin = sys.stdin
    self.stdin = stdin
    if stdout is None:
      stdout = sys.stdout
    self.stdout = stdout
    if stderr is None:
      stderr = sys.stderr
    self.stderr = stderr
    self.console = Mu_Console(self)
    self.completed = False
    self.functions = {}
    self.module_functions = {}
    self.held_threads = set()
    self.mark_holding_threads = set()
    self.mark_releasing_threads = set()
    self.holding_threads = set()
    self.boards = []
    self.threads = set()
    self.waiting_threads = set()
    self.join_waiters = {}
    self.serial_waiters = []
    self.global_variables = {}

   
  i2l = staticmethod(Mu_i2l)
  l2i = staticmethod(Mu_l2i)
  i2a = staticmethod(Mu_i2a)
  a2i = staticmethod(Mu_a2i)
  l2a = staticmethod(Mu_l2a)
  a2l = staticmethod(Mu_a2l)
  

  def del_thread(self, thread):
    if thread in self.threads:
      self.threads.remove(thread)
    else:
      #print "...", thread in self.held_threads
      #print "...", thread in self.mark_holding_threads
      #print "...", thread in self.mark_releasing_threads
      #print "...", thread in self.holding_threads
      #print "...", thread in self.waiting_threads
      self.waiting_threads.remove(thread)

  @classmethod
  def set_symbol_operator(clss):
    for i in xrange(Mu.SYM_MIN, Mu.SYM_MAX+1):
      clss.SYMBOL_OPERATOR.setdefault(i, "UNEXPECTED")

  def add_serial_waiters(self, threads):
    self.serial_waiters.append(threads)
    for thread in threads[1:]:
      thread.sleep()
    
  def add_join_waiter(self, thread):
    if thread.group in self.join_waiters:
      self.join_waiters[thread.group] += 1
    else:
      self.join_waiters[thread.group] = 1
    thread.sleep()

  def apply_join_waiters(self):
    #print ','.join("<%s>"%(group) for group in self.join_waiters.keys())
    for group, num_joint in self.join_waiters.items():
      if group is None:
        continue
      if len(group) == num_joint:
        parent_group = group.parent_group
        if parent_group is None:
          parent_group = Mu_ThreadGroup(group.mu_board, group)
        curs = {}
        for thread in group[:]:
          thread.wakeup()
          thread.set_completed()
          curs.setdefault(thread.cur, []).append(thread.dir)
        for cur, dirs in curs.iteritems():
          inv_dirs = [(-dir_i, -dir_j) for (dir_i, dir_j) in dirs]
          for dir in Mu.DIRECTIONS:
            if not dir in inv_dirs:
              cur_i, cur_j = cur
              dir_i, dir_j = dir
              new_i, new_j = cur_i+dir_i, cur_j+dir_j
              if not group.mu_board.matrix[new_i][new_j] in Mu.DIRECTIONS_INVALID_SYMBOLS[dir]:
                new_thread = Mu_Thread.WITH_NEW_STACK(
							Mu_Frame(group.mu_board),
							None,
							(new_i, new_j),
							dir,
							None,
							group=parent_group
                )
                group.mu_board.add_thread(new_thread)
        del self.join_waiters[group]

  def apply_serial_waiters(self):
    for idx, threads in enumerate(self.serial_waiters):
      if threads:
        thread = threads[0]
        group_completed = thread.group.is_completed()
        for sub_thread in thread.group:
          if not sub_thread.completed:
            group_completed = False
            break
        if group_completed:
          del threads[0]
          if threads:
            threads[0].wakeup()
          else:
            del self.serial_waiters[idx]
          

  def run(self):
    while (not self.completed) and self.threads:
      self.run_step()

  def parse(self):
    self.itn += 1
    for board in self.boards:
      board.parse()
    self.hold_release_threads()
    
  start = parse

  def mark_holding(self, thread):
    self.mark_holding_threads.add(thread)

  def hold_release_threads(self):
    if self.mark_holding_threads:
      for thread in self.threads.difference(self.mark_holding_threads):
        thread.hold()
      self.holding_threads = set(self.mark_holding_threads)
      self.mark_holding_threads.clear()
    elif self.held_threads and not self.holding_threads:
      for thread in set(self.held_threads):
        thread.release()
    if self.mark_releasing_threads:
      self.holding_threads.difference_update(self.mark_releasing_threads)

  def mark_releasing(self, holding_thread):
    if not holding_thread in self.holding_threads.union(self.mark_holding_threads):
      raise Mu_RuntimeError, ("cannot release: thread is not holding", holding_thread)
    self.mark_releasing_threads.add(holding_thread)

  def has_global_variable(self, name):
    return name in self.global_variables

  def set_global_variable(self, name, value):
    self.global_variables[name] = value

  def get_global_variable(self, name):
    if name in self.global_variables:
      return self.global_variables[name]
    else:
      return None

  def del_global_variable(self, name):
    if name in self.global_variables:
      del self.global_variables[name]
      return True
    else:
      return False

  def add_module_function(self, fun_ord, fun):
    self.module_functions[fun_ord] = fun

  def add_function(self, mu_board, fun_ord, cur, dir):
    function = Mu_Function(mu_board, cur, dir, None)
    fq_ord = mu_board.fully_qualified_name_ord(fun_ord)
    self.functions[fq_ord] = function
    if fun_ord in self.functions:
      del self.functions[fun_ord]
    else:
      self.functions[fun_ord] = function
    mu_board.ifunctions[fun_ord] = function
    
  def add_mainfunction(self, mu_board, fun_ord, cur, dir):
    function = Mu_StaticFunction(mu_board, cur, dir, None)
    fq_ord = mu_board.fully_qualified_name_ord(fun_ord)
    self.functions[fq_ord] = function
    if fun_ord in self.functions:
      del self.functions[fun_ord]
    else:
      self.functions[fun_ord] = function
    mu_board.ifunctions[fun_ord] = function
    function.begin()
    
  def add_staticfunction(self, mu_board, fun_ord, cur, dir):
    function = Mu_StaticFunction(mu_board, cur, dir, None)
    fq_ord = mu_board.fully_qualified_name_ord(fun_ord)
    self.functions[fq_ord] = function
    if fun_ord in self.functions:
      del self.functions[fun_ord]
    else:
      self.functions[fun_ord] = function
    mu_board.ifunctions[fun_ord] = function
    
  def set_operator(self, op_board, op_ord, empty_operator):
    for mu_board in self.boards:
      mu_board.set_operator(op_board, op_ord, empty_operator)
    
  def run_step(self):
    self.itn += 1
    for thread in set(self.threads):
      #print "STEP %2d {" % self.itn, thread
      thread.step()
      #print "STEP %2d }" % self.itn, thread
    self.hold_release_threads()
    if self.join_waiters:
      self.apply_join_waiters()
    if self.serial_waiters:
      self.apply_serial_waiters()

  def show(self):
    for mu_board in self.mu_boards:
      print '='*80
      mu_board.show()

class Mu_Board(object):
  UNICODE = True
  COLORS = True
  WIDTH = (10, 10)
  def __init__(	self,
		mu,
		source,
		config=None,
		unicode=None,
		colors=None,
		width=None,
		name=None,
    ):
    if unicode is None:
      unicode = self.UNICODE
    self.unicode = unicode
    if colors is None:
      colors = self.COLORS
    self.colors = colors
    if width is None:
      width = self.WIDTH
    self.width = width
    if name is None:
      name = "MAIN"
    self.name = name
    name_prefix = "%s." % self.name
    self.name_prefix = "%s." % self.name
    self.name_prefix_ord = Mu_a2i(self.name_prefix)
    self.name_prefix_factor = MU_MAX_ORD**len(self.name_prefix)
    self.mu = mu
    self.mu.boards.append(self)
    self.source = source
    self.console = mu.console
    self.filename = None
    if isinstance(source, file):
      self.filename = source.name
      self.source_lines = [line.strip('\n') for line in source.readlines()]
    elif isinstance(source, basestring):
      self.filename = '<string>'
      self.source_lines = source.split('\n')
    elif isinstance(source, (tuple, list)):
      self.filename = '<string>'
      self.source_lines = [line.rstrip('\n') for line in source]
    lines = []
    for line in self.source_lines:
      for k, v in Mu.TRANSLATION.iteritems():
        line = line.replace(k, v)
      lines.append(line)
    self.source_lines = lines

    if config is None:
      config = Mu_Config()
    self.config = config

    max_len = reduce(lambda x, y: max(x, len(y)), self.source_lines, 0)
    #lines =  [(line + ' '*(max_len-len(line))) for line in self.source_lines]
    self.sym_absorbers = (Mu.SYM_ABSORBER, Mu.SYM_WHITESPACE)
    self.sym_bridges = (
				Mu.SYM_START,
				#Mu.SYM_MAINFUNCTION_BEGIN,
				Mu.SYM_BEGIN_AND_HOLD,
				Mu.SYM_BRIDGE
    )
    self.sym_unary_operators =	self.sym_bridges + (
							Mu.SYM_IGNORE,
							Mu.SYM_STACK_PUSH,
							Mu.SYM_STACK_ESCAPED_PUSH,
							Mu.SYM_FUNCTION_CALL,
							Mu.SYM_STACK_IF_POSITIVE,
							Mu.SYM_STACK_IF_NEGATIVE,
							Mu.SYM_STACK_IF_NONZERO,
							Mu.SYM_STACK_IF_ZERO,
    )
    self.symbol_operator = Mu.SYMBOL_OPERATOR.copy()

    self.step_operator = dict((e, Mu.OPERATOR[o][1]) for e, o in self.symbol_operator.iteritems())

    for bridge_operator in self.sym_bridges:
      empty_operator = self.step_operator[bridge_operator]
      self.step_operator[bridge_operator] = Mu_Thread._step_empty_operator__bridge

    for absorber_operator in self.sym_absorbers:
      empty_operator = self.step_operator[absorber_operator]
      self.step_operator[absorber_operator] = Mu_Thread._step_empty_operator__absorber

        
    #for op, fun in self.step_operator.iteritems():
    #  print 'unary:', op, repr(chr(op)), fun.func_name
    #raw_input()

    self.border_size = 2
    self.border_symbol = Mu.SYM_WHITESPACE
    lr = [self.border_symbol for i in xrange(self.border_size)]
    l2 = [self.border_symbol for i in xrange(max_len+self.border_size*2)]
  
    self.matrix = []
    self.matrix.append(l2)
    self.matrix.append(l2)
    for source_line in self.source_lines:
      l_center = lr + [Mu.a2i(c) for c in source_line] + [Mu.SYM_WHITESPACE]*(max_len-len(source_line)) + lr
      self.matrix.append(l_center)
    self.matrix.append(l2)
    self.matrix.append(l2)
    self.max_i = len(self.matrix)
    self.max_j = max_len+4
    for cur_i, row in enumerate(self.matrix):
      for cur_j, c in enumerate(row):
        if c<0 or c>Mu.MAX_ORD:
          raise Mu_SyntaxError,("invalid char %d[%s]" % (c, self.i2a(c)), self, (cur_i, cur_j), (0, 0))
    #self.board = [[(c, self.step_operator[c][0], self.step_operator[c][1]) for c in row] for row in self.matrix]
    self.board = tuple(tuple(c for c in row) for row in self.matrix)
    self.board_debugger = None
    self.threads = set()
    self.ifunctions = {}
    self.local_variables = {}
    self.local_operators = set()
    #self.ioperators = {}
    
  def fully_qualified_name_ord(self, n_ord):
    n = MU_MAX_ORD**(int(math.ceil(math.log(float(n_ord))/math.log(MU_MAX_ORD))))
    fq_ord = self.name_prefix_ord*n + n_ord
    return fq_ord

  @classmethod
  def _dump_fake_filter(clss, m, f, i, j):
    return Mu.i2a(m[i][j])

  @classmethod
  def _dump_filter(clss, m, f, i, j):
    if f[i][j]:
      return Mu.i2a(m[i][j])
    else:
      return ' '

  def has_variable(self, name):
    if name in self.local_variables:
      return True
    else:
      return self.mu.has_global_variable(name)

  def set_global_variable(self, name, value):
    return self.mu.set_global_variable(name, value)

  def set_local_variable(self, name, value):
    self.local_variables[name] = value

  def get_variable(self, name):
    if name in self.local_variables:
      return self.local_variables[name]
    else:
      return self.mu.get_global_variable(name)
      
  def del_variable(self, name):
    if name in self.local_variables:
      del self.local_variables[name]
      return True
    else:
      return self.mu.del_global_variable(name)
      
  def dump_board(self):
    return '\n'.join(''.join(Mu_i2a(e) for e in line) for line in self.board)

  def dump_lines(self, width, center=None, threads=None, unicode=None, colors=None, row_numbers=True, col_numbers=True, filter_map=None, formatter_map=None, return_data=None):
    if unicode is None:
      unicode = self.unicode
    if colors is None:
      colors = self.colors
    if threads is None:
      threads = self.threads
    border_size = self.border_size
    grid_min_i = border_size
    grid_max_i = self.max_i-border_size-1
    grid_min_j = border_size
    grid_max_j = self.max_j-border_size-1
    if center is None:
      if threads:
        u_threads = filter(lambda thread: not (thread.is_held or thread.is_waiting), threads)
        if not u_threads:
         u_threads = threads
        min_i = min(thread.cur[0] for thread in u_threads)
        max_i = max(thread.cur[0] for thread in u_threads)
        min_j = min(thread.cur[1] for thread in u_threads)
        max_j = max(thread.cur[1] for thread in u_threads)
        #print min_i, max_i, min_j, max_j, len(threads)
        #raw_input('...')
      else:
        min_i = max(grid_min_i, width[0])
        max_i = min(grid_max_i, min_i+width[0])
        min_j = max(grid_min_j, width[1])
        max_j = min(grid_max_j, min_j+width[1])
        #min_j = grid_min_j
        #max_j = grid_max_j
      center_i = (min_i+max_i)//2
      center_j = (min_j+max_j)//2
      center = center_i, center_j
      
      #print center, min_i, max_i, min_j, max_j, len(threads)

    center_i, center_j = center
    il, jl = width
    min_i = max(grid_min_i, center_i-il)
    min_j = max(grid_min_j, center_j-jl)
    max_i = min(grid_max_i, center_i+il)
    max_j = min(grid_max_j, center_j+jl)
    if return_data is not None:
      return_data['center'] = center
    #print center, width, min_i, max_i, min_j, max_j, threads is None, len(threads)
    #raw_input('...1')
    if filter_map:
      filter_function = self._dump_filter
    else:
      filter_function = self._dump_fake_filter
    m = [[filter_function(self.matrix, filter_map, i, j) for j in xrange(min_j,max_j+1)] for i in xrange(min_i,max_i+1)]
    lines = []


    if unicode:
      if min_i == grid_min_i:
        u_ = u"━"
        if min_j == grid_min_j:
          ul = u"┏"
        else:
          ul = u"┍"
        if max_j == grid_max_j:
          ur = u"┓"
        else:
          ur = u"┑"
      else:
        #u_ = u"━"
        u_ = u"─"
        if min_j == grid_min_j:
          ul = u"┎"
        else:
          ul = u"┌"
        if max_j == grid_max_j:
          ur = u"┒"
        else:
          ur = u"┐"
      if max_i == grid_max_i:
        d_ = u"━"
        if min_j == grid_min_j:
          dl = u"┗"
        else:
          dl = u"┕"
        if max_j == grid_max_j:
          dr = u"┛"
        else:
          dr = u"┙"
      else:
        d_ = u"─"
        if min_j == grid_min_j:
          dl = u"┖"
        else:
          dl = u"└"
        if max_j == grid_max_j:
          dr = u"┚"
        else:
          dr = u"┘"
      if min_j == grid_min_j:
        l_ = u"┃"
      else:
        l_ = u"│"
      if max_j == grid_max_j:
        r_ = u"┃"
      else:
        r_ = u"│"
#←  ↑  →  ↓
#$ unicode 2500..2570
#          .0 .1 .2 .3 .4 .5 .6 .7 .8 .9 .A .B .C .D .E .F
#     250.  ─  ━  │  ┃  ┄  ┅  ┆  ┇  ┈  ┉  ┊  ┋  ┌  ┍  ┎  ┏
#     251.  ┐  ┑  ┒  ┓  └  ┕  ┖  ┗  ┘  ┙  ┚  ┛  ├  ┝  ┞  ┟
#     252.  ┠  ┡  ┢  ┣  ┤  ┥  ┦  ┧  ┨  ┩  ┪  ┫  ┬  ┭  ┮  ┯
#     253.  ┰  ┱  ┲  ┳  ┴  ┵  ┶  ┷  ┸  ┹  ┺  ┻  ┼  ┽  ┾  ┿
#     254.  ╀  ╁  ╂  ╃  ╄  ╅  ╆  ╇  ╈  ╉  ╊  ╋  ╌  ╍  ╎  ╏
#     255.  ═  ║  ╒  ╓  ╔  ╕  ╖  ╗  ╘  ╙  ╚  ╛  ╜  ╝  ╞  ╟
#     256.  ╠  ╡  ╢  ╣  ╤  ╥  ╦  ╧  ╨  ╩  ╪  ╫  ╬  ╭  ╮  ╯
#     257.  ╰  ╱  ╲  ╳  ╴  ╵  ╶  ╷  ╸  ╹  ╺  ╻  ╼  ╽  ╾  ╿
#     258.  ▀  ▁  ▂  ▃  ▄  ▅  ▆  ▇  █  ▉  ▊  ▋  ▌  ▍  ▎  ▏
#     259.  ▐  ░  ▒  ▓  ▔  ▕  ▖  ▗  ▘  ▙  ▚  ▛  ▜  ▝  ▞  ▟
#     25A.  ■  □  ▢  ▣  ▤  ▥  ▦  ▧  ▨  ▩  ▪  ▫  ▬  ▭  ▮  ▯
#     25B.  ▰  ▱  ▲  △  ▴  ▵  ▶  ▷  ▸  ▹  ►  ▻  ▼  ▽  ▾  ▿
#     25C.  ◀  ◁  ◂  ◃  ◄  ◅  ◆  ◇  ◈  ◉  ◊  ○  ◌  ◍  ◎  ●
#     25D.  ◐  ◑  ◒  ◓  ◔  ◕  ◖  ◗  ◘  ◙  ◚  ◛  ◜  ◝  ◞  ◟
#     25E.  ◠  ◡  ◢  ◣  ◤  ◥  ◦  ◧  ◨  ◩  ◪  ◫  ◬  ◭  ◮  ◯
#     25F.  ◰  ◱  ◲  ◳  ◴  ◵  ◶  ◷  ◸  ◹  ◺  ◻  ◼  ◽  ◾  ◿


      as_left =   u"→"
      as_top =    u"↓"
      as_right =  u"←"
      as_bottom = u"↑"
      ad_left =   u"⇒"
      ad_top =    u"⇓"
      ad_right =  u"⇐"
      ad_bottom = u"⇑"
    else:
      ul = '/'
      u_ = '-'
      ur = '\\'
      l_ = '|'
      r_ = '|'
      dl = '\\'
      d_ = '-'
      dr = '/'
      as_left =   u"-"
      as_top =    u"|"
      as_right =  u"-"
      as_bottom = u"|"
      ad_left =   u">"
      ad_top =    u"v"
      ad_right =  u"<"
      ad_bottom = u"^"
    if row_numbers:
     h_len = 7
    else:
     h_len = 0
    h_init = " "*h_len
    top_lst = [h_init, ul]
    top_lst.extend(itertools.repeat(u_, max_j-min_j+1))
    top_lst.append(ur)
    bottom_lst = [h_init, dl]
    bottom_lst.extend(itertools.repeat(d_, max_j-min_j+1))
    bottom_lst.append(dr)
    w_cur_lst = []
    r_cur_lst = []
    for thread in threads:
      if isinstance(thread, Mu_Thread):
        cur = thread.cur
        waiting = thread.is_waiting
      else:
        cur = thread
        waiting = False
      if waiting:
        w_cur_lst.append(cur)
      else:
        r_cur_lst.append(cur)
    cur_lst = [(True, cur) for cur in w_cur_lst] + [(False, cur) for cur in r_cur_lst]
    if formatter_map:
      num_i = max_i-min_i
      num_j = max_j-min_j
      for pos, formatter in formatter_map:
        i = pos[0]-min_i
        if i<0 or i>num_i:
          continue
        j = pos[1]-min_j
        if j<0 or j>num_j:
          continue
        m[i][j] = formatter.format_string(m[i][j])
    else:
      formatters = {
	'DEFAULT':	widget.Formatter(color="BLACK"),
	'CUR_WAIT':	widget.Formatter(color="YELLOW"),
	'CUR':		widget.Formatter(color="RED", reverse=True),
      }
      for waiting, cur in cur_lst:
        if waiting:
	  formatter = formatters['CUR_WAIT']
        else:
	  formatter = formatters['CUR']
        i, j = cur[0]-min_i, cur[1]-min_j
        m[i][j] = formatter.format_string(m[i][j])
        
    c_lines = []
#←  ↑  →  ↓
    for i, row in enumerate(m):
      ci = i+min_i
      if row_numbers and (ci == 1 or ci%5 == 0):
        rn = u"%5d→ " % ci
      else:
        rn = h_init
      l = widget.FormattedString()
      for e in row:
        if isinstance(e, widget.FormattedString):
          l.extend(e)
        else:
          l.append(e)
      c_lines.append([rn, l_, l, r_])
    if col_numbers:
      if max_j < 10:
        s = 1
      elif max_j < 1000:
        s = 3
      s2 = (s-1)//2
      cj_lst = []
      col_numbers_0 = []
      col_numbers_1 = []
      if unicode:
        vl = u"↓"
      else:
        vl = '|'
      for cj in xrange(min_j, max_j+1):
        j = cj-min_j+1
        if cj%5 == 0:
          cj_lst.append(cj)
      if cj_lst:
        hj = cj_lst[0]-min_j+1
        hl = h_len
        if hj-s2 < 0:
          hl -= s2-hj-1
        hl += hj-2
        col_numbers_0.append(" "*hl)
        col_numbers_0.append("".join(str(cj).center(5) for cj in cj_lst))
        col_numbers_1.append(" "*hl)
        col_numbers_1.append("".join(vl.center(5) for cj in cj_lst))
        lines.append(''.join(col_numbers_0))
        lines.append(''.join(col_numbers_1))
    for waiting, (cur_i, cur_j) in cur_lst:
      j = cur_j-min_j+1
      i = cur_i-min_i
      if waiting:
        a_left, a_top, a_right, a_bottom = as_left, as_top, as_right, as_bottom
      else:
        a_left, a_top, a_right, a_bottom = ad_left, ad_top, ad_right, ad_bottom
      top_lst[j+1] = a_top
      bottom_lst[j+1] = a_bottom
      if i>=0 and i <len(c_lines):
        c_lines[i][1] = a_left
        c_lines[i][3] = a_right
      #except:
      #  print i, len(c_lines)
      #  if i>=0 and i<len(c_lines):
      #    print "---", len(c_lines[i])
      #  import traceback
      #  traceback.print_exc()
      #  raise
    lines.append(''.join(top_lst))
    #lines.extend(''.join(l) for l in c_lines)
    for rn, l_, l, r_ in c_lines:
      line = widget.FormattedString([rn, l_])
      line.extend(l)
      line.append(r_)
      lines.append(line)
    #lines.extend(c_lines)
    lines.append(''.join(bottom_lst))
    return lines
 
  def has_function(self, fun_ord):
    return self.ifunctions.has_key(fun_ord) or self.mu.functions.has_key(fun_ord)

#  def has_operator(self, op_ord):
#    return self.ioperators.has_key(op_ord) or self.mu.operators.has_key(op_ord)

  def get_function(self, fun_ord, thread):
    if self.mu.module_functions.has_key(fun_ord):
      return self.mu.module_functions[fun_ord]
    elif self.ifunctions.has_key(fun_ord):
      return self.ifunctions[fun_ord]
    elif self.mu.functions.has_key(fun_ord):
      return self.mu.functions[fun_ord]
    else:
      print fun_ord, repr(Mu_i2a(fun_ord))
      print self.mu.functions.keys()
      print map(Mu_i2a, self.mu.functions.iterkeys())
      raise Mu_RuntimeError, ("function %d[%s] not defined" % (fun_ord, Mu.i2a(fun_ord)), self, thread.cur, thread.dir)

#  def get_operator(self, op_ord, thread):
#    if self.ioperators.has_key(op_ord):
#      return self.ioperators[op_ord]
#    elif self.mu.operators.has_key(op_ord):
#      return self.mu.operators[op_ord]
#    else:
#      raise Mu_RuntimeError, ("operator %d[%s] not defined" % (op_ord, Mu.i2a(op_ord)), self, thread.cur, thread.dir)

  def add_function(self, fun_ord, cur, dir):
    self.mu.add_function(self, fun_ord, cur, dir)
    
  def add_mainfunction(self, fun_ord, cur, dir):
    self.mu.add_mainfunction(self, fun_ord, cur, dir)
    
  def add_staticfunction(self, fun_ord, cur, dir):
    self.mu.add_staticfunction(self, fun_ord, cur, dir)
    
  def add_ifunction(self, fun_ord, cur, dir):
    self.ifunctions[fun_ord] = Mu_Function(self, cur, dir, None)
    
  def add_imainfunction(self, fun_ord, cur, dir):
    self.ifunctions[fun_ord] = Mu_StaticFunction(self, cur, dir, None)
    self.ifunctions[fun_ord].begin()
    
  def add_istaticfunction(self, fun_ord, cur, dir):
    self.ifunctions[fun_ord] = Mu_StaticFunction(self, cur, dir, None)
    
  def make_operator(self, op_ord, cur, dir):
    return lambda thread, symbol, empty_operator: Mu_Thread._step_empty_operator__operator_call_wrapper(thread, Mu_Function(self, cur, dir, None), symbol, empty_operator)

  def add_operator(self, op_ord, cur, dir):
    empty_operator = self.make_operator(op_ord, cur, dir)
    self.mu.set_operator(self, op_ord, empty_operator)
    
  def add_ioperator(self, op_ord, cur, dir):
    self.set_operator(self, op_ord, self.make_operator(op_ord, cur, dir))
    
  def set_operator(self, op_board, op_ord, empty_operator):
    #print op_board is self, op_ord, op_ord in self.local_operators
    if op_board is self:
      self.step_operator[op_ord] = empty_operator
      self.local_operators.add(op_ord)
    elif not op_ord in self.local_operators:
      self.step_operator[op_ord] = empty_operator

  def attach_debugger(self, board_debugger):
    self.board_debugger = board_debugger

  def check_bounds_N(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_N)

  def check_bounds_NE(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_NE)

  def check_bounds_E(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_E)

  def check_bounds_SE(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_SE)

  def check_bounds_S(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_S)

  def check_bounds_SW(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_SW)

  def check_bounds_W(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_W)

  def check_bounds_NW(self, cur_i, cur_j):
    return self.check_bounds(cur_i, cur_j, DIR_NW)

  def check_bounds(self, cur, dir):
    cur_i, cur_j = cur
    dir_i, dir_j = dir
    new_i, new_j = cur_i+dir_i, cur_j+dir_j
    if new_i < 0 or new_i >= self.max_i or new_j < 0 or new_j >= self.max_j:
      raise Mu_SyntaxError, ("bound error at (%2d, %2d), direction (%2d, %2d)[%c:%s]" % (
		cur_i, cur_j, dir_i, dir_j, Mu.DIRECTION_SYMBOL[dir]), Mu.DIRECTION_NAME[dir][0],
		self, cur, dir
      )

  def parse(self):
    if self.max_i == 0:
      return
    for cur_i in xrange(self.max_i):
      for cur_j in xrange(self.max_j):
        cur = cur_i, cur_j
        if self.matrix[cur_i][cur_j] == Mu.SYM_START:
          if self.board_debugger:
            self.board_debugger.set_seen_cur(None, cur_i, cur_j)
          for start_dir, start_dir_symbol in Mu.DIRECTION_SYMBOL.iteritems():
            start_dir_i, start_dir_j = start_dir
            start_cur_i, start_cur_j = cur_i+start_dir_i, cur_j+start_dir_j
            start_cur = (start_cur_i, start_cur_j)
            start_symbol = self.matrix[start_cur_i][start_cur_j]
            if start_symbol in (Mu.SYM_BEGIN_AND_HOLD, ):
              if self.board_debugger:
                self.board_debugger.set_seen_cur(None, start_cur_i, start_cur_j)
              new_i, new_j = start_cur_i+start_dir[0], start_cur_j+start_dir[1]
              if not self.matrix[new_i][new_j] in Mu.DIRECTIONS_INVALID_SYMBOLS[start_dir]:
                thread = Mu_Thread.WITH_NEW_STACK(
							Mu_Frame(self),
							None,
							start_cur,
							start_dir,
							None
                )
                self.add_thread(thread)
                self.mu.mark_holding(thread)
            elif start_symbol in (
					Mu.SYM_MAINFUNCTION_BEGIN,
					Mu.SYM_IMAINFUNCTION_BEGIN,
					Mu.SYM_STATICFUNCTION_BEGIN,
					Mu.SYM_ISTATICFUNCTION_BEGIN,
					Mu.SYM_FUNCTION_BEGIN,
					Mu.SYM_IFUNCTION_BEGIN,
					Mu.SYM_OPERATOR_BEGIN,
					Mu.SYM_IOPERATOR_BEGIN
              ):
              if self.board_debugger:
                self.board_debugger.set_seen_cur(None, start_cur_i, start_cur_j)
              new_i, new_j = start_cur_i+start_dir[0], start_cur_j+start_dir[1]
              if self.board_debugger:
                self.board_debugger.set_seen_cur(None, new_i, new_j)
              of_ord = self.matrix[new_i][new_j]
              if of_ord != Mu.SYM_WHITESPACE:
                if start_symbol == Mu.SYM_MAINFUNCTION_BEGIN:
                  self.add_mainfunction(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_IMAINFUNCTION_BEGIN:
                  self.add_imainfunction(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_STATICFUNCTION_BEGIN:
                  self.add_staticfunction(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_ISTATICFUNCTION_BEGIN:
                  self.add_istaticfunction(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_FUNCTION_BEGIN:
                  self.add_function(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_IFUNCTION_BEGIN:
                  self.add_ifunction(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_OPERATOR_BEGIN:
                  self.add_operator(of_ord, (new_i, new_j), start_dir)
                elif start_symbol == Mu.SYM_IOPERATOR_BEGIN:
                  self.add_ioperator(of_ord, (new_i, new_j), start_dir)
                else:
                  raise Mu_InternalError, ("should not be here", self, cur, dir)

  def add_thread(self, thread):
    self.threads.add(thread)
    self.mu.threads.add(thread)

  def del_thread(self, thread):
    self.threads.remove(thread)
    self.mu.del_thread(thread)

  def show(self):
    print "=== Mu_Board<%s>" % self.filename
    for row in self.matrix:
      print ''.join(Mu.i2a(i) for i in row)
            
class Mu_Config(dict):
  CONFIG_mu = dict(
  )
  CONFIGS = {
		'default':	CONFIG_mu,
		'.mu':		CONFIG_mu,
  }
  def __init__(self, config=None):
    if config is None:
      config = self.CONFIGS['default']
    elif isinstance(config, basestring):
      config = self.CONFIGS.get(config, self.CONFIGS["default"])
    dict.__init__(self, config)

Mu.set_symbol_operator()

def _optparse_callback_libdir(option, opt, value, parser):
  libdir = os.path.abspath(value)
  if not os.path.isdir(libdir):
    raise Mu_Error, "lib directory '%s' does not exist" % value
  if getattr(parser.values, option.dest) is None:
    setattr(parser.values, option.dest, [])
  getattr(parser.values, option.dest).insert(0, libdir)

def _optparse_callback_code(option, opt, value, parser):
  if getattr(parser.values, option.dest) is None:
    setattr(parser.values, option.dest, [])
  getattr(parser.values, option.dest).append(('code', value, getattr(parser.values, 'config')))

def _optparse_callback_include(option, opt, value, parser):
  filename = os.path.abspath(value)
  if not os.path.lexists(filename):
    raise Mu_Error, "include file '%s' does not exist" % value
  if getattr(parser.values, option.dest) is None:
    setattr(parser.values, option.dest, [])
  getattr(parser.values, option.dest).append(('file', filename, getattr(parser.values, 'config')))

def _optparse_callback_library(option, opt, value, parser):
  libdirs = getattr(parser.values, 'libdirs')
  for libdir in libdirs:
    for mu_or_py, extensions in (
				('py', mu_config.PY_LIB_EXTENSIONS),
				('mu', mu_config.MU_LIB_EXTENSIONS),
      ):
      for extension in extensions:
        filename = os.path.abspath(os.path.join(libdir, '%s.%s'%(value, extension)))
        if os.path.lexists(filename):
          if getattr(parser.values, option.dest) is None:
            setattr(parser.values, option.dest, [])
          getattr(parser.values, option.dest).append((value, 'file', filename, mu_or_py, getattr(parser.values, 'config')))
          return
  raise Mu_Error, "library '%s' does not exist" % value
   
def elapsed_seconds():
  return resource.getrusage(resource.RUSAGE_SELF).ru_utime 

class Mu_Interpreter(object):
  MU_LIB_EXTENSIONS = ('m', 'mu')
  PY_LIB_EXTENSIONS = ('pym', 'py')
  LIB_EXTENSIONS = tuple( list(MU_LIB_EXTENSIONS) + list(PY_LIB_EXTENSIONS) )
  OPTION_LIST = [
		optparse.make_option(	'-i', '--include',
					metavar='IN',
					dest='codes',
					type='string',
					nargs=1,
					action='callback',
					callback=_optparse_callback_include,
					default=None,
					help='include file [default: %default]',
		),
		optparse.make_option(	'-c', '--code',
					metavar='C',
					dest='codes',
					type='string',
					nargs=1,
					action='callback',
					callback=_optparse_callback_code,
					default=None,
					help='run code [default: %default]',
		),
		optparse.make_option(	'-l', '--lib',
					dest='codes',
					action="callback",
					type='string',
					nargs=1,
					callback=_optparse_callback_library,
					default=None,
					help='add system library [default: %default]',
		),
		optparse.make_option(	'-L', '--libdir',
					dest='libdirs',
					action="callback",
					type='string',
					nargs=1,
					callback=_optparse_callback_libdir,
					default=['.', mu_config.MU_LIBDIR],
					help='add system library [default: %default]',
		),
		optparse.make_option(	'-x', '--x-debug',
					dest='x_debug',
					action="store_true",
					default=False,
					help='x debug [default: %default]',
		),
		optparse.make_option(	'-w', '--w-debug',
					dest='w_debug',
					action="store_true",
					default=False,
					help='w debug [default: %default]',
		),
		optparse.make_option(	'-d', '--debug',
					dest='debug',
					action="store_true",
					default=False,
					help='debug [default: %default]',
		),
		optparse.make_option(	'-D', '--debug-threads',
					dest='debug_threads',
					action="store_true",
					default=False,
					help='debug threads [default: %default]',
		),
		optparse.make_option(	'-r', '--report',
					dest='report',
					action="store_true",
					default=None,
					help='show final report [default: %default]',
		),
		optparse.make_option(	'-W', '--thread-width',
					dest='thread_width',
					type="int",
					nargs=2,
					action="store",
					default=(2, 10),
					help='thread width [default: %default]',
		),
		optparse.make_option(	'-a', '--thread-len',
					dest='thread_len',
					type="int",
					nargs=1,
					action="store",
					default=-1,
					help='thread len in debug mode [default: %default]',
		),
		optparse.make_option(	'-y', '--concat',
					dest='concat',
					action="store_true",
					default=None,
					help='concatenate source files [default: %default]',
		),
		optparse.make_option(	'-U', '--no-unicode',
					dest='unicode',
					action="store_false",
					default=True,
					help='use unicode [default: %default]',
		),
		optparse.make_option(	'-C', '--config',
					dest='config',
					action="store",
					default=Mu_Config(),
					help='set config [default: %default]',
		),
    ]
  def __init__(self,
			codes=None,
			sources=None,
			libraries=None,
			libdirs=None,
			debug=False,
			xgui=False,
			wgui=False,
			concat=False,
			config=None,
			debug_threads=None,
			thread_len=None,
			stdin=None,
			stdout=None,
			stderr=None,
    ):
    self.mu = Mu(stdin=stdin, stdout=stdout, stderr=stderr)
    self.mu_boards = []
    self.codes = []
    self.libdirs = []
    if libdirs:
      self.libdirs.extend(libdirs)
    self.libdirs.append(mu_config.MU_LIBDIR)
    self.libdirs.append('.')
    self.xgui = xgui
    self.wgui = wgui
    if self.xgui or self.wgui:
      debug = True
    self.debug = debug
    self.concat = concat
    if config is None:
      config = Mu_Config()
    self.config = config
    self.debug_threads = debug_threads
    self.thread_len = thread_len
    self.mu_deugger = None
    self.elapsed_parse = None
    self.elapsed_run = None

    if codes:
      for code in codes:
        self.add_code(code)
    if sources:
      for source in sources:
        self.add_source(source)
    if libraries:
      for library in libraries:
        self.add_library(library)

  def add_code(self, code, config=None, name=None):
    self.codes.append((name, 'code', code, 'mu', config))

  def add_source(self, source, config=None, name=None):
    if config is None:
      config = self.config
    if not os.path.lexists(source):
      raise Mu_Error, "source '%s' not found" % source
    self.codes.append((name, 'file', os.path.abspath(source), 'mu', config))

  def add_library(self, library, config=None, name=None):
    if config is None:
      config = self.config
    for libdir in self.libdirs:
      for extension in self.MU_LIB_EXTENSIONS:
        lib_filename = os.path.join(libdir, "%s.%s"%(library, extension))
        if os.path.lexists(lib_filename):
          if name is None:
            name = os.path.splitext(os.path.basename(lib_filename))[0]
          self.codes.append((name, 'file', lib_filename, 'mu', config))
          return
      for extension in self.PY_LIB_EXTENSIONS:
        lib_filename = os.path.join(libdir, "%s.%s"%(library, extension))
        if os.path.lexists(lib_filename):
          if name is None:
            name = os.path.splitext(os.path.basename(lib_filename))[0]
          self.codes.append((name, 'file', lib_filename, 'py', config))
          return
    raise Mu_Error, "library '%s' not found" % library

  def parse(self):
    codes = tuple((name, t, filename, config) for (name, t, filename, mu_or_py, config) in self.codes if mu_or_py == 'mu')
    modules = tuple((name, t, filename, config) for (name, t, filename, mu_or_py, config) in self.codes if mu_or_py == 'py')
    if self.concat:
      mu_code = []
      for name, t, mp, code, config in codes:
        if t is 'code':
          mu_code = code
        else:
          with open(filename, 'rb') as mu_file:
            mu_code.extend(mu_file.readlines())
      mu_board = Mu_Board(self.mu, mu_code, config=config, name=None)
      self.mu_boards.append(mu_board)
    else:
      for name, t, filename, config in codes:
        if t is 'code':
          mu_code = code
        else:
          with open(filename, 'rb') as mu_file:
            mu_code = mu_file.readlines()
        mu_board = Mu_Board(self.mu, mu_code, config=config, name=name)
        self.mu_boards.append(mu_board)
    if modules:
      for module_name, module_t, module_filename, module_config in modules:
        #print module_t, module_filename
        if module_t == 'file':
          if module_name is None:
            module_name = os.path.splitext(os.path.basename(module_filename))[0]
          module = imp.load_source(module_name, module_filename)
          pym_prefix = "PYM_"
          for attribute_name in dir(module):
            if attribute_name.startswith(pym_prefix):
              function_name = attribute_name[len(pym_prefix):]
              op_ord = Mu.a2i("%s.%s" % (module_name, function_name))
              #print "...", module_name, op_ord
              self.mu.add_module_function(op_ord, getattr(module, attribute_name))
        else:
          raise Mu_Error, "pym source modules are not implemented yet"
      #raise Mu_Error, "pym modules are not implemented yet"
    if self.debug:
      if self.xgui:
        from MU.mu_x_debug import Mu_XDebugger as mu_debugger_class
        from MU.mu_x_debug import Mu_XBoardDebugger as mu_board_debugger_class
      elif self.wgui:
        from MU.mu_w_debug import Mu_WDebugger as mu_debugger_class
        from MU.mu_w_debug import Mu_WBoardDebugger as mu_board_debugger_class
      else:
        from MU.mu_debug import Mu_Debugger as mu_debugger_class
        from MU.mu_debug import Mu_BoardDebugger as mu_board_debugger_class
      self.mu_debugger = mu_debugger_class(
		self.mu,
		debug_threads=self.debug_threads,
      )
      for mu_board in self.mu_boards:
        mu_board.attach_debugger(
			mu_board_debugger_class(
				mu_board,
				self.mu_debugger,
				thread_len=self.thread_len,
			)
        )
      #t0 = time.time()
      t0 = elapsed_seconds()
      self.mu_debugger.start()
      #t1 = time.time()
      t1 = elapsed_seconds()
      self.elapsed_parse = t1-t0
    else:
      #t0 = time.time()
      t0 = elapsed_seconds()
      self.mu.start()
      #t1 = time.time()
      t1 = elapsed_seconds()
      self.elapsed_parse = t1-t0
 
  def run(self):
    if self.debug:
      #t0 = time.time()
      t0 = elapsed_seconds()
      self.mu_debugger.run()
      #t1 = time.time()
      t1 = elapsed_seconds()
      self.elapsed_run = t1-t0
    else:
      #t0 = time.time()
      t0 = elapsed_seconds()
      self.mu.run()
      #t1 = time.time()
      t1 = elapsed_seconds()
      self.elapsed_run = t1-t0
    self.mu.stdout.flush()
    self.mu.stderr.flush()
  

  def parse_args(self, args=None, additional_options=None):
    if args is None:
      args = sys.argv[1:]

    option_list = self.OPTION_LIST[:]
    if additional_options:
      option_list.extend(additional_options)

    help_formatter=optparse.IndentedHelpFormatter(max_help_position=38)
    parser = optparse.OptionParser(option_list=option_list,formatter=help_formatter)


    (options,args) = parser.parse_args(args)

    if options.thread_width is not None:
      Mu_Error.WIDTH = options.thread_width

    if options.unicode is not None:
      Mu_Error.UNICODE = options.unicode

    if options.codes is None:
      options.codes = []
    for arg in args:
      filename = os.path.abspath(arg)
      if not os.path.lexists(filename):
        raise Mu_Error, "source file '%s' does not exist" % value
      options.codes.append((None, 'file', filename, 'mu', options.config))
    del args[:]

    self.codes.extend(options.codes)

    if options.debug:
      self.debug = True
    if options.x_debug:
      self.debug = True
      self.xgui = True
    if options.w_debug:
      self.debug = True
      self.wgui = True
    self.concat = options.concat
    self.debug_threads = options.debug_threads
    self.thread_width = options.thread_width
    self.thread_width = options.thread_width
    self.thread_len = options.thread_len
    return options, args

  def setup(self):
    if not self.codes:
      self.codes.append((None, 'code', sys.stdin.readlines(), 'mu', options['config']))

  def report(self):
    if self.elapsed_run is not None:
      self.elapsed_iteration = self.elapsed_run/self.mu.itn
    else:
      self.elapsed_iteration = None
    return self.mu.itn, self.elapsed_parse, self.elapsed_run, self.elapsed_iteration
      
class Mu_Error(Exception):
  pass

class Mu_CodeError(Mu_Error):
  UNICODE = True
  COLORS = True
  ARROWS = {
    Mu.DIR_E:		(u"⇒", "E"),
    Mu.DIR_SE:		(u"⇘", "SE"),
    Mu.DIR_S:		(u"⇓", "S"),
    Mu.DIR_SW:		(u"⇙", "SW"),
    Mu.DIR_W:		(u"⇐", "W"),
    Mu.DIR_NW:		(u"⇖", "NW"),
    Mu.DIR_N:		(u"⇑", "N"),
  }
  INDENTATION = " "
  WIDTH = (2, 10)
  pass
  def trace(self, stream, width=None, indentation=None, unicode=None):
    for line in self.tracelines(width=width, indentation=indentation, unicode=unicode):
      stream.write("%s\n" % line)

  def tracelines(self, width=None, indentation=None, unicode=None, colors=None):
    if width is None:
      width = self.WIDTH
    if unicode is None:
      unicode = self.UNICODE
    if colors is None:
      colors = self.COLORS
    if indentation is None:
      indentation = self.INDENTATION
    traces = []
    trace_lines = ["Traceback:"]
    if len(self.args) == 4:
      message, mu_board, cur, dir = self.args
      trace = None
      traces.append((mu_board, cur, dir))
    else:
      message, thread = self.args
      mu_board, cur, dir = thread.mu_board, thread.cur, thread.dir
      traces.append((mu_board, cur, dir))
      while thread.parent_thread is not None:
        thread = thread.parent_thread
        mu_board, cur, dir = thread.mu_board, thread.cur, thread.dir
        traces.append((mu_board, cur, dir))

    for indentation_level, (mu_board, cur, dir) in enumerate(reversed(traces)):
      trace_lines.extend(self._traceback_lines(mu_board, cur, dir, width, indentation*indentation_level, unicode, colors))
    trace_lines.append("%s: %s" % (self.__class__.__name__, message))
    return trace_lines

  def _traceback_lines(self, mu_board, cur, dir, width, indentation, unicode, colors):
    cur_i, cur_j = cur
    dir_i, dir_j = dir
    if self.UNICODE:
      dir_arrow = self.ARROWS[dir][0]
    else:
      dir_arrow = self.ARROWS[dir][1]
    hdr = "!!! %s: " % self.__class__.__name__
    trace_lines = []
    trace_lines.append(("  File %r:" % (mu_board.filename, )).encode("utf-8"))
    trace_lines.append(("  Line %d, column %d, direction %s [%s]" % (cur_i, cur_j, dir, dir_arrow)).encode("utf-8"))
    #trace_lines.append("%s%s(%2d, %2d)[%c]" % (hdr, indentation, cur_i, cur_j, mu_board.matrix[cur_i][cur_j]))
    #trace_lines.append("%s%s(%2d, %2d)[%c:%s]" % (hdr, indentation, dir_i, dir_j, Mu.DIRECTION_SYMBOL[dir], Mu.DIRECTION_NAME[dir][0]))
    lines = mu_board.dump_lines(width, cur, (cur,), unicode=unicode, colors=colors)

    for line in lines:
      #trace_lines.append((u"%s SRC: %s%s" % (hdr, indentation, line)).encode("utf-8"))
      trace_lines.append((u"    %s" % (line)).encode("utf-8"))
    return trace_lines
    
  
class Mu_SyntaxError(Mu_CodeError):
  pass

class Mu_RuntimeError(Mu_CodeError):
  pass

class Mu_InternalError(Mu_CodeError):
  pass

if __name__ == '__main__':
  s0 = raw_input("enter:")
  print "s0:<%s>" % s0
  i0 = Mu_a2i(s0)
  print "i0:[%d]" %  i0

  s1 = Mu_i2a(i0)
  print "s1:<%s>" % s1
  i1 = Mu_a2i(s1)
  print "s0==s1:(%s)" % (s0==s1)
  print "i1:[%d]" % i1
  print "i0==i1:(%s)" % (i0==i1)

  s2 = Mu_i2a(i1)
  print "s2:<%s>" % s2
  i2 = Mu_a2i(s2)
  print "s1==s2:(%s)" % (s1==s2)
  print "i2:[%d]" % i2
  print "i1==i2:(%s)" % (i1==i2)

  import sys
  if sys.argv[1:]:
    input = file(sys.argv[1], 'rb')
    input_2close = True
    del sys.argv[1]
  else:
    input = sys.stdin
    input_2close = False
  
  lines = input.readlines()
  if input_2close:
    input.close()

  v = Mu(lines, debug=True)
  v.parse()
  
