#=========================================================================
# VerilogLogicTransl_test.py
#=========================================================================

import SimulationTool_seq_test    as sequential
import SimulationTool_struct_test as structural

from CLogicTransl import CLogicTransl
from subprocess   import check_output, STDOUT, CalledProcessError
from SignalValue  import CreateWrappedClass
from Model        import *

from CLogicHelpers import gen_cppsim

import tempfile
import os

compiler = "g++ -O3 -fPIC -shared -o {libname} {csource}"

#-------------------------------------------------------------------------
# translate
#-------------------------------------------------------------------------
def translate( model ):
  model.elaborate()

  with tempfile.NamedTemporaryFile(suffix='.cpp') as output:

    cdef, CSimWrapper = CLogicTransl( model, output )
    output.flush()

    # NOTE: if we don't create a unique name for each .so, things get
    #       inconsisten (stale data?)
    clib = os.getcwd() + '/' + model.class_name+'.so'
    cmd  = compiler.format( libname = clib,
                            csource = output.name )

    try:

      result = check_output( cmd.split() , stderr=STDOUT )
      output.seek(0)
      source = output.read()

      csim, ffi = gen_cppsim ( clib, cdef )
      sim       = CSimWrapper( csim, ffi )

      #print
      #print source
      #print

      return sim

    except CalledProcessError as e:

      output.seek(0)
      source = output.read()

      raise Exception( 'Module did not compile!\n\n'
                       'Command:\n' + ' '.join(e.cmd) + '\n\n'
                       'Error:\n' + e.output + '\n'
                       'Source:\n \x1b[31m' + source + '\x1b[0m'
                     )


#-------------------------------------------------------------------------
# NetObject
#-------------------------------------------------------------------------
class _NetObject( object ):
  def __init__( self, dest=0, src=0, seqnum=0, payload=0 ):
    self.dest    = dest
    self.src     = src
    self.seqnum  = seqnum
    self.payload = payload

NO = CreateWrappedClass( _NetObject )

#-------------------------------------------------------------------------
# Sequential Logic
#-------------------------------------------------------------------------

def test_Register():
  sim = translate( sequential.Register( 8 ) )
  sim.in_ = 8; assert sim.out == 0
  sim.cycle(); assert sim.out == 8
  sim.in_ = 9; assert sim.out == 8
  sim.in_ = 10
  sim.cycle(); assert sim.out == 10
  sim.in_ = 2
  sim.cycle(); assert sim.out == 2

def test_RegisterWrapped():
  sim = translate( sequential.RegisterWrapped( 8 ) )
  sim.in_ = 8; assert sim.out == 0
  sim.cycle(); assert sim.out == 8
  sim.in_ = 9; assert sim.out == 8
  sim.in_ = 10
  sim.cycle(); assert sim.out == 10
  sim.in_ = 2
  sim.cycle(); assert sim.out == 2

def test_RegisterWrappedChain():
  sim = translate( sequential.RegisterWrappedChain( 8 ) )
  sim.in_ = 8; assert sim.out == 0
  sim.cycle(); assert sim.out == 0
  sim.cycle(); assert sim.out == 0
  sim.in_ = 9;
  sim.in_ = 10
  sim.cycle(); assert sim.out == 8
  sim.in_ = 2
  sim.cycle(); assert sim.out == 8
  sim.cycle(); assert sim.out == 10
  sim.cycle(); assert sim.out == 2

def test_RegisterReset():
  sim = translate( sequential.RegisterReset( 16 ) )
  model = sim
  model.in_ = 8
  assert model.out == 0
  sim.reset()
  assert model.out == 0
  sim.cycle()
  assert model.out == 8
  model.in_ = 9
  assert model.out == 8
  model.in_ = 10
  sim.cycle()
  assert model.out == 10
  sim.reset()
  assert model.out == 0

# TODO: slices not supported
# TODO: bit math doesn't work properly

#def test_SliceWriteCheck():
#  translate( sequential.SliceWriteCheck( 16 ) )
#
#def test_SliceTempWriteCheck():
#  translate( sequential.SliceTempWriteCheck( 16 ) )

