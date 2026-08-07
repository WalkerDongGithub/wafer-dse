"""流量选择器——S_n 共轭类、暴力枚举。"""
from lp.ctx import Ctx
from lp.models.perf.traffic_based.traffic import SConjugacyReps, AllDerangements, PermutationRep

ctx = Ctx()


def test_conjugacy_reps():
    """S_4 derangement 共轭类 = 2 个（4-cycle + 双对换）。"""
    reps = SConjugacyReps(derangements_only=True).select(4)
    assert len(reps) == 2, f"expected 2, got {len(reps)}"
    labels = {r.label for r in reps}
    assert "λ=4" in labels
    assert "λ=2,2" in labels


def test_permutation_flow_matrix():
    """排列 (1,2,3,0) → D[0][1]=1, D[1][2]=1, D[2][3]=1, D[3][0]=1。"""
    p = PermutationRep("test", (1, 2, 3, 0))
    D = p.as_flow_matrix()
    assert D[0][1] == 1.0
    assert D[1][2] == 1.0
    assert D[0][0] == 0.0  # 不发自收


def test_all_derangements_n4():
    """S_4 的 derangement 共 9 个。"""
    reps = AllDerangements().select(4)
    assert len(reps) == 9


def test_all_derangements_guard():
    """n > 8 应该报错。"""
    try:
        AllDerangements().select(9)
        assert False, "should have raised"
    except ValueError:
        pass


print(f"test_traffic: 4/4 PASSED")
