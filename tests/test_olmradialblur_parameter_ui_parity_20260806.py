from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text()
STRINGS = (ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp").read_text()


def test_windows_group_controls_are_real_ae_topics() -> None:
    assert SOURCE.count("PF_ADD_TOPIC(") == 4
    assert SOURCE.count("PF_END_TOPIC(") == 4
    assert "PF_ADD_NULL(" not in SOURCE


def test_windows_control_types_and_ui_ranges_are_preserved() -> None:
    assert "PF_ADD_POINT(GetStringPtr(StrID_Center_Param_Name), 50, 50" in SOURCE
    assert SOURCE.count("PF_ADD_ANGLE(") == 2
    assert "PF_ADD_SLIDER(GetStringPtr(StrID_OuterEdgeFade_Param_Name)" in SOURCE
    assert "PF_ADD_SLIDER(GetStringPtr(StrID_InnerEdgeFade_Param_Name)" in SOURCE
    assert "0.0, 10.0, 0.0, 2.0, 1.0" in SOURCE
    assert "PF_Precision_HUNDREDTHS, 0, 0,\n\t                     THICKNESS_DISK_ID" in SOURCE


def test_windows_visible_names_and_popup_labels_are_preserved() -> None:
    assert 'StrID_InnerStrength_Param_Name, "Strength"' in STRINGS
    assert '"Zoom | Rotation"' in STRINGS
    assert '"Add | Max | Override"' in STRINGS
    assert '"Smooth | Block | Layer"' in STRINGS
