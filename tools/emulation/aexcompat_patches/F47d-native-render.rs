// Included inside ClassicHost: preserve arena construction and output reporting.
    #[cfg(target_os = "macos")]
    fn render_native_bundle(
        &mut self, path: &str, params: u64, input_param: u64,
        output_world: u64, format: FramePixelFormat, request: [i32; 4], smart: bool,
    ) -> Result<(i32, Option<GuestCensus>, Vec<ExecutionTrace>), ClassicError> {
        use crate::native_bridge;
        let mut input = vec![0u8; abi::PF_IN_DATA_SIZE];
        self.engine.read(self.input, &mut input)?;
        let count = read_u32(&input, abi::IN_NUM_PARAMS_OFFSET) as usize;
        if count == 0 || count > 4096 { return Err(ClassicError::Input("invalid parameter count".into())); }
        let mut definitions = vec![0u8; count * abi::PF_PARAM_DEF_SIZE];
        let mut pointers = vec![0u8; count * 8];
        self.engine.read(params, &mut pointers)?;
        for (i, definition) in definitions.chunks_exact_mut(abi::PF_PARAM_DEF_SIZE).enumerate() {
            let address = u64::from_le_bytes(pointers[i*8..i*8+8].try_into().unwrap());
            self.engine.read(address, definition)?;
        }
        let mut src = vec![0u8; abi::PF_LAYER_DEF_SIZE];
        let mut dst = vec![0u8; abi::PF_LAYER_DEF_SIZE];
        self.engine.read(input_param + abi::PARAM_U_OFFSET as u64, &mut src)?;
        self.engine.read(output_world, &mut dst)?;
        let world_shape = |world: &[u8]| -> Result<(u64, usize), ClassicError> {
            let address = u64::from_le_bytes(world[abi::LAYER_DATA_OFFSET..abi::LAYER_DATA_OFFSET+8].try_into().unwrap());
            let stride = read_u32(world, abi::LAYER_ROWBYTES_OFFSET) as usize;
            let height = read_u32(world, abi::LAYER_HEIGHT_OFFSET) as usize;
            let bytes = stride.checked_mul(height).filter(|&n| n > 0 && n <= 256*1024*1024)
                .ok_or_else(|| ClassicError::Input("native world exceeds bounded snapshot".into()))?;
            Ok((address, bytes))
        };
        let (source, source_bytes) = world_shape(&src)?;
        let (destination, destination_bytes) = world_shape(&dst)?;
        let mut source_pixels = vec![0u8; source_bytes];
        let mut destination_pixels = vec![0u8; destination_bytes];
        self.engine.read(source, &mut source_pixels)?;
        self.engine.read(destination, &mut destination_pixels)?;
        let error = native_bridge::render(path, &input, &mut definitions, &mut src, &mut dst,
            &mut source_pixels, &mut destination_pixels, format.bit_depth(), &request, smart)
            .map_err(ClassicError::Input)?;
        self.engine.write(destination, &destination_pixels)?;
        Ok((error, None, Vec::new()))
    }
