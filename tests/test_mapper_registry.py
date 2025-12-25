"""
Test Mapper Registry functionality.
"""

from nwtrack.mapper_registry import MapperRegistry


def test_mapper_registry_get_mapper_for():
    registry = MapperRegistry()

    class DummyEntityA:
        pass

    class DummyEntityB:
        pass

    class DummyMapperA:
        pass

    class DummyMapperB:
        pass

    dummy_mapper_a = DummyMapperA()
    dummy_mapper_b = DummyMapperB()
    registry.register(DummyEntityA, dummy_mapper_a)
    registry.register(DummyEntityB, dummy_mapper_b)

    retrieved_mapper_a = registry.get_mapper_for(DummyEntityA)
    retrieved_mapper_b = registry.get_mapper_for(DummyEntityB)
    assert retrieved_mapper_a is dummy_mapper_a
    assert retrieved_mapper_b is dummy_mapper_b
    assert retrieved_mapper_a is not retrieved_mapper_b
