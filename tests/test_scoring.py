from pathlib import Path
from tdc.models import Candidate
from tdc.scoring import select, score

def item(id, **kw):
    data=dict(id=id,title="t",category="funny",source_url="https://example.com/v",creator="c",views=1000,likes=100,comments=10,shares=5,local_path=Path(__file__),authorized=True,license="permission",authorization_reference="ref")
    data.update(kw); return Candidate(**data)

def test_select_requires_authorization_and_local_file():
    good=item("good")
    bad=item("bad", authorized=False)
    assert [x.id for x in select([good,bad])] == ["good"]

def test_category_filter():
    assert select([item("x", category="politics")]) == []

def test_score_positive():
    assert score(item("x")) > 0
