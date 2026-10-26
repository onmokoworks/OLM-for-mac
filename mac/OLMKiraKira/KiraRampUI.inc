// Included by OLMKiraKira.cpp inside its anonymous namespace.
static PF_Err NewRampHandle(PF_InData *in_data, const OLMKiraKiraRampData &data, PF_ArbitraryH *out)
{
	if (!in_data || !out) return PF_Err_BAD_CALLBACK_PARAM;
	AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
	PF_Handle handle = handles->host_new_handle(sizeof(data));
	if (!handle) return PF_Err_OUT_OF_MEMORY;
	void *locked = handles->host_lock_handle(handle);
	if (!locked) {
		handles->host_dispose_handle(handle);
		return PF_Err_OUT_OF_MEMORY;
	}
	std::memcpy(locked, &data, sizeof(data));
	handles->host_unlock_handle(handle);
	*out = handle;
	return PF_Err_NONE;
}

static PF_Err ReadRampHandle(PF_InData *in_data, PF_ArbitraryH handle, OLMKiraKiraRampData *out)
{
	if (!in_data || !handle || !out) return PF_Err_BAD_CALLBACK_PARAM;
	AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
	if (handles->host_get_handle_size(handle) < sizeof(*out)) return PF_Err_BAD_CALLBACK_PARAM;
	void *locked = handles->host_lock_handle(handle);
	if (!locked) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(out, locked, sizeof(*out));
	handles->host_unlock_handle(handle);
	if (out->count > 16) return PF_Err_BAD_CALLBACK_PARAM;
	return PF_Err_NONE;
}

static PF_Err RampArbitraryCallback(PF_InData *in_data, PF_ArbParamsExtra *extra)
{
	if (!extra) return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	switch (extra->which_function) {
	case PF_Arbitrary_NEW_FUNC:
		return NewRampHandle(in_data, DefaultRampData(), extra->u.new_func_params.arbPH);
	case PF_Arbitrary_DISPOSE_FUNC: {
		AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
		if (extra->u.dispose_func_params.arbH) handles->host_dispose_handle(extra->u.dispose_func_params.arbH);
		extra->u.dispose_func_params.arbH = nullptr;
		return PF_Err_NONE;
	}
	case PF_Arbitrary_COPY_FUNC: {
		OLMKiraKiraRampData ramp = {};
		err = ReadRampHandle(in_data, extra->u.copy_func_params.src_arbH, &ramp);
		return err ? err : NewRampHandle(in_data, ramp, extra->u.copy_func_params.dst_arbPH);
	}
	case PF_Arbitrary_FLAT_SIZE_FUNC:
		*extra->u.flat_size_func_params.flat_data_sizePLu = 0x145;
		return PF_Err_NONE;
	case PF_Arbitrary_FLATTEN_FUNC: {
		if (extra->u.flatten_func_params.buf_sizeLu < 0x145 || !extra->u.flatten_func_params.flat_dataPV)
			return PF_Err_BAD_CALLBACK_PARAM;
		OLMKiraKiraRampData ramp = {};
		err = ReadRampHandle(in_data, extra->u.flatten_func_params.arbH, &ramp);
		if (err) return err;
		unsigned char *flat = static_cast<unsigned char *>(extra->u.flatten_func_params.flat_dataPV);
		std::memset(flat, 0, 0x145);
		flat[0] = 1;
		std::memcpy(flat + 1, &ramp.count, sizeof(ramp.count));
		std::memcpy(flat + 5, ramp.stops, static_cast<size_t>(ramp.count) * sizeof(ramp.stops[0]));
		return PF_Err_NONE;
	}
	case PF_Arbitrary_UNFLATTEN_FUNC: {
		const unsigned char *flat = static_cast<const unsigned char *>(extra->u.unflatten_func_params.flat_dataPV);
		OLMKiraKiraRampData ramp = {};
		size_t count = 0;
		if (!olm::kirakira::parse_merge2_ramp_flat(
				flat, extra->u.unflatten_func_params.buf_sizeLu,
				reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp.stops), 16, &count))
			return PF_Err_BAD_CALLBACK_PARAM;
		ramp.count = static_cast<A_u_long>(count);
		return NewRampHandle(in_data, ramp, extra->u.unflatten_func_params.arbPH);
	}
	case PF_Arbitrary_INTERP_FUNC: {
		OLMKiraKiraRampData left = {}, right = {}, result = {};
		err = ReadRampHandle(in_data, extra->u.interp_func_params.left_arbH, &left);
		if (!err) err = ReadRampHandle(in_data, extra->u.interp_func_params.right_arbH, &right);
		if (err) return err;
		result.count = static_cast<A_u_long>(olm::kirakira::interpolate_merge2_ramps(
			reinterpret_cast<olm::kirakira::Merge2RampStop *>(result.stops),
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(left.stops), left.count,
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(right.stops), right.count,
			static_cast<float>(extra->u.interp_func_params.tF)));
		return NewRampHandle(in_data, result, extra->u.interp_func_params.interpPH);
	}
	case PF_Arbitrary_COMPARE_FUNC: {
		OLMKiraKiraRampData a = {}, b = {};
		err = ReadRampHandle(in_data, extra->u.compare_func_params.a_arbH, &a);
		if (!err) err = ReadRampHandle(in_data, extra->u.compare_func_params.b_arbH, &b);
		if (err) return err;
		const bool equal = olm::kirakira::equal_merge2_ramps(
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(a.stops), a.count,
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(b.stops), b.count);
		*extra->u.compare_func_params.compareP = equal ? PF_ArbCompare_EQUAL : PF_ArbCompare_NOT_EQUAL;
		return PF_Err_NONE;
	}
	case PF_Arbitrary_PRINT_SIZE_FUNC:
		*extra->u.print_size_func_params.print_sizePLu = 0;
		return PF_Err_NONE;
	case PF_Arbitrary_PRINT_FUNC:
	case PF_Arbitrary_SCAN_FUNC:
		return PF_Err_NONE;
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
}

