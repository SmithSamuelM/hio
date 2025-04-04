# -*- encoding: utf-8 -*-
"""tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio import Mixin, HierError
from hio.base.hier import ActBase, actify, Act, Tract, Need, Box, Bag

from hio.help import Mine

def test_act_basic():
    """Test Act class"""
    # clear registries for debugging
    Act._clear()


    act = Act()
    assert "Act" in Act.Registry
    assert Act.Registry["Act"] == Act

    assert act.name == "Act0"
    assert act.Index == 1
    assert act.Names[act.name] == act
    assert act.stuff == None

    assert not act()

    """Done Test"""


def test_tract_basic():
    """Test Tract class"""
    # clear registries for debugging
    Tract._clear()


    tract = Tract()
    assert "Tract" in Tract.Registry
    assert Tract.Registry["Tract"] == Tract

    assert tract.name == "Tract0"
    assert tract.Index == 1
    assert tract.Names[tract.name] == tract
    assert tract.dest == None
    assert isinstance(tract.need, Need)
    assert tract.need()

    with pytest.raises(HierError):
        assert not tract()  # since default .dest not yet resolved

    mine = Mine()
    mine.cycle = Bag(value=3)
    box = Box(mine=Mine)
    need = Need(expr='M.cycle.value >= 3', mine=mine)
    tract = Tract(dest=box, need=need)
    assert not tract.need.compiled

    dest = tract()
    assert dest == box
    assert tract.need.compiled

    mine.cycle.value = 1
    assert not tract()


    """Done Test"""

if __name__ == "__main__":
    test_act_basic()
    test_tract_basic()
