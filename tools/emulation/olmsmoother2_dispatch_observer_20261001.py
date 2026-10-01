"""Read-only observation of the actual AEX switch index before dispatch."""
from collections import Counter

import pefile
from unicorn.x86_const import UC_X86_REG_RAX
import probe_olmsmoother2_switch_reachability_20261001 as retained


def native_setup():
    matrix, instances = retained.native_setup()
    pe = pefile.PE(str(matrix.typed.AEX_PATH))
    assert pe.get_data(0xc50a, 5) == bytes.fromhex('3dfc000000')  # CMP EAX, 0xfc
    base = matrix.typed.AexLoader

    class ObservedLoader(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.executed_dispatch_histogram = Counter()
            self.dispatch_observer_errors = []

            def observe(loader, address, size):
                try:
                    index = loader.uc.reg_read(UC_X86_REG_RAX) & 0xffffffff
                    if index > 255:
                        raise RuntimeError('AEX dispatch index out of range: ' + str(index))
                    self.executed_dispatch_histogram[index] += 1
                except Exception as exc:
                    self.dispatch_observer_errors.append(repr(exc))
                    loader.uc.emu_stop()

            self.add_code_hook(pe.OPTIONAL_HEADER.ImageBase + 0xc50a, observe)

    matrix.typed.AexLoader = ObservedLoader
    return matrix, instances