def test_MultipleWrites():
  sim = translate( sequential.MultipleWrites() )
  model = sim

  assert model.out == 0
  sim.cycle(); assert model.out == 1
  sim.cycle(); assert model.out == 1
  sim.cycle(); assert model.out == 1

#-------------------------------------------------------------------------
# Complex Objects
#-------------------------------------------------------------------------
#def test_Register_Obj():
#  translate( sequential.Register( NO ) )

#-------------------------------------------------------------------------
# Structural
#-------------------------------------------------------------------------

def passthrough_tester( model ):
  model.in_ = 8
  # Note: no need to call cycle, no @combinational block
  # TODO: must call cycle with current impl, change later!
  model.cycle()  # TODO: remove
  assert model.out   == 8
  model.in_ = 9
  model.in_ = 10
  model.cycle()  # TODO: remove
  assert model.out == 10

def test_PassThrough():
  passthrough_tester( translate( structural.PassThrough(8) ) )

def test_PassThroughWrapped():
  passthrough_tester( translate( structural.PassThroughWrapped(8) ) )

def test_PassThroughWrappedChain():
  passthrough_tester( translate( structural.PassThroughWrappedChain(8) ) )

def splitter_tester( model ):
  model.in_ = 8
  model.cycle()  # TODO: remove
  assert model.out0 == 8
  model.cycle()  # TODO: remove
  assert model.out1 == 8
  model.in_ = 9
  model.in_ = 10
  model.cycle()  # TODO: remove
  assert model.out0 == 10
  assert model.out1 == 10

def test_Splitter():
  splitter_tester( translate(structural.Splitter(16)) )

def test_SplitterWires():
  splitter_tester( translate(structural.SplitterWires(16)) )

def test_SplitterWrapped():
  splitter_tester( translate(structural.SplitterWrapped(16)) )

def test_SplitterPT_1():
  splitter_tester( translate(structural.SplitterPT_1(16)) )

def test_SplitterPT_2():
  splitter_tester( translate(structural.SplitterPT_2(16)) )

def test_SplitterPT_3():
  splitter_tester( translate(structural.SplitterPT_3(16)) )

def test_SplitterPT_4():
  splitter_tester( translate(structural.SplitterPT_4(16)) )

def test_SplitterPT_5():
  splitter_tester( translate(structural.SplitterPT_5(16)) )

def test_PassThroughList():
  sim = translate( structural.PassThroughList(16, 4) )
  model = sim
  for i in range( 4 ):
    model.in_[i] = i
  model.cycle()  # TODO: remove
  for i in range( 4 ):
    # Note: no need to call cycle, no @combinational block
    assert model.out[i] == i
  model.in_[2] = 9
  model.in_[2] = 10
  model.cycle()  # TODO: remove
  assert model.out[2] == 10

def test_PassThroughListWire():
  sim = translate( structural.PassThroughListWire(16, 4) )
  model = sim
  for i in range( 4 ):
    model.in_[i] = i
  model.cycle()  # TODO: remove
  for i in range( 4 ):
    # Note: no need to call cycle, no @combinational block
    assert model.out[i] == i
  model.in_[2] = 9
  model.in_[2] = 10
  model.cycle()  # TODO: remove
  assert model.out[2] == 10


#-------------------------------------------------------------------------
# Sequential
#-------------------------------------------------------------------------

class ForAssign0( Model ):
  def __init__( s ):
    s.in_ = [ InPort (16) for x in range(4) ]
    s.out = [ OutPort(16) for x in range(4) ]
    s.nports = 4

  def elaborate_logic( s ):
    @s.posedge_clk
    def logic():

      for i in range( s.nports ):
        s.out[i].next = s.in_[i]

def test_ForAssign0():
  sim = translate( ForAssign0() )
  model = sim
  for i in range( 4 ): model.in_[i] = i
  model.cycle()
  for i in range( 4 ): assert model.out[i] == i
  model.in_[2] = 9
  model.in_[2] = 10
  model.cycle()
  assert model.out[2] == 10


