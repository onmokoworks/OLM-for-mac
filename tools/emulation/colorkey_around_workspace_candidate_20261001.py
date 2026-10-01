"""Source experiment for native reuse of the Thin/Blur distance workspace."""
import probe_olmcolorkey_around_range_20261001 as around
import probe_olmcolorkey_blur_float_materialization_20261001 as amount

def candidate_source(original):
    body=amount.normalized_source(around.candidate_source(original))
    old='static std::vector<float> ChessboardDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)'
    new=old[:-1]+', const std::vector<float> *initial = nullptr)'
    assert body.count(old)==1;body=body.replace(old,new)
    old='std::vector<float> d((size_t)h, 0.0f);'
    new='std::vector<float> d = initial && initial->size() == (size_t)h\n            ? *initial : std::vector<float>((size_t)h, 0.0f);'
    assert body.count(old)==1;body=body.replace(old,new)
    old='float left = mask[(size_t)y] ? 0.0f : std::min(read(y - 1), read(y)) + 1.0f;'
    new='float left = mask[(size_t)y] ? 0.0f : std::min(4000.0f, std::min(read(y - 1), read(y)) + 1.0f);'
    assert body.count(old)==1;body=body.replace(old,new)
    old='std::min(left + 1.0f, std::min(read(y - 1), read(y - 2)) + 1.0f);'
    new='std::min(4000.0f, std::min(left + 1.0f, std::min(read(y - 1), read(y - 2)) + 1.0f));'
    assert body.count(old)==1;body=body.replace(old,new)
    old='\tstd::vector<u_char> thin_expanded(pixel_count, 0);'
    assert body.count(old)==1;body=body.replace(old,old+'\n\tstd::vector<float> thin_distance_workspace;')
    old='''\t\t\tmatched[i] = (matched[i] && dist[i] * scale >= amount) ? 1 : 0;
\t\t}
\t} else if'''
    new=old.replace('\n\t} else if','\n        if (w == 1 && IsRecoveredAroundBlur(info) && info.edge_blur_distance_type == 1)\n            thin_distance_workspace = std::move(dist);\n\t} else if')
    assert body.count(old)==1;body=body.replace(old,new)
    old='''\t\tstd::vector<float> dist = MatteDistanceTo(matched, w, h, info.edge_thin_distance_type);'''
    new=old+'''
        if (w == 1 && IsRecoveredAroundBlur(info) && info.edge_blur_distance_type == 1)
            thin_distance_workspace = MatteDistanceTo(Boundary8(matched, w, h), w, h,
                info.edge_thin_distance_type);'''
    assert body.count(old)==1;body=body.replace(old,new)
    old='''\t\t        : EdgeBlurDistanceTo(boundary, w, h, info.edge_blur_distance_type);'''
    new='''            : (w == 1 && IsRecoveredAroundBlur(info) && info.edge_blur_distance_type == 1 &&
               !thin_distance_workspace.empty())
                ? ChessboardDistanceTo(boundary, w, h, &thin_distance_workspace)
                : EdgeBlurDistanceTo(boundary, w, h, info.edge_blur_distance_type);'''
    assert body.count(old)==1;return body.replace(old,new)
