'use strict';

const SCHEMA = 'windows_witness.aex.v1';
const state = {
  config: null,
  module: null,
  sequence: 0,
  timer: null,
  configurePromise: null,
  configureResolve: null,
  configureReject: null,
  hooks: []
};

function text(value) {
  return value === undefined || value === null ? '' : String(value);
}

function pointer(value) {
  try { return ptr(value).toString(); } catch (_) { return null; }
}

function json(value) {
  try { return JSON.stringify(value); } catch (error) { return JSON.stringify({ value: text(value) }); }
}

function emit(kind, fields) {
  const event = Object.assign({
    schema: SCHEMA,
    run_id: text(state.config && (state.config.run_id || state.config.runId)),
    sequence: ++state.sequence,
    timestamp: new Date().toISOString(),
    thread_id: Process.getCurrentThreadId(),
    event: kind
  }, fields || {});
  send(json(event));
  return event;
}

function fail(code, message, details) {
  emit('error', { error: { code: code, message: message, details: details || null } });
}

function moduleName(module) {
  return module.name || module.path.split('\\').pop().split('/').pop();
}

function sameModule(module, config) {
  const wantedName = text(config.module_name || config.moduleName);
  const wantedPath = text(config.module_path || config.modulePath);
  const nameOK = !wantedName || moduleName(module).toLowerCase() === wantedName.toLowerCase();
  const pathOK = !wantedPath || module.path.toLowerCase() === wantedPath.toLowerCase();
  return nameOK && pathOK;
}

function findModule() {
  const config = state.config || {};
  const wanted = text(config.module_name || config.moduleName);
  if (!wanted) { fail('CONFIG_MODULE_NAME_REQUIRED', 'module_name is required'); return null; }
  const modules = Process.enumerateModules().filter(function (module) { return sameModule(module, config); });
  if (modules.length > 1) {
    fail('MODULE_NOT_UNIQUE', 'more than one matching module was found', modules.map(function (m) { return m.path; }));
    return null;
  }
  return modules[0] || null;
}

function moduleInfo(module) {
  return { name: moduleName(module), path: module.path, base: pointer(module.base), size: module.size };
}

function inModule(address, length) {
  if (!state.module || !address) return false;
  const start = state.module.base;
  const end = start.add(state.module.size);
  try { return address.compare(start) >= 0 && address.add(length || 1).compare(end) <= 0; } catch (_) { return false; }
}

function readValue(address, type) {
  const widths = { u8: 1, u16: 2, u32: 4, u64: 8, i8: 1, i16: 2, i32: 4, i64: 8, f32: 4, f64: 8, ptr: Process.pointerSize, pointer: Process.pointerSize };
  const width = widths[type];
  if (!width || !inModule(address, width)) throw new Error('read is outside the selected module');
  if (type === 'u8') return Memory.readU8(address);
  if (type === 'u16') return Memory.readU16(address);
  if (type === 'u32') return Memory.readU32(address);
  if (type === 'u64') return Memory.readU64(address).toString();
  if (type === 'i8') return Memory.readS8(address);
  if (type === 'i16') return Memory.readS16(address);
  if (type === 'i32') return Memory.readS32(address);
  if (type === 'i64') return Memory.readS64(address).toString();
  if (type === 'f32') return Memory.readFloat(address);
  if (type === 'f64') return Memory.readDouble(address);
  return pointer(Memory.readPointer(address));
}

function readRequest(request) {
  const address = ptr(request.address !== undefined ? request.address : state.module.base.add(request.rva || 0));
  const type = text(request.type).toLowerCase();
  if (type === 'bytes') {
    const length = Number(request.length);
    if (!Number.isInteger(length) || length < 0 || length > 1024 * 1024 || !inModule(address, length)) throw new Error('invalid byte range');
    return { address: pointer(address), type: type, length: length, bytes: Array.prototype.slice.call(new Uint8Array(Memory.readByteArray(address, length))) };
  }
  return { address: pointer(address), type: type, value: readValue(address, type) };
}

