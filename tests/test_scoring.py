from pathlib import Path
from tdc.models import Candidate
from tdc.scoring import select

def make(**kw):
    d=dict(id="x",title="test",category="funny",source_url="https://example.com",creator="c",views=1000,likes=100,comments=10,shares=5,local_path=Path(__file__),authorized=True,license="permission",authorization_reference="ref")
    d.update(kw); return Candidate(**d)

def test_authorization_required():
    assert len(select([make(),make(id="no",authorized=False)])) == 1

def test_categories_filtered():
    assert select([make(category="politics")]) == []