static PF_Err AddRampParam(PF_InData *in_data, A_short id, A_long disk_id)
{
	// PF_ArbitraryDef::refconPV is opaque to the host and is passed back to
	// PF_Cmd_ARBITRARY_CALLBACKS. The Windows owner uses one stable non-null
	// handler address for all five ramps, so keep the same identity/lifetime
	// contract even though the native callback does not need handler state.
	static const char ramp_handler_refcon = 0;
	PF_ParamDef def;
	AEFX_CLR_STRUCT(def);
	PF_ArbitraryH default_handle = nullptr;
	PF_Err err = NewRampHandle(in_data, DefaultRampData(), &default_handle);
	if (err) return err;
	def.param_type = PF_Param_ARBITRARY_DATA;
	std::strncpy(def.name, "Ramp", sizeof(def.name) - 1);
	def.ui_width = 0x136;
	def.ui_height = 0xaa;
	def.ui_flags = PF_PUI_CONTROL | PF_PUI_DONT_ERASE_CONTROL;
	def.flags = PF_ParamFlag_SUPERVISE | PF_ParamFlag_START_COLLAPSED;
	def.uu.id = disk_id;
	def.u.arb_d.id = id;
	def.u.arb_d.dephault = default_handle;
	def.u.arb_d.value = nullptr;
	def.u.arb_d.refconPV = const_cast<char *>(&ramp_handler_refcon);
	err = PF_ADD_PARAM(in_data, -1, &def);
	if (err) {
		AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
		handles->host_dispose_handle(default_handle);
	}
	return err;
}

namespace ramp_ui = olm::kirakira::editor;
struct RampUIInstance {
    ramp_ui::Clipboard<OLMKiraKiraRampData> clipboard;
    std::map<A_long, ramp_ui::State> ramps;
};
static std::recursive_mutex ramp_ui_mutex;
static std::map<PF_ProgPtr, RampUIInstance> ramp_ui_instances;
// Original global at 181824968, initialized to the PE's 0x000810cd.
static std::uint32_t ramp_ui_rng = 0x000810cd;