function readableRange(address, length) {
  const range = Process.findRangeByAddress(address);
  if (!range || text(range.protection).indexOf('r') === -1) return false;
  try { return address.add(length).compare(range.base.add(range.size)) <= 0; } catch (_) { return false; }
}

function readArgumentValue(address, type) {
  const widths = { u8: 1, u16: 2, u32: 4, u64: 8, i8: 1, i16: 2, i32: 4, i64: 8, f32: 4, f64: 8, ptr: Process.pointerSize };
  const width = widths[type];
  if (type === 'bytes') throw new Error('bytes requires a length');
  if (!width || !readableRange(address, width)) throw new Error('read is outside a readable mapped range');
  if (type === 'u8') return Memory.readU8(address);
  if (type === 'u16') return Memory.readU16(address);
  if (type === 'u32') return Memory.readU32(address);
  if (type === 'u64') return Memory.readU64(address).toString();
  if (type === 'i8') return Memory.readS8(address);
  if (type === 'i16') return Memory.readS16(address);
  if (type === 'i32') return Memory.readS32(address);
  if (type === 'i64') return Memory.readS64(address).toString();
  if (type === 'f32') return Memory.readFloat(address);
  if (type === 'f64') return Memory.readDouble(address);
  return pointer(Memory.readPointer(address));
}

function readArgumentBytes(address, length) {
  if (!Number.isInteger(length) || length < 0 || length > 1024 * 1024 || !readableRange(address, length)) throw new Error('invalid readable byte range');
  return Array.prototype.slice.call(new Uint8Array(Memory.readByteArray(address, length)));
}

function readDirectArgument(value, type) {
  const address = ptr(value);
  if (type === 'ptr' || type === 'u64' || type === 'i64') return pointer(address);
  if (type === 'u32' || type === 'u16' || type === 'u8') return address.toUInt32();
  if (type === 'i32' || type === 'i16' || type === 'i8') return address.toInt32();
  throw new Error('direct argument reads support integer and pointer types only');
}

function readSource(read, args, retval) {
  const source = read.source;
  if (typeof source === 'string') {
    const match = /^arg\((\d+)\)$/i.exec(source);
    if (match) return { address: args[Number(match[1])], kind: 'arg' };
    if (source.toLowerCase() === 'retval') return { address: retval, kind: 'retval' };
  } else if (source && typeof source === 'object') {
    if (text(source.kind || source.type).toLowerCase() === 'arg') return { address: args[Number(source.index)], kind: 'arg' };
    if (text(source.kind || source.type).toLowerCase() === 'retval') return { address: retval, kind: 'retval' };
  }
  throw new Error('read source must be arg(index) or retval');
}

function configuredReads(spec, args, retval, phase, hookName) {
  const reads = spec.reads || spec.typed_reads || spec.typedReads || [];
  const results = {};
  (Array.isArray(reads) ? reads : [reads]).forEach(function (read, index) {
    if (!read || (read.when && text(read.when).toLowerCase() !== phase)) return;
    let source;
    try {
      source = readSource(read, args, retval);
      if ((read.when && text(read.when).toLowerCase() !== phase) || source.kind !== phase) return;
      let address = ptr(source.address);
      const offsets = read.offsets === undefined ? [] : read.offsets;
      if (!Array.isArray(offsets) || offsets.some(function (offset) { return !Number.isInteger(Number(offset)); })) throw new Error('offsets must be an integer array');
      const maxDepth = read.max_depth === undefined ? read.maxDepth : read.max_depth;
      const depthLimit = maxDepth === undefined ? offsets.length : Number(maxDepth);
      if (!Number.isInteger(depthLimit) || depthLimit < 0 || offsets.length > depthLimit) throw new Error('pointer indirection exceeds max_depth');
      offsets.forEach(function (offset) {
        const pointerAddress = address.add(Number(offset));
        if (!readableRange(pointerAddress, Process.pointerSize)) throw new Error('pointer indirection is outside a readable mapped range');
        address = Memory.readPointer(pointerAddress);
        if (address.isNull()) throw new Error('pointer indirection resolved to NULL');
      });
      const type = text(read.type).toLowerCase();
      const result = { address: pointer(address), type: type };
      if (read.direct === true || read.dereference === false) {
        if (offsets.length) throw new Error('direct argument reads may not use offsets');
        result.value = readDirectArgument(address, type);
      } else {
        result.value = type === 'bytes' ? readArgumentBytes(address, Number(read.length)) : readArgumentValue(address, type);
      }
      results[text(read.name || ('read_' + index))] = result;
    } catch (error) {
      const name = text(read.name || ('read_' + index));
      results[name] = { error: text(error) };
      fail('ARGUMENT_READ_FAILED', text(error), { hook: hookName, read: read });
    }
  });
  return results;
}

