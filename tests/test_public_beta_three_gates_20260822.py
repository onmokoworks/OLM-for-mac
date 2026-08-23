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
    assert "| ColorKeep | 通過 | 限定 | 限定 |" in text
    assert "Windows実AEXのcount 5/100末尾色境界は3深度hostless exact" in text
    assert "Repeat 10＋Legacy onをSmart HD/4K×8/16/32 native AEで6/6通過" in text
    assert "入力一致key＋Edge Blur Amount 4をSmart HD/4K×8/16/32 native AEで6/6通過" in text
    assert "| OLMSmoother | 通過 | 限定 | 限定 |" in text
    assert "PF16 Windows実用代表は現行Classic/Smart exact" in text
    assert "| OLMToonDilate | 通過 | 限定 | 限定 |" in text
    assert "3深度Windows corner-seed代表は現行core exact" in text
    assert "宣言済みnative AE matrixは2026-08-23時点で54/54成功" in text
    assert "個別テストが増えても行・列・完了基準を増やさない" in text
    support = (ROOT / "docs/BETA_SUPPORT.md").read_text()
    assert "Public Betaの判断基準は" in support
    assert "追加ゲートではありません" in support
    assert "74dd05284203287a61205a9f937e25c62731d4a07bbe6fbcecb3d951f523f80d" in support


if __name__ == "__main__":
    test_three_gate_matrix_is_fixed_and_covers_all_plugins()
    print("PUBLIC_BETA_3_GATES pass=1 plugins=10 gates=3")
