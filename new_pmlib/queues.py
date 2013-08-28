#=======================================================================
# queues.py
#=======================================================================
# Collection of queues for cycle-level modeling.

from new_pymtl    import *
from ValRdyBundle import InValRdyBundle, OutValRdyBundle
from collections  import deque

#-----------------------------------------------------------------------
# Queue
#-----------------------------------------------------------------------
class Queue( object ):

  def __init__( self, size=1 ):
    self.data = deque( maxlen=size )

  def is_empty( self ):
    return len( self.data ) == 0

  def is_full( self ):
    return len( self.data ) == self.data.maxlen

  def enq( self, item ):
    assert not self.is_full()
    self.data.append( item )

  def deq( self ):
    return self.data.popleft()

  def peek( self ):
    return self.data[0]

  def nitems( self ):
    return len( self.data )

#-----------------------------------------------------------------------
# InValRdyQueue
#-----------------------------------------------------------------------
class InValRdyQueue( Model ):

  def __init__( s, MsgType, size=1, pipe=False ):
    s.in_  = InValRdyBundle( MsgType )
    s.data = deque( maxlen = size )
    s.deq  = s._pipe_deq if pipe else s._simple_deq

  def elaborate_logic( s ):
    pass

  def is_empty( s ):
    return len( s.data ) == 0

  def deq( s ):
    pass

  def _simple_deq( s ):
    return s.data.popleft()

  def _pipe_deq( s ):
    data = s.data.popleft()
    s.in_.rdy.next = len( s.data ) != s.data.maxlen
    return data

  def peek( s ):
    return s.data[0]

  def xtick( s ):
    if s.in_.rdy and s.in_.val:
      s.data.append( s.in_.msg[:] )
    s.in_.rdy.next = len( s.data ) != s.data.maxlen

#-----------------------------------------------------------------------
# OutValRdyQueue
#-----------------------------------------------------------------------
class OutValRdyQueue( Model ):

  def __init__( s, MsgType, size=1, bypass=False ):
    s.out  = OutValRdyBundle( MsgType )
    s.data = deque( maxlen = size )
    s.enq  = s._bypass_enq if bypass else s._simple_enq

  def elaborate_logic( s ):
    pass

  def is_full( s ):
    return len( s.data ) == s.data.maxlen

  def enq( s ):
    pass

  def _simple_enq( s, item ):
    assert not s.is_full()
    s.data.append( item )

  def _bypass_enq( s, item ):
    assert not s.is_full()
    s.data.append( item )
    if len( s.data ) != 0:
      s.out.msg.next = s.data[0]
    s.out.val.next = len( s.data ) != 0

  def xtick( s ):
    if s.out.rdy and s.out.val:
      s.data.popleft()
    if len( s.data ) != 0:
      s.out.msg.next = s.data[0]
    s.out.val.next = len( s.data ) != 0

#-----------------------------------------------------------------------
# Pipeline
#-----------------------------------------------------------------------
class Pipeline( object ):

  def __init__( self, stages=1 ):
    assert stages > 0
    self.stages = stages
    self.data   = deque( [None]*stages, maxlen = stages )

  def insert( self, item ):
    self.data[0] = item

  def remove( self ):
    item = self.data[-1]
    self.data[-1] = None
    return item

  def ready( self ):
    return self.data[-1] != None

  def advance( self ):
    self.data.rotate()