function gateMatches(gate, args) {
  if (!gate) return true;
  const value = text(args[Number(gate.arg_index !== undefined ? gate.arg_index : gate.argIndex || 0)]);
  let matches = true;
  if (gate.equals !== undefined) matches = value.toLowerCase() === text(gate.equals).toLowerCase();
  if (gate.contains !== undefined) matches = value.toLowerCase().indexOf(text(gate.contains).toLowerCase()) !== -1;
  if (gate.regex !== undefined) { try { matches = new RegExp(gate.regex, gate.flags || '').test(value); } catch (_) { return false; } }
  return gate.negate ? !matches : matches;
}

function resolveAddress(spec) {
  if (spec.address !== undefined) return ptr(spec.address);
  if (spec.rva === undefined) throw new Error('hook needs an address or RVA');
  const rva = Number(spec.rva);
  if (!Number.isInteger(rva) || rva < 0 || rva >= state.module.size) throw new Error('RVA is outside the selected module');
  return state.module.base.add(rva);
}

function hookSpec(spec, defaultKind) {
  const address = resolveAddress(spec);
  const limit = spec.hit_limit === undefined ? spec.hitLimit : spec.hit_limit;
  const item = { spec: spec, address: address, hits: 0, limit: limit === undefined ? Infinity : Math.max(0, Number(limit)), kind: defaultKind };
  if (!Number.isFinite(item.limit)) item.limit = Infinity;
  const hookName = text(spec.name || spec.hook_name || spec.export || (spec.rva !== undefined ? 'rva_' + Number(spec.rva).toString(16) : 'address'));
  const rva = address.sub(state.module.base).toUInt32();
  item.listener = Interceptor.attach(address, {
    onEnter: function (args) {
      this.witness = item.hits < item.limit && gateMatches(spec.case_gate || spec.caseGate, args);
      if (!this.witness) return;
      item.hits++;
      const values = [];
      const count = Number(spec.argument_count !== undefined ? spec.argument_count : spec.argumentCount || 0);
      for (let i = 0; i < count; i++) values.push(pointer(args[i]));
      emit('call', { module: moduleInfo(state.module), hook: { name: hookName, kind: item.kind, rva: rva }, arguments: values, reads: configuredReads(spec, args, null, 'arg', hookName) });
    },
    onLeave: function (retval) {
      if (!this.witness) return;
      emit('return', { module: moduleInfo(state.module), hook: { name: hookName, kind: item.kind, rva: rva }, return_value: pointer(retval), reads: configuredReads(spec, [], retval, 'retval', hookName) });
    }
  });
  state.hooks.push(item);
}