static PF_Err DrawRampCommands(PF_InData *in_data, PF_EventExtra *event,
                              const std::vector<ramp_ui::DrawCommand>& commands)
{
    PF_Err err = PF_Err_NONE;
    AEGP_SuiteHandler suites(in_data->pica_basicP);
    DRAWBOT_DrawRef draw = nullptr;
    ERR(suites.EffectCustomUISuite2()->PF_GetDrawingReference(event->contextH, &draw));
    if (err || !draw) return err;
    DRAWBOT_SupplierRef supplier = nullptr;
    DRAWBOT_SurfaceRef surface = nullptr;
    ERR(suites.DrawbotSuiteCurrent()->GetSupplier(draw, &supplier));
    ERR(suites.DrawbotSuiteCurrent()->GetSurface(draw, &surface));
    if (err) return err;
    const auto sup = suites.SupplierSuiteCurrent();
    const auto surf = suites.SurfaceSuiteCurrent();
    const auto path_suite = suites.PathSuiteCurrent();
    const float ox = event->effect_win.current_frame.left;
    const float oy = event->effect_win.current_frame.top;
    DRAWBOT_PenRef shared_pen = nullptr;
    AEFX_SuiteScoper<PFAppSuite6> app(in_data,kPFAppSuite,kPFAppSuiteVersion6);
    std::map<int,ramp_ui::Color> theme_colors;
    for (const auto& c : commands) {
        auto color=c.color;
        if(color.theme_role) color=ramp_ui::scaled(theme_colors.at(color.theme_role),color.factor);
        DRAWBOT_ColorRGBA rgba{color.red,color.green,color.blue,color.alpha};
        DRAWBOT_RectF32 rect{c.x+ox,c.y+oy,c.w,c.h};
        DRAWBOT_PathRef path = nullptr;
        DRAWBOT_PenRef pen = nullptr;
        DRAWBOT_FontRef font = nullptr;
        DRAWBOT_BrushRef brush = nullptr;
        switch(c.kind) {
        case ramp_ui::DrawKind::theme_query: {
            PF_App_Color value{};
            ERR(app->PF_AppGetColor(static_cast<PF_App_ColorType>(c.x),&value));
            theme_colors[static_cast<int>(c.x)]={value.red*0x1.0001p-16f,value.green*0x1.0001p-16f,value.blue*0x1.0001p-16f,1.0f};
            break;
        }
        case ramp_ui::DrawKind::pen:
            ERR(sup->NewPen(supplier,&rgba,1.0f,&shared_pen)); break;
        case ramp_ui::DrawKind::release_pen:
            if(shared_pen) { ERR(sup->ReleaseObject(reinterpret_cast<DRAWBOT_ObjectRef>(shared_pen))); shared_pen=nullptr; }
            break;
        case ramp_ui::DrawKind::ticks:
            ERR(sup->NewPath(supplier,&path));
            ERR(path_suite->MoveTo(path,rect.left,rect.top));
            ERR(path_suite->LineTo(path,rect.left,rect.top+5.0f));
            ERR(path_suite->MoveTo(path,rect.left,rect.top+c.h));
            ERR(path_suite->LineTo(path,rect.left,rect.top+c.h-5.0f));
            ERR(surf->StrokePath(surface,shared_pen,path)); break;
        case ramp_ui::DrawKind::antialias:
            ERR(surf->SetAntiAliasPolicy(surface,static_cast<DRAWBOT_AntiAliasPolicy>(0))); break;
        case ramp_ui::DrawKind::fill:
            ERR(surf->PaintRect(surface,&rgba,&rect)); break;
        case ramp_ui::DrawKind::frame:
            ERR(sup->NewPath(supplier,&path));
            ERR(path_suite->MoveTo(path,rect.left+ox,rect.top+oy));
            ERR(path_suite->AddRect(path,&rect));
            ERR(sup->NewPen(supplier,&rgba,1.0f,&pen));
            ERR(surf->StrokePath(surface,pen,path)); break;
        case ramp_ui::DrawKind::line:
            ERR(sup->NewPath(supplier,&path));
            ERR(path_suite->MoveTo(path,rect.left,rect.top));
            ERR(path_suite->LineTo(path,rect.left+c.w,rect.top+c.h));
            ERR(sup->NewPen(supplier,&rgba,1.0f,&pen));
            ERR(surf->StrokePath(surface,pen,path)); break;
        case ramp_ui::DrawKind::text: {
            ERR(sup->NewDefaultFont(supplier,c.font,&font));
            ERR(sup->NewBrush(supplier,&rgba,&brush));
            const DRAWBOT_PointF32 origin{rect.left,rect.top};
            ERR(surf->DrawString(surface,brush,font,
                reinterpret_cast<const DRAWBOT_UTF16Char*>(c.text),&origin,
                static_cast<DRAWBOT_TextAlignment>(1),static_cast<DRAWBOT_TextTruncation>(1),c.w));
            break;
        }
        }
        // Release all resources even when a suite call fails.
        for (auto object : {reinterpret_cast<DRAWBOT_ObjectRef>(brush),reinterpret_cast<DRAWBOT_ObjectRef>(font),
                            reinterpret_cast<DRAWBOT_ObjectRef>(pen),reinterpret_cast<DRAWBOT_ObjectRef>(path)})
            if(object) { const auto release_err=sup->ReleaseObject(object); if(!err) err=release_err; }
        if(err) break;
    }
    if(shared_pen) { const auto release_err=sup->ReleaseObject(reinterpret_cast<DRAWBOT_ObjectRef>(shared_pen)); if(!err) err=release_err; }
    return err;
}

