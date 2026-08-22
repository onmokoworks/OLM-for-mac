from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_three_gate_matrix_is_fixed_and_covers_all_plugins() -> None:
    text = (ROOT / "docs/PUBLIC_BETA_3_GATES.md").read_text()
    assert "個別fixture、SHA、" in text
    assert "新しい完了基準ではない" in text
    assert text.count("| プラグイン | 安全性 | 主要操作 | 互換性・実機 | RCまでの残件 |") == 1
    plugins = (
        "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
        "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
        "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
    )
    for plugin in plugins:
        assert text.count(f"| {plugin} |") == 1
    assert text.count("| 通過 |") == len(plugins)


if __name__ == "__main__":
    test_three_gate_matrix_is_fixed_and_covers_all_plugins()
    print("PUBLIC_BETA_3_GATES pass=1 plugins=10 gates=3")