function installHooks() {
  const config = state.config;
  const exportsList = config.exports || config.export_hooks || config.exportHooks || [];
  const rvas = config.internal_rvas || config.internalRvas || [];
  const specs = [];
  (Array.isArray(exportsList) ? exportsList : [exportsList]).forEach(function (entry) {
    const spec = typeof entry === 'string' ? { export: entry, name: entry } : Object.assign({}, entry);
    if (!spec.export) return;
    const address = Module.findExportByName(state.module.name, spec.export);
    if (address) { spec.address = address; specs.push([spec, 'export']); }
    else if (spec.required !== false) fail('EXPORT_NOT_FOUND', 'configured export was not found', { name: spec.export });
  });
  ['EffectMain', 'PluginDataEntryFunction2'].forEach(function (name) {
    if (!specs.some(function (pair) { return pair[0].export === name; })) {
      const address = Module.findExportByName(state.module.name, name);
      if (address) specs.push([{ export: name, name: name, address: address }, 'export']);
    }
  });
  (Array.isArray(rvas) ? rvas : [rvas]).forEach(function (entry) {
    const spec = typeof entry === 'number' ? { rva: entry } : Object.assign({}, entry);
    if (spec.rva !== undefined) specs.push([spec, 'internal_rva']);
  });
  if (!specs.length) fail('NO_HOOKS', 'no requested or default exports were found and no internal RVAs were configured');
  specs.forEach(function (pair) { try { hookSpec(pair[0], pair[1]); } catch (error) { fail('HOOK_INSTALL_FAILED', text(error), pair[0]); } });
}

function locate() {
  if (state.module) return;
  const module = findModule();
  if (!module) return;
  state.module = module;
  emit('module', { module: moduleInfo(module) });
  try { installHooks(); } catch (error) { fail('HOOK_SETUP_FAILED', text(error)); }
  if (state.timer) { clearInterval(state.timer); state.timer = null; }
  if (state.configureResolve) state.configureResolve({ module: moduleInfo(module), hooks: state.hooks.length });
}

function requestBuffer(request) {
  try {
    const result = readRequest(Object.assign({}, request || {}, { type: 'bytes' }));
    const bytes = new Uint8Array(result.bytes);
    const chunkSize = Math.max(1, Number((request && request.chunk_size) || 65536));
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      send({
        event: 'buffer', run_id: text(state.config && state.config.run_id),
        address: result.address, offset: offset, total: bytes.length
      }, bytes.slice(offset, Math.min(offset + chunkSize, bytes.length)).buffer);
    }
    return { address: result.address, length: bytes.length, delegated: true };
  } catch (error) {
    fail('BUFFER_FAILED', text(error), request);
    return { error: text(error) };
  }
}

rpc.exports = {
  configure: function (config) {
    if (state.timer) clearInterval(state.timer);
    state.config = config || {};
    state.module = null;
    state.hooks.forEach(function (item) { try { item.listener.detach(); } catch (_) {} });
    state.hooks = [];
    state.sequence = 0;
    state.configurePromise = new Promise(function (resolve, reject) { state.configureResolve = resolve; state.configureReject = reject; });
    const interval = Math.max(10, Number(state.config.poll_interval_ms || state.config.pollIntervalMs || 100));
    const timeout = Math.max(0, Number(state.config.wait_timeout_ms || state.config.waitTimeoutMs || 30000));
    locate();
    if (!state.module) {
      state.timer = setInterval(locate, interval);
      if (timeout) setTimeout(function () {
        if (!state.module) {
          clearInterval(state.timer);
          state.timer = null;
          fail('MODULE_TIMEOUT', 'named AEX module was not found before timeout');
          if (state.configureResolve) state.configureResolve({ error: 'MODULE_TIMEOUT' });
        }
      }, timeout);
    }
    return state.configurePromise;
  },
  read: function (request) {
    try { return readRequest(request || {}); } catch (error) { fail('READ_FAILED', text(error), request); return { error: text(error) }; }
  },
  requestBuffer: requestBuffer,
  request_buffer: requestBuffer,
  status: function () { return { module: state.module ? moduleInfo(state.module) : null, hooks: state.hooks.length, sequence: state.sequence }; }
};