static PF_Err RampEvent(PF_InData *in_data, PF_ParamDef *params[], PF_EventExtra *event)
{
    if (!in_data || !params || !event || event->effect_win.area != PF_EA_CONTROL)
        return PF_Err_NONE;
    const A_long index=event->effect_win.index;
    if (index!=14 && index!=20 && index!=26 && index!=32 && index!=38) return PF_Err_NONE;
    PF_ParamDef *param=params[index];
    if (!param || param->param_type!=PF_Param_ARBITRARY_DATA || !param->u.arb_d.value) return PF_Err_NONE;
    if(event->e_type!=PF_Event_DRAW && event->e_type!=PF_Event_DO_CLICK &&
       event->e_type!=PF_Event_DRAG && event->e_type!=PF_Event_ADJUST_CURSOR) return PF_Err_NONE;
    std::lock_guard<std::recursive_mutex> guard(ramp_ui_mutex);
    auto& instance=ramp_ui_instances[in_data->effect_ref];
    auto& state=instance.ramps[index];
    OLMKiraKiraRampData ramp{};
    PF_Err err=ReadRampHandle(in_data,param->u.arb_d.value,&ramp);
    if(err) return err;
    AEFX_SuiteScoper<PFAppSuite6> app(in_data,kPFAppSuite,kPFAppSuiteVersion6);
    if(event->e_type==PF_Event_DRAW) {
        // Original 181155700 subtracts the frame origin on every event,
        // including DRAW, which retains the previous converted pointer.
        state.hover_x -= event->effect_win.current_frame.left;
        state.hover_y -= event->effect_win.current_frame.top;
        // Resolve theme colors at each original widget query, in draw order.
        ramp_ui::Theme theme{{0,0,0,1,7},{0,0,0,1,8},{0,0,0,1,2},{0,0,0,1,42}};
        return err ? err : DrawRampCommands(in_data,event,ramp_ui::draw(ramp,state,instance.clipboard.available,theme));
    }
    const auto& frame=event->effect_win.current_frame;
    const PF_Point point=event->e_type==PF_Event_ADJUST_CURSOR ? event->u.adjust_cursor.screen_point : event->u.do_click.screen_point;
    ramp_ui::EventType type=ramp_ui::EventType::hover;
    if(event->e_type==PF_Event_DO_CLICK) {
        type=event->u.do_click.num_clicks==1 ? ramp_ui::EventType::single : ramp_ui::EventType::multiple;
        event->u.do_click.send_drag=TRUE;
    } else if(event->e_type==PF_Event_DRAG)
        type=event->u.do_click.last_time ? ramp_ui::EventType::release : ramp_ui::EventType::drag;
    const auto result=ramp_ui::dispatch(ramp,state,instance.clipboard,ramp_ui_rng,
        {type,int(point.x-frame.left),int(point.y-frame.top)});
    if(result.picker>=0) {
        const auto c=ramp_ui::color(ramp.stops[result.picker]);
        PF_PixelFloat sample{c.alpha,c.red,c.green,c.blue}, picked=sample;
        const PF_Err picker_err=app->PF_AppColorPickerDialog("Color select",&sample,TRUE,&picked);
        ramp_ui::picker_result(ramp,state,result.picker,picker_err==PF_Interrupt_CANCEL,
                              {picked.red,picked.green,picked.blue,picked.alpha});
    }
    if(type!=ramp_ui::EventType::hover) {
        AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data,kPFHandleSuite,kPFHandleSuiteVersion1);
        void* locked=handles->host_lock_handle(param->u.arb_d.value);
        if(!locked) return PF_Err_BAD_CALLBACK_PARAM;
        std::memcpy(locked,&ramp,sizeof(ramp));
        handles->host_unlock_handle(param->u.arb_d.value);
        ERR(app->PF_InvalidateRect(event->contextH,&frame));
    }
    param->uu.change_flags |= PF_ChangeFlag_CHANGED_VALUE;
    event->evt_out_flags |= PF_EO_HANDLED_EVENT | PF_EO_UPDATE_NOW;
    return err;
}
