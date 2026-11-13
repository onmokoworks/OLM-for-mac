import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import ubdetect as u
import probes


class VerdictTests(unittest.TestCase):
    def decision(self,r=1,c=1,**kwargs):
        return u.decide({'distinct_outputs':r},{'distinct_outputs':c},
                        complete=kwargs.pop('complete',True),mismatch=kwargs.pop('mismatch',True),**kwargs)

    def test_unstable_original(self):
        self.assertEqual(self.decision(r=2)[0],'original_ub')

    def test_stable_bug(self):
        self.assertEqual(self.decision()[0],'stable_mismatch')

    def test_exact_is_not_a_mismatch(self):
        self.assertEqual(self.decision(mismatch=False),('inconclusive','no_mismatch'))

    def test_partial_evidence_never_decisive(self):
        self.assertEqual(self.decision(r=2,complete=False,poison_proven=True)[0],'inconclusive')

    def test_candidate_instability_not_original(self):
        self.assertEqual(self.decision(c=2)[0],'inconclusive')

    def test_direct_oob(self):
        self.assertEqual(self.decision(oob_observed=True)[0],'original_ub')

    def test_differential_without_nondeterminism(self):
        self.assertEqual(self.decision(poison_proven=True)[0],'original_ub')

    def test_float_bits_not_float_equality(self):
        a=np.array([0,0x7fc00001,0,0],dtype='<u4').reshape(1,1,4)
        b=a.copy();b[0,0,0]=0x80000000;b[0,0,1]=0x7fc00002
        mask,stats=u.variation([a,b])
        self.assertEqual(stats['distinct_outputs'],2)
        self.assertTrue(mask[0,0])

    def test_all_varying_pixels(self):
        a=np.zeros((5,7,4),dtype='uint16');b=a.copy();b[1,2,0]=1;c=a.copy();c[4,6,3]=32768
        mask,stats=u.variation([a,b,c]);self.assertEqual(stats['varying_pixels'],2)
        self.assertEqual(np.argwhere(mask).tolist(),[[1,2],[4,6]])

    def test_shape_change_rejected(self):
        with self.assertRaises(ValueError):u.variation([np.zeros((1,1,4)),np.zeros((2,1,4))])


class FakeMemory:
    def __init__(self):self.memory=bytearray([0x55]*2048)
    def read(self,p,addr,size):return bytes(self.memory[addr:addr+size])
    def write(self,p,addr,data):self.memory[addr:addr+len(data)]=data


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.mem=FakeMemory();self.ctx=probes.Debugger.__new__(probes.Debugger)
        from win_debug import Context
        self.ctx=Context();self.ctx.put(probes.REGS['rax'],1000);self.ctx.put(probes.REGS['rcx'],2**64-2)
        self.p={'pid':1,'base':0x1000}
        self.h={'name':'read','kind':'oob_read','rva':'0x100','instruction':'90','basis':'test',
                'table':{'reg':'rax'},'index_reg':'rcx','count':101}

    def test_invalid_index_only_and_restore_hook(self):
        probe=probes.Probe({},b'\x3f')
        probe.entry(self.mem,self.p,2,self.ctx,self.h)
        self.assertEqual(probe.events[0]['index'],-2)
        self.assertEqual(self.mem.read(self.p,992,4),b'\x3f'*4)
        debug=probes.RestoringDebugger.__new__(probes.RestoringDebugger)
        self.p['step']={'address':0x1100}
        with patch.object(probes.Debugger,'write',side_effect=self.mem.write):
            debug.write(self.p,0x1100,b'\xcc')
        self.assertEqual(self.mem.read(self.p,992,4),b'\x55'*4)
        self.assertTrue(probe.events[0]['restored'])

    def test_valid_endpoint_untouched(self):
        self.ctx.put(probes.REGS['rcx'],100)
        probe=probes.Probe({},b'\xff');probe.entry(self.mem,self.p,2,self.ctx,self.h)
        self.assertFalse(probe.events[0]['invalid']);self.assertEqual(probe.bytes_written,0)

    def test_endpoint_minus_one_right_zero(self):
        self.ctx.put(probes.REGS['rcx'],2**64-1)
        probe=probes.Probe({},b'\xff');probe.entry(self.mem,self.p,2,self.ctx,{**self.h,'index_add':1})
        self.assertFalse(probe.events[0]['invalid']);self.assertEqual(probe.bytes_written,0)

    def test_world_padding_does_not_touch_active_samples(self):
        world=1000
        for offset,value,size in [(24,100,8),(32,16,4),(36,3,4),(40,2,4)]:
            self.mem.write(self.p,world+offset,value.to_bytes(size,'little'))
        hook={**self.h,'kind':'world_padding','address':{'reg':'rax'},'pixel_bytes':4,
              'layout':{'data':24,'rowbytes':32,'width':36,'height':40}}
        probe=probes.Probe({},b'\xaa');probe.entry(self.mem,self.p,2,self.ctx,hook)
        self.assertEqual(self.mem.read(self.p,100,32),(b'\x55'*12+b'\xaa'*4)*2)

    def test_parameter_handle_span_preserves_other_fields(self):
        self.mem.write(self.p,1000,(200).to_bytes(8,'little'))
        hook={**self.h,'kind':'span','address':{'reg':'rax','deref':[0],'offset':8},'size':4}
        probe=probes.Probe({},b'\x00');probe.entry(self.mem,self.p,2,self.ctx,hook)
        self.assertEqual(self.mem.read(self.p,200,16),b'\x55'*8+b'\0'*4+b'\x55'*4)

    def test_allocator_result(self):
        self.ctx.put(probes.REGS['rcx'],16)
        hook={**self.h,'kind':'allocation','size_reg':'rcx'}
        probe=probes.Probe({},b'\xcc');ev=probe.entry(self.mem,self.p,2,self.ctx,hook)
        probe.returned(self.mem,self.p,self.ctx,ev)
        self.assertEqual(self.mem.read(self.p,1000,16),b'\xcc'*16)
        self.assertEqual(ev['status'],'complete')

    def test_budget_fails_closed(self):
        probe=probes.Probe({},b'\x00',max_events=0)
        with self.assertRaises(ValueError):probe.entry(self.mem,self.p,2,self.ctx,self.h)
        with self.assertRaises(ValueError):probes.size_value(self.mem,self.p,self.ctx,-1)

    @unittest.skipUnless(os.name=='nt','Windows debugger lifecycle')
    def test_timeout_owns_and_drains_children(self):
        (u.HERE/'runs').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=u.HERE/'runs') as tmp:
            r=probes.run([sys.executable,'-c','import time; time.sleep(5)'],Path(sys.executable),
                         {'hooks':[]},Path(tmp)/'timeout',.05)
            self.assertFalse(r['ok']);self.assertTrue(r['cleanup_verified'])
            self.assertIn(r['pid'],r['processes'])


if __name__=='__main__':unittest.main()
